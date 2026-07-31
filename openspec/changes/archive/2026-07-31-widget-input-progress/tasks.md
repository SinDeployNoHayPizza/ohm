# Tasks: Widget Input & Progress

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 150–200 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-always |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Agent.last_metrics + ContextProgress real data | Single PR | `uv run pytest tests/ -k "agent or progress"` | Launch TUI, send message, verify % bar updates | Revert agent.py + progress.py + app.py changes |
| 2 | CommandInput auto-resize | Same PR | `uv run pytest tests/ -k "input"` | Launch TUI, type/paste multi-line, verify resize | Revert input.py + app.py Input→TextArea changes |
| 3 | Verification | Same PR | `uv run pytest` | Manual: scroll, /commands, #files | n/a — tests only |

## Phase 1: Agent.last_metrics property (Foundation)

- [x] 1.1 **RED** Write `test_agent_last_metrics_populated` in `tests/test_agent.py` — verify `Agent.last_metrics` is populated after `stream()` iteration and after `run()` returns (mock strands `Agent` to avoid real LLM calls)
- [x] 1.2 Add `last_metrics: dict = field(default_factory=dict)` to `AgentState` in `src/ohm/core/agent.py`; in `run()` populate `self.state.last_metrics = self._extract_metrics(result)` after successful execution; in `stream()` access the strands `Agent.last_usage` / `Agent.last_result` to call `_extract_metrics()` and store to `self.state.last_metrics` in the `finally` block (**open question**: inspect strands internals for final result — try `agent._last_result`, `agent._usage`, or final-stream event metadata; fallback: `_extract_metrics(None)` returns `{}`)
- [x] 1.3 Add `last_metrics` property on `Agent` that returns `self.state.last_metrics`

## Phase 2: ContextProgress real data

- [x] 2.1 **RED** Write `test_context_progress_update` in `tests/cli/test_progress.py` — instantiate `ContextProgress`, call `update(tokens_used=50000, context_window=200000)`, assert `render()` output reflects 25% bar fraction and label
- [x] 2.2 In `src/ohm/cli/widgets/progress.py`: remove `FAKE_TOKEN_USAGE` import and `__init__` override; add `tokens_used: reactive[int] = reactive(0)` and `context_window: reactive[int] = reactive(200_000)`; add `update(tokens_used, context_window)` setter; replace `render()` to compute `percentage` from `self.tokens_used / self.context_window * 100` and show live counts in label
- [x] 2.3 In `src/ohm/cli/app.py` `_stream_agent_response()`: after the `async for event in self.agent.stream(prompt)` loop completes, read `self.agent.last_metrics`; resolve `context_window` from `ProviderModel` matching `self.current_provider` / `self.current_model` (look up via `provider.get_models()`); call `self.query_one(ContextProgress).update(tokens_used=metrics["total_tokens"], context_window=N)`

## Phase 3: CommandInput auto-resize

- [x] 3.1 **RED** Write `test_command_input_max_lines` in `tests/cli/test_input.py` — verify `_max_lines` formula gives `min(10, int(0.4 * viewport_height))` and never below 1 (parameterized height for testability)
- [x] 3.2 In `src/ohm/cli/widgets/input.py`: replace `Input` with `TextArea`, remove `height: 5` from CSS, add `_compute_max_lines()`, `on_mount`, `on_resize`, `_on_textarea_changed` for dynamic height
- [x] 3.3 In `src/ohm/cli/app.py`: replace `@on(Input.Changed, "#command-input")` with `@on(TextArea.Changed, "#command-input")`; replace `@on(Input.Submitted, "#command-input")` with Ctrl+Enter binding + `action_submit_input`; fix `Input` focus refs in `model_selector.py` and `modal_menu.py`

## Phase 4: Verification

- [x] 4.1 Run `uv run pytest` — 57 passed, 1 pre-existing failure (unrelated config test)
- [ ] 4.2 Run `uv run ohm` — manual TUI check: (a) paste multi-line text, verify widget grows/shrinks; (b) type `/` verify command dropdown appears; (c) type `#` verify file includer works; (d) send message, verify progress bar updates with real metrics
