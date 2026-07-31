# Apply Progress: widget-input-progress

## Mode
Strict TDD — RED → GREEN → TRIANGULATE → REFACTOR per phase

## Completed Tasks

### Phase 1: Agent.last_metrics property (Foundation)
- [x] 1.1 RED — Write tests for `Agent.last_metrics` (tests/test_agent.py)
- [x] 1.2 Add `last_metrics` field to AgentState + populate in `run()` and `stream()` finally block
- [x] 1.3 Add `last_metrics` property on Agent

### Phase 2: ContextProgress real data
- [x] 2.1 RED — Write tests for ContextProgress.update() and render() (tests/cli/test_progress.py)
- [x] 2.2 Strip FAKE_TOKEN_USAGE, add reactive tokens_used/context_window, update render() with live ratio
- [x] 2.3 Wire real metrics in app.py _stream_agent_response() after stream completes

### Phase 3: CommandInput auto-resize
- [x] 3.1 RED — Write tests for _compute_max_lines formula (tests/cli/test_input.py)
- [x] 3.2 Replace Input with TextArea, add dynamic height, on_mount, on_resize, _on_textarea_changed
- [x] 3.3 Update app.py TextArea handlers, add Ctrl+Enter submit binding, fix Input focus refs in widget files

### Phase 4: Verification
- [x] 4.1 Run full test suite — 57 passed, 1 pre-existing failure (test_config test_project_overrides_global — unrelated)
- [ ] 4.2 Manual TUI verification (optional — can be done by user)

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1-1.3 | `tests/test_agent.py` | Unit | ✅ 14/14 | ✅ Written | ✅ Passed | ✅ 2 cases (different data, no result) | ✅ Clean |
| 2.1-2.2 | `tests/cli/test_progress.py` | Unit | N/A (new) | ✅ Written | ✅ Passed | ✅ 4 cases (idle, update, zero-window, near-full) | ✅ Clean |
| 3.1-3.2 | `tests/cli/test_input.py` | Unit | N/A (new) | ✅ Written | ✅ Passed | ✅ 4 cases (formula, tall, short, medium) | ✅ Parameterized for testability |

### Test Summary
- **Total tests written**: 13 (5 agent + 4 progress + 4 input)
- **Total tests passing**: 57 (all project tests, pre-existing failure is unrelated)
- **Layers used**: Unit (13)
- **Approval tests**: None — no refactoring tasks
- **Pure functions created**: `ContextProgress.update()`, `CommandInput._compute_max_lines()`

## Files Changed

| File | Action | What Was Done |
|------|--------|---------------|
| `src/ohm/core/agent.py` | Modified | Added `last_metrics` to `AgentState`, populated in `run()` and `stream()`, exposed as `@property` |
| `src/ohm/cli/widgets/progress.py` | Modified | Stripped `FAKE_TOKEN_USAGE`, added `tokens_used`/`context_window` reactives, `update()` method, real % computation in `render()` |
| `src/ohm/cli/widgets/input.py` | Modified | Replaced `Input` with `TextArea`, dynamic height via `_compute_max_lines()`, `on_mount`/`on_resize`/`_on_textarea_changed` |
| `src/ohm/cli/app.py` | Modified | `TextArea` import, `TextArea.Changed` handler, Ctrl+Enter submit action, `_resolve_context_window` helper, ContextProgress wiring after stream |
| `src/ohm/cli/widgets/model_selector.py` | Modified | Updated `Input` focus references to `#command-input` |
| `src/ohm/cli/widgets/modal_menu.py` | Modified | Updated `Input` focus references to `#command-input` |
| `tests/test_agent.py` | Modified | Added 5 tests for `Agent.last_metrics` |
| `tests/cli/test_progress.py` | Created | 4 tests for `ContextProgress.update()` and `render()` |
| `tests/cli/test_input.py` | Created | 4 tests for `CommandInput._compute_max_lines()` |
| `openspec/changes/widget-input-progress/tasks.md` | Modified | Marked Phase 1-4 tasks complete |

## Deviations from Design

1. **`_compute_max_lines` parameterization**: Made `viewport_height` an optional parameter to enable unit testing without Textual app context. The method still defaults to `self.app.size.height` when called from widget lifecycle.
2. **ContextProgress reactive percentage removed**: The old `percentage: reactive[float]` field was removed per design. Percentage is now computed in `render()` from `tokens_used / context_window`.
3. **Submit via Ctrl+Enter binding**: Instead of `TextArea.Submitted` (which doesn't exist), added a `Binding("ctrl+enter", "submit_input", ...)` at the app level.

## Issues Found
- **Pre-existing test failure**: `test_config.py::TestLoadConfig::test_project_overrides_global` fails because the test expects `gemini-2.5-flash` but the defaults now resolve to `gemini-3.1-flash-lite`. Pre-existing, unrelated to this change.
- **Textual `app` property**: Cannot mock via `_app` — uses ContextVar internally. Parameterized `_compute_max_lines` to accept explicit height.

## Remaining Tasks
- [ ] 4.2 Manual TUI verification — user to run `uv run ohm` and test interactively

## Status
14/15 tasks complete. Ready for manual verification (4.2).
