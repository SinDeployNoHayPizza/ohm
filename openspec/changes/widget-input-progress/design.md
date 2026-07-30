# Design: Widget Input & Progress

## Technical Approach

Two independent widget refactors. No backend/agent logic changes beyond one attribute addition.

1. **CommandInput auto-resize** — Replace `Input` with `TextArea`, compute dynamic height from content line count, clamp to `min(line_count, max_lines)` where `max_lines = min(10, int(0.4 * viewport_height))`. Shrink on content removal. TextArea's built-in scroll handles overflow.
2. **ContextProgress real data** — Strip `FAKE_TOKEN_USAGE`. Accept `tokens_used` / `context_window` as reactives. Caller wires real metrics after each agent interaction.

## Architecture Decisions

### Decision: TextArea over Input

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `Input` + hack height | Multi-line unsupported natively; virtual_size missing | ✗ |
| `TextArea` | Native multi-line, built-in scroll, reliable `virtual_size`; same keybinding surface | **✓** |
| Custom render widget | More code, less tested, no free keybinding | ✗ |

### Decision: Reactive attributes for ContextProgress

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Accept `AgentResponse` directly | Couples widget to agent data model, fails if struct changes | ✗ |
| Reactive `tokens_used` + `context_window` | Self-contained, auto-render on write, defaults show idle 0% | **✓** |

### Decision: `last_metrics` on Agent

**Choice**: Add `last_metrics: dict` to `Agent`, populated after `run()` and after `stream()` iteration completes.

**Rationale**: The streaming path in `app.py` iterates `agent.stream()` events but never captures the final result's metrics. Adding one dict attribute (populated from `_extract_metrics(result)` after both execution paths) is the minimal change — no new backend logic, no contract breakage. The stream path captures the strands agent's final result in a `finally` block.

## Data Flow

### Progress bar — after agent interaction

```
agent.stream() completes
  → Agent._stream_done() populates self.last_metrics from strands result
       ↓
OhmApp._stream_agent_response()
  reads agent.last_metrics
  resolves context_window from current ProviderModel
  calls ContextProgress.update(tokens_used=N, context_window=N)
       ↓
ContextProgress.render() computes bar ← self.tokens_used / self.context_window
```

### Input — dynamic height

```
User types/deletes → TextArea.Changed
  → CommandInput._on_textarea_changed()
    → line_count = len(text.splitlines())
    → target = clamp(line_count, min=1, max=_max_lines)
    → self.styles.height = target  (no-op if unchanged)

Window resized → App.on_resize → CommandInput._on_resize()
  → recalc _max_lines from new viewport
  → re-clamp current content
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/ohm/cli/widgets/input.py` | Modify | Replace `Input` with `TextArea`, remove `height: 5` from CSS, add `_on_textarea_changed` + `_on_resize` + `_max_lines` |
| `src/ohm/cli/widgets/progress.py` | Modify | Remove `FAKE_TOKEN_USAGE` import, add `tokens_used`/`context_window` reactives + `update()` method, compute bar from live reactives in `render()` |
| `src/ohm/core/agent.py` | Modify (minimal) | Add `last_metrics: dict = field(default_factory=dict)` to `AgentState`; populate in `run()` after `_extract_metrics()`, in `stream()` after iteration via `finally` |
| `src/ohm/cli/app.py` | Modify | In `_stream_agent_response()`, after streaming loop, read `agent.last_metrics` + resolve model context_window → call `progress.update(...)` |

## Interfaces / Contracts

```python
# progress.py — public API
class ContextProgress(Widget):
    tokens_used: reactive[int] = reactive(0)
    context_window: reactive[int] = reactive(200_000)

    def update(self, tokens_used: int, context_window: int) -> None:
        self.tokens_used = tokens_used
        self.context_window = context_window  # triggers reactive recompute

# agent.py — new field
@dataclass
class AgentState:
    ...
    last_metrics: dict = field(default_factory=dict)
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `ContextProgress.update()` → `render()` output matches ratio | Instantiate widget, call update, assert bar fraction + label |
| Unit | `CommandInput._max_lines` formula | Unit test with mocked `self.app.size` |
| Manual | Multi-line type/paste, deletion, shrinking, scroll overflow | Run TUI, interactively verify |
| Regression | `/` command filter, `#` file include still work | Run TUI, test both hotkey paths |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

No migration required. Widgets are in-memory only. Progress bar defaults to idle 0% until first agent interaction; input starts at 1 line.

## Open Questions

- [ ] How to access strands' final result object after `stream_async()` iteration? Resolve during apply by inspecting `strands.Agent` internals (look for `_last_result`, `result`, or final chunk metadata).
- [ ] TextArea border padding math: tall border = 2 rows — verify widget height calc accounts for this so 1 line of text doesn't show empty space. Visual tune during apply.
