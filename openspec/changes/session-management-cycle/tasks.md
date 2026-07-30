# Tasks: Session Management Cycle

## Review Workload Forecast

`Decision needed before apply: No` | `Chained PRs recommended: No` | `400-line budget risk: Medium`

Estimated ~480 changed lines across 7 files. Single coherent feature — chaining adds overhead without clear slice boundaries. Apply as one PR.

---

## Task 1 — Session persistence tests (Strict TDD)

- [x] Create `tests/test_session.py` covering:
  - `_gen_session_id()` produces valid `ses_YYYYMMDD_HHMMSS_XXXX` format
  - Save → `last_session.json` pointer resolves to `{session_id}.json`
  - Load restores messages with correct role/content/timestamp
  - No `last_session.json` → `load_last_session()` returns `{}`
  - Corrupt `last_session.json` → graceful fallback
  - Corrupt session file → graceful fallback
  - Quit via ctrl+Q → confirm → both files written correctly
  - Multiple saves keep both session files, pointer points to latest
  - Content is plain text in JSON (no Rich objects)
- [x] Extend `tests/test_cli.py` with `--continue` / `-c` flag parsing tests
- [x] Extend `tests/test_cli.py` with exit banner content check
- [x] Extend `tests/test_cli.py` with `ohm session continue` routing test
- **Run**: `uv run pytest tests/test_session.py tests/test_cli.py -v` ✅ 15+19=34 passed
- **Rollback**: `git checkout -- tests/test_session.py tests/test_cli.py`

## Task 2 — Session save/load in app.py

- [x] Add `_gen_session_id()` helper returning `ses_{ISO8601-no-punct}_{4hex}`
- [x] Add `_load_last_session()` reading pointer → resolving file → returning data
- [x] Modify `OhmApp.__init__` to accept `continue_session: dict | None = None`
- [x] Capture user messages at submit boundary in `_handle_input_submit`
- [x] Capture agent responses at end of `_stream_agent_response`
- [x] Rewrite `on_unmount` save: write `{session_id}.json` + update `last_session.json` pointer
- [x] Rewrite `action_quit_ohm` to use new save flow
- [x] Add `on_mount()` replay: iterate continue_session messages → `chat.add_message()` for each
- [x] Register F3 binding with `action_open_session_browser`
- **Run**: `uv run pytest tests/test_session.py -v` ✅ 15 passed
- **Rollback**: `git checkout -- src/ohm/cli/app.py`

## Task 3 — CLI continue flag + exit banner

- [x] Add `register_global("--continue", "-c", dest="continue_")` in `main.py`
- [x] Add `continue_mode` param to `_launch_tui()`: resolve session before constructing app
- [x] Print exit banner (plain ASCII OHM_LOGO + resume instructions) after `app.run()`
- [x] Wire `ns.continue_` from `main.py` into registry dispatch → `_launch_tui()`
- **Run**: `uv run pytest tests/test_cli.py -v` ✅ 19 passed
- **Rollback**: `git checkout -- src/ohm/cli/registry.py src/ohm/cli/main.py`

## Task 4 — Session browser modal

- [x] Create `src/ohm/cli/screens/session_browser.py`: `SessionBrowser(ModalScreen[dict | None])`
- [x] List session files (exclude `last_session.json`) with columns: ID, started, messages, theme
- [x] ↑↓ navigate, Enter select (dismiss with session dict), Esc dismiss (None)
- [x] Empty state: notify "No saved sessions found"
- [x] Corrupt entry: skip with notification, continue listing
- [x] Wire F3 action in app.py: `self.push_screen(SessionBrowser(), on_session_selected)`
- **Run**: `uv run pytest tests/test_session.py -v` ✅ 15 passed
- **Rollback**: `git checkout -- src/ohm/cli/screens/session_browser.py src/ohm/cli/app.py`

## Task 5 — `ohm session continue` sub-action

- [x] Add `continue` sub-parser in `session.py` `register_args()`
- [x] Handler: load last session → launch `OhmApp(continue_session=data)`
- [x] No session → exit code 1 with message
- **Run**: `uv run pytest tests/test_cli.py -v` ✅ 19 passed
- **Rollback**: `git checkout -- src/ohm/commands/session.py`
