# Spec: session-resume

**Change**: `session-management-cycle` | **Status**: Draft

## 1. CLI Entry Points

### 1.1 Global Flag `ohm -c` / `ohm --continue`
Registry MUST register with `dest="continue_"`. When present:
1. Resolve `last_session.json` → load session → launch `OhmApp(continue_session=dict)`.
2. Missing/corrupt pointer → launch fresh TUI with "No previous session found" notification.

### 1.2 Sub-action `ohm session continue`
Add `continue` action to `session.py`. Reads pointer → loads session → launches TUI. No session → exit code 1 + message.

## 2. TUI Resume

### 2.1 Constructor
`OhmApp.__init__` SHOULD accept `continue_session: dict | None = None`. If provided:
1. Skip welcome logo in ChatArea.
2. On `on_ready`/`call_after_refresh`, replay `messages[]` via `chat.add_message(role, content)`.

### 2.2 Session Browser
New `SessionBrowser` modal screen listing saved sessions (exclude `last_session.json`). Each row: ID | started | messages | theme. F3 or command palette to open. Select → dismiss with data → load + resume. Empty: "No saved sessions found." Corrupt entry: skip + notify.

### 2.3 Exit Banner
After `self.exit()`, print to stdout:
```
{plain ASCII OHM_LOGO}

Continue last session:  ohm -c
Session browser:        ohm session list
```
MUST use `OHM_LOGO` (no ANSI escapes) for portable output.

## 3. Scenarios

**GIVEN** prior session with messages  
**WHEN** `ohm -c`  
**THEN** TUI launches with replayed messages, no welcome logo  

**GIVEN** no `last_session.json`  
**WHEN** `ohm -c`  
**THEN** fresh TUI + "No previous session found" notification  

**GIVEN** running TUI  
**WHEN** user quits  
**THEN** stdout shows plain ASCII OHM_LOGO + resume instruction  

**GIVEN** multiple saved sessions  
**WHEN** user selects one from browser  
**THEN** selected session messages loaded into ChatArea + chat continues
