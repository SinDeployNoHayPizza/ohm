# Tasks: Session Management Cycle

## Review Workload Forecast

`Decision needed before apply: No` | `Chained PRs recommended: No` | `400-line budget risk: Medium`

Estimated ~480 changed lines across 7 files. Single coherent feature — chaining adds overhead without clear slice boundaries. Apply as one PR.

---

## Task 1 — Session persistence tests (Strict TDD)

- [ ] Create `tests/test_session.py` covering:
  - `_gen_session_id()` produces valid `ses_YYYYMMDD_HHMMSS_XXXX` format
  - Save → `last_session.json` pointer resolves to `{session_id}.json`
  - Load restores messages with correct role/content/timestamp
  - No `last_session.json` → `load_last_session()` returns `{}`
  - Corrupt `last_session.json` → graceful fallback
  - Corrupt session file → graceful fallback
  - Quit via ctrl+Q → confirm → both files written correctly
  - Multiple saves keep both session files, pointer points to latest
  - Content is plain text in JSON (no Rich objects)
- [ ] Extend `tests/test_cli.py` with `--continue` / `-c` flag parsing tests
- [ ] Extend `tests/test_cli.py` with exit banner content check
- [ ] Extend `tests/test_cli.py` with `ohm session continue` routing test
- **Run**: `uv run pytest tests/test_session.py tests/test_cli.py -v`
- **Rollback**: `git checkout -- tests/test_session.py tests/test_cli.py`

## Task 2 — Session save/load in app.py

- [ ] Add `_gen_session_id()` helper returning `ses_{ISO8601-no-punct}_{4hex}`
- [ ] Add `_load_last_session()` reading pointer → resolving file → returning data
- [ ] Modify `OhmApp.__init__` to accept `continue_session: dict | None = None`
- [ ] Capture user messages at submit boundary in `_handle_input_submit`
- [ ] Capture agent responses at end of `_stream_agent_response`
- [ ] Rewrite `on_unmount` save: write `{session_id}.json` + update `last_session.json` pointer
- [ ] Rewrite `action_quit_ohm` to use new save flow
- [ ] Add `on_mount()` replay: iterate continue_session messages → `chat.add_message()` for each
- [ ] Register F3 binding with `action_open_session_browser`
- - **Run**: `uv run pytest tests/test_session.py -v`
- **Rollback**: `git checkout -- src/ohm/cli/app.py`

## Task 3 — CLI continue flag + exit banner

- [ ] Add `register_global("--continue", "-c", dest="continue_")` in `registry.py`
- [ ] Add `continue_mode` param to `_launch_tui()`: resolve session before constructing app
- [ ] Print exit banner (plain ASCII OHM_LOGO + resume instructions) after `app.run()`
- [ ] Wire `ns.continue_` from `main.py` into registry dispatch → `_launch_tui()`
- - **Run**: `uv run pytest tests/test_cli.py -v`
- **Rollback**: `git checkout -- src/ohm/cli/registry.py src/ohm/cli/main.py`

## Task 4 — Session browser modal

- [ ] Create `src/ohm/cli/screens/session_browser.py`: `SessionBrowser(ModalScreen[dict | None])`
- [ ] List session files (exclude `last_session.json`) with columns: ID, started, messages, theme
- [ ] ↑↓ navigate, Enter select (dismiss with session dict), Esc dismiss (None)
- [ ] Empty state: notify "No saved sessions found"
- [ ] Corrupt entry: skip with notification, continue listing
- [ ] Wire F3 action in app.py: `self.push_screen(SessionBrowser(), on_session_selected)`
- **Run**: `uv run pytest tests/test_session.py -v`
- **Rollback**: `git checkout -- src/ohm/cli/screens/session_browser.py src/ohm/cli/app.py`

## Task 5 — `ohm session continue` sub-action

- [ ] Add `continue` sub-parser in `session.py` `register_args()`
- [ ] Handler: load last session → launch `OhmApp(continue_session=data)`
- [ ] No session → exit code 1 with message
- - **Run**: `uv run pytest tests/test_cli.py -v`
- **Rollback**: `git checkout -- src/ohm/commands/session.py`
