# Proposal: widget-input-progress

## Intent

Two independent widget improvements that make the TUI feel production-quality. The input box is fixed-height and clips multi-line content; the context progress bar renders fake data instead of real usage metrics. Fixing both removes known demo-jank without touching backend or agent logic.

## Scope

### In Scope
1. **CommandInput auto-resize** — height adapts to content lines, bounded by `min(10, 40% * viewport_height)`, shrinks when lines are removed, scrolls when exceeding max.
2. **ContextProgress real data** — wire `AgentResponse.tokens_used` + `Agent._extract_metrics()` into the progress bar; derive context-window ceiling from `ProviderModel.context_window` instead of `FAKE_TOKEN_USAGE`.

### Out of Scope
- Backend/agent logic changes (no new fields, no new metrics extraction)
- Other widget visual polish (banner, sidebar, status bar)
- Persistence of token usage across sessions
- Unit/e2e tests for these widgets (would require Textual test harness)

## Capabilities

### New Capabilities

None. Both changes are internal refactors of existing widgets with no spec-level behavior changes.

### Modified Capabilities

None. No existing specs in `openspec/specs/` to modify.

## Approach

### CommandInput auto-resize

- Replace fixed `height: 5` in CSS with computed height from `on_mount` + `on_input_changed`
- Switch from `Input` to `TextArea` (Textual's multi-line widget) to support line wrapping and virtual_size detection
- On every content change, query `self.query_one(TextArea).virtual_size.height` → clamp to `min(line_count, max_lines)` where `max_lines = min(10, int(0.4 * self.app.size.height))`
- Set widget height via `self.styles.height` = computed value
- Re-evaluate `max_lines` on screen resize (`on_resize`)

### ContextProgress real data

- Accept `tokens_used: int` and `context_window: int` via reactive attributes or a public `update(agent_response: AgentResponse)` method
- The caller (main screen or app) passes `AgentResponse` from the last agent interaction, or `None` to show an idle/empty state
- Replace all `FAKE_TOKEN_USAGE` references with live `self.tokens_used / self.context_window`
- Default to 0% / idle when no data has been received yet
- The `Agent._extract_metrics()` already returns `input_tokens`, `output_tokens`, `total_tokens` — no backend changes needed

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/ohm/cli/widgets/input.py` | Modified | Replace `Input` with `TextArea`, add dynamic height logic |
| `src/ohm/cli/widgets/progress.py` | Modified | Remove `FAKE_TOKEN_USAGE`, accept real token data via reactive attrs |
| `src/ohm/cli/screens/main.py` | Modified | Wire `AgentResponse` into `ContextProgress.update()` (minimal change) |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| TextArea vs Input behavioral differences (keybindings, paste, etc.) | Medium | Test interactive input in TUI; verify `/` filter and `#` file-include still work |
| ContextProgress shows 0% before first interaction | Low | Design intentional — idle state is correct; no mock data to fake it |
| `on_resize` recalc in input may cause layout jitter | Low | Debounce height updates; only change when max_lines actually changes |

## Rollback Plan

Revert the two files (`input.py`, `progress.py`) plus the caller wiring in `main.py`. Both changes are self-contained, no data migration needed. If one widget breaks, the other can be rolled back independently.

## Dependencies

- `textual.widgets.TextArea` — already available in Textual (no new dependency)
- Existing `AgentResponse` and `ProviderModel` from `src/ohm/core/` — no changes needed

## Success Criteria

- [ ] Input box starts compact (single line), grows as user types multiple lines, shrinks when lines are deleted, never exceeds `min(10, 40% * viewport_height)`
- [ ] Context progress bar shows accurate percentage from real agent metrics after an interaction, and shows idle state before any interaction
- [ ] No regressions in `/` command filtering, `#` file inclusion, or keyboard input
