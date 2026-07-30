# Design: Session Management Cycle

**Change**: `session-management-cycle`

## Session ID Format

`ses_{ISO8601-no-punct}_{4-hex}` — e.g., `ses_20260729_221530_a1b2c3`

| Alternative | Rejected because |
|---|---|
| UUID4 (`550e8400-...`) | Opaque, unreadable in CLI listings |
| Sequential integer | Requires shared state + file lock |
| Pure timestamp | Collision risk on same-second starts |

**Chosen**: Human-readable sortable prefix + random hex suffix for uniqueness. Matches spec.

## Storage Layout

```
~/.ohm/sessions/
  ses_20260729_221530_a1b2c3.json   # full session data
  ses_20260729_223145_d4e5f6.json   # another session
  last_session.json                  # pointer: {"last_session_id": "ses_..."}
```

`last_session.json` is a **pointer only** — never stores messages inline. Self-contained session files. On save: write `{session_id}.json` + update pointer. On load: read pointer → resolve file → return data. Missing/corrupt → `None`.

## Message Capture Pipeline

Two integration points in `OhmApp` (`src/ohm/cli/app.py`):

**User submit** — `_handle_input_submit` (~line 467):
```python
if text:
    chat.add_message("user", text)
    self._session_data["messages"].append({
        "role": "user",
        "content": text,
        "timestamp": datetime.now().isoformat(),
    })
```

**Agent response** — end of `_stream_agent_response` (~line 590):
```python
if full_response:
    self._session_data["messages"].append({
        "role": "agent",
        "content": full_response,
        "timestamp": datetime.now().isoformat(),
    })
```

System messages, warnings, thinking widgets are NOT captured. Content is already plain text (Markdown strings) — `json.dumps` works directly. Rich renderables exist only in `MessageWidget.update()`, not in raw content strings.

## Continue Mode Flow

### CLI → TUI path

`src/ohm/cli/registry.py` — global flag:
```python
register_global("--continue", "-c", dest="continue_",
                action="store_true", default=False,
                help="Resume the last session")
```

Registry `_launch_tui()` resolves session before constructing app:
```python
def _launch_tui(self, continue_mode: bool = False) -> int:
    session_data = None
    if continue_mode:
        session_data = _load_last_session()
        if not session_data:
            print("No previous session to continue.")
    from ohm.cli.app import OhmApp
    app = OhmApp(continue_session=session_data)
    app.run()
    # Exit banner prints after app.run() returns
    from ohm.utils.fake_data import OHM_LOGO
    print(OHM_LOGO)
    print("Continue last session:  ohm -c")
    print("Session browser:        ohm session list")
    return EXIT_SUCCESS
```

### OhmApp init & mount

`OhmApp.__init__(continue_session: dict | None = None)` — stores `self._continue_session`.

`on_mount()` — on resume: replay messages, skip welcome logo:
```python
if self._continue_session:
    msgs = self._continue_session.get("messages", [])
    if msgs:
        # Remove default welcome widget
        chat = self.query_one(ChatArea)
        scroll = chat.query_one("#chat-scroll")
        scroll.remove_children()
        for m in msgs:
            chat.add_message(m["role"], m["content"])
        self.notify(f"Resumed session ({len(msgs)} messages)")
```

### Sub-action `ohm session continue`

New `continue` sub-parser in `session.py` `register_args()`. Handler loads last session pointer → loads data → launches `OhmApp(continue_session=data)`. Same behavior as `-c`. No session → exit code 1.

## TUI Session Browser

**New file**: `src/ohm/cli/screens/session_browser.py`

`SessionBrowser(ModalScreen[dict | None])`:
- Lists `{session_id}.json` files (filters out `last_session.json`)
- Columns: ID | started | messages | theme
- Keyboard: ↑↓ navigate, Enter select (dismiss with session dict), Esc dismiss (result None)
- Empty: notify "No saved sessions found"
- Corrupt entry: skip + notify, continue listing
- Opened via new `F3` hotkey or command palette in `OhmApp`

Reuses `_list_session_files()` / `_load_session()` from `session.py`.

## Exit Banner

After `self.exit()` returns from `app.run()`, print to stdout inside `_launch_tui()`:
- Plain ASCII `OHM_LOGO` from `fake_data.py` (no ANSI escapes)
- Two lines: "Continue last session:  ohm -c" and "Session browser:  ohm session list"

## Affected Files

| File | Impact | Change |
|---|---|---|
| `src/ohm/cli/app.py` | Major | Message capture, `continue_session` param, session replay on mount, F3 hotkey |
| `src/ohm/cli/registry.py` | Medium | `--continue`/`-c` global flag, exit banner in `_launch_tui()` |
| `src/ohm/commands/session.py` | Medium | `continue` sub-action handler |
| `src/ohm/cli/screens/session_browser.py` | New | `SessionBrowser` ModalScreen |
| `src/ohm/cli/main.py` | Minor | Continue flag dispatch — minimal change |
| `tests/test_session.py` | New | Persistence + resume unit tests |
| `tests/test_cli.py` | Extend | CLI session command tests |

## Key Integration Points (code sketches)

**Save flow** — `action_quit_ohm` / `on_unmount`:
```python
session_id = self._session_data.get("session_id", self._gen_session_id())
session_path = SESSION_DIR / f"{session_id}.json"
session_path.write_text(json.dumps(self._session_data, indent=2))
(SESSION_DIR / "last_session.json").write_text(
    json.dumps({"last_session_id": session_id})
)
```

**Load flow** — helper called from `_launch_tui`:
```python
def _load_last_session() -> dict | None:
    pointer = SESSION_DIR / "last_session.json"
    if not pointer.exists():
        return None
    try:
        data = json.loads(pointer.read_text())
        sid = data.get("last_session_id")
        if not sid:
            return None
        session_file = SESSION_DIR / f"{sid}.json"
        if not session_file.exists():
            return None
        return json.loads(session_file.read_text())
    except (json.JSONDecodeError, OSError):
        return None
```

## Threat Matrix

N/A — no routing, shell, subprocess, VCS automation, or process-integration boundary.
