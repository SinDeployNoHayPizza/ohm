# Exploration: Session Management Cycle

**Change**: `session-management-cycle`
**Date**: 2026-07-29
**Status**: Complete

## 1. Executive Summary

Sessions are currently auto-managed (save on exit, load on start) but the mechanism is **incomplete**: chat messages are never persisted, there's no way to resume from CLI, no logo/instructions printed on exit, and no in-TUI session browser. This exploration maps the full codebase to define exactly what needs to change.

## 2. Current Architecture

### 2.1 Session Persistence Layer

**Location**: `~/.ohm/sessions/` (defined in `src/ohm/core/config.py:32` as `SESSIONS_DIR`)

```python
GLOBAL_DIR = Path.home() / ".ohm"
SESSIONS_DIR = GLOBAL_DIR / "sessions"
```

**Format**: Single JSON file per session. Special file `last_session.json` for auto-saved state.

**Current content of `last_session.json`**:
```json
{
  "messages": [],
  "started_at": "2026-07-29T21:19:24.953293",
  "theme": "gruvbox",
  "ended_at": "2026-07-29T21:43:10.519972",
  "saved_at": "2026-07-29T21:43:10.519972"
}
```

**⚠ CRITICAL FINDING**: `messages` is an empty array `[]` — the TUI never populates `_session_data["messages"]` with actual chat history. The agent conversation is rendered in `ChatArea` widgets but is NOT serialized. Any "resume session" feature must first fix this gap.

### 2.2 Session Lifecycle in OhmApp (`src/ohm/cli/app.py`)

| Lifecycle point | Function | What it does |
|---|---|---|
| App starts (`on_mount`) | `load_session()` | Reads `last_session.json`, shows notification |
| User quits (`action_quit_ohm`) | `save_session()` | Saves metadata to `last_session.json` |
| App unmounts (`on_unmount`) | `save_session()` | Same — copies metadata on clean exit |
| No message tracking | — | `_session_data["messages"]` is initialized empty but never written to |

**Save function** (`app.py:45-49`):
```python
def save_session(state: dict) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    state["saved_at"] = datetime.now().isoformat()
    SESSION_FILE.write_text(json.dumps(state, indent=2))
```

**Load function** (`app.py:52-59`):
```python
def load_session() -> dict | None:
    if SESSION_FILE.exists():
        return json.loads(SESSION_FILE.read_text())
    return None
```

### 2.3 CLI Entry Point (`src/ohm/cli/main.py`)

- `ohm.cli.main.main()` → `Registry().parse(argv)` → `Registry.dispatch(result)`
- No subcommand → launches TUI via `_launch_tui()` → `OhmApp().run()`
- **No `--continue` / `-c` flag exists**
- **No `continue` subcommand exists**

**Global args**: Only `--version/-V`. No session-related flags.

**Custom Registry** in `src/ohm/cli/registry.py`:
- Supports global args via `register_global()`
- Supports subcommands via `register_subcommand()`
- `register_global` can add `--continue` / `-c` at the top level

### 2.4 Session CLI Command (`src/ohm/commands/session.py`)

Current sub-actions: **list**, **show**, **delete**, **clear**

**No `continue` action.** The command covers CRUD but not resume.

Session IDs are filename stems. `last_session.json` is explicitly filtered out:
```python
files = [f for f in files if f.name != "last_session.json"]
```

### 2.5 TUI Structure (`src/ohm/cli/app.py`)

```
OhmApp (Textual App)
├── ChatArea (chat display + welcome/logo)
├── ContextProgress (token progress bar)
├── CommandInput (text input)
├── Sidebar (provider/model/status)
├── StatusBar
├── ModalMenu
├── FileIncluder
├── ModelSelector
└── QuitConfirm (modal dialog on ctrl+q)
```

**Quit flow**: `ctrl+q` → `QuitConfirm` dialog → `save_session()` → `self.exit()`
**No post-exit output**: after `self.exit()`, the app just returns to the shell with no logo or resume instructions.

### 2.6 Logo Assets (`src/ohm/utils/fake_data.py`)

Four logo variants exist:
- `OHM_LOGO` — plain ASCII (7 lines + subtitle)
- `OHM_LOGO_SMALL` — same art (used in `Banner` widget)
- `OHM_LOGO_ANSI` — ANSI-colored blue variant
- `OHM_LOGO_VARIANTS` — dict of 6 color variants (blue, cyan, green, purple, red, silver)
- `get_random_logo()` — returns a random color variant

**Banner widget** (`src/ohm/cli/widgets/banner.py`):
```python
class Banner(Widget):
    """Textual widget — renders OHM_LOGO_SMALL + version in Rich style."""
```

**Chat welcome** (`src/ohm/cli/widgets/chat.py:65-72`):
```python
if self.role == "welcome":
    logo = Text.from_ansi(get_random_logo())
    logo.append(f"\nv{__version__} | ...")
```

### 2.7 Message History (Missing Piece)

In `_stream_agent_response()` (`app.py:482-623`), agent responses are rendered to `ChatArea` via `chat.add_message()` but are NOT appended to `self._session_data["messages"]`. The session data only tracks metadata.

To support resume, the TUI needs to:
1. Capture user messages and agent responses into `_session_data["messages"]`
2. On load, replay saved messages into `ChatArea`
3. Persist the session ID so it can be referenced on resume

### 2.8 Available Commands Overview

```
Commands registered in src/ohm/commands/:
  run, session, config, status, init, doctor,
  goal, loop, serve, cron, skills, plugin, mcp, test_cmd
```

Auto-discovered via `pkgutil.iter_modules` in `src/ohm/commands/__init__.py`.

### 2.9 Test Coverage (`tests/`)

| Test file | Session-related tests |
|---|---|
| `tests/test_cli.py` | `test_session_command_imports` — only checks the import |
| `tests/test_agent.py` | None for sessions |
| `tests/test_config.py` | Config loading tests, no session tests |
| `tests/cli/test_progress.py` | No |
| `tests/cli/test_input.py` | No |

**No tests exist for**: session persistence, session CLI commands, TUI session lifecycle, resume mechanism.

## 3. Implementation Blueprint

### 3.1 What Must Change

| Component | What | Why |
|---|---|---|
| `src/ohm/cli/app.py` | Track messages in `_session_data["messages"]` | So sessions actually contain history |
| `src/ohm/cli/app.py` | Print logo + resume instructions on exit | Core user requirement |
| `src/ohm/cli/app.py` | Load and replay messages on `on_mount()` | Restore conversation from session |
| `src/ohm/cli/app.py` | Add session list/selection in TUI | Resume from within TUI |
| `src/ohm/cli/app.py` | Change session filename from `last_session.json` to timestamped/id | Support multiple sessions |
| `src/ohm/cli/registry.py` | Add `--continue`/`-c` global flag | CLI resume entry point |
| `src/ohm/commands/session.py` | Add `continue` action or new `continue` command | `ohm session continue` or `ohm continue` |
| Logo rendering | Reuse existing logo assets for CLI exit output | Logo exists, just needs to be printed on exit |
| Tests | Add comprehensive session tests | Strict TDD requirement |

### 3.2 Architecture Decisions to Make

1. **CLI resume syntax**: `ohm -c continue` (global flag) vs `ohm continue` (subcommand) vs `ohm session continue` (session sub-action). The user's example says `ohm -c continue last session`.

2. **Session ID format**: Use a human-readable format vs UUID for session filenames.

3. **Message serialization format**: How much of the agent response to persist (plain text vs markdown vs Rich renderables).

4. **TUI resume UI**: Modal screen, sidebar section, or new screen for session browser.

5. **Logo on exit**: Which logo variant (plain ASCII for CLI safety vs ANSI color). ANSI works in most modern terminals but plain ASCII is safer.

### 3.3 Affected Files

```
src/ohm/cli/app.py           — Major: message tracking, exit output, session restore, in-TUI resume
src/ohm/cli/registry.py      — Medium: add --continue/-c global flag
src/ohm/commands/session.py  — Medium: add continue action
src/ohm/cli/main.py          — Minor: dispatch continue flag path
src/ohm/utils/fake_data.py   — Minor: potentially expose logo for CLI use
tests/test_cli.py            — New: session command tests
tests/test_session.py        — New: session persistence tests (new file)
```

## 4. Key Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Messages may contain rich Rich/Textual renderables (Markdown, Syntax) that don't serialize cleanly to JSON | Session restore shows raw markup | Strip or convert to plain text for persistence; re-render on load |
| No existing mechanism to track chat messages in session — requires careful integration with `_stream_agent_response()` and `_handle_input_submit()` | Messages lost on restart | Capture at both user input and agent response points |
| `last_session.json` is a fixed filename — if concurrent sessions exist, resume is ambiguous | Wrong session restored | Migrate to timestamped filenames; `last_session.json` becomes a symlink/pointer or we always prompt |
| Agent streaming is async and interleaved — capturing messages must not block UI | UI jank | Append at natural boundaries (submit, response end) |
| Strict TDD means tests must be written BEFORE implementation code | Slower start | Plan test structure in advance; unit tests for serialize/deserialize first |
| Logo assets are in `fake_data.py` (demo data file) — not ideal for production code | Architectural smell | Move logo to a proper assets module, or import from fake_data with clear naming |

## 5. Session Persistence Flow (Proposed)

```
CLI: ohm -c continue
  │
  ├─ Registry detects --continue flag
  ├─ Launches OhmApp with continue=True
  │
OhmApp.on_mount()
  │
  ├─ Load last_session.json
  ├─ If messages exist, replay into ChatArea
  ├─ Set session_id = saved session_id (or new)
  │
  │   [User interacts with agent]
  │
  ├─ On each user input: append to _session_data["messages"]
  ├─ On each agent response: append to _session_data["messages"]
  │
  │   [User quits via ctrl+q or close]
  │
  ├─ QuitConfirm dialog
  ├─ save_session() with full message history
  ├─ PRINT logo + "Continue with: ohm -c continue"
  └─ exit()
```

## 6. Discovery Log

- **Session messages are never saved**. The `_session_data["messages"]` attribute exists but is never populated. This is the fundamental gap that makes resume impossible today.
- **TUI exits silently** — no logo, no instructions, no feedback. The user drops back to shell with no indication OHM was running or how to resume.
- **Logo assets are rich and varied** — 6 ANSI color variants exist plus plain ASCII. Ready for use on exit.
- **Registry supports global flags** — adding `--continue`/`-c` is straightforward via `register_global()`.
- **`last_session.json` is special** — filtered out from `session list` and always overwritten. This must be handled carefully to avoid losing previous session data.
- **No existing in-TUI session browser** — the TUI has no screen or modal for listing/selecting sessions. The ModalMenu or ModelSelector patterns could be reused.
- **Test coverage for sessions is minimal** — only an import test exists. Strict TDD requires new test files.
