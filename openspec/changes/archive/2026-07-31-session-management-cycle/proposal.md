# Proposal: Session Management Cycle

## Intent

Sessions save metadata but NEVER persist chat history. TUI exits silently with no resume path. Users lose context between sessions. This makes sessions actually useful: messages persisted, sessions resumable from CLI or TUI, exit prints logo + instructions.

## Scope

### In Scope
1. Message capture at user submit + agent response → persisted to session files
2. Multi-session support (timestamped IDs, not just `last_session.json`)
3. `ohm -c`/`ohm --continue` global flag + `ohm session continue` sub-action
4. TUI exit banner: OHM logo + `ohm -c continue last session`
5. In-TUI session browser (modal screen, select from saved list)
6. Session replay on resume (load + render messages into ChatArea)

### Out of Scope
- strands-agents FileSessionManager integration (custom persistence simpler)
- Cloud/remote session storage
- Session export/import

## Capabilities

### New Capabilities
- `session-persistence`: Track & serialize full conversation history in session files, multi-session support, restore on load
- `session-resume`: CLI resume flag, TUI session browser, exit banner with logo + instructions

### Modified Capabilities
None — no existing session specs.

## Approach

1. **Format**: Extend current JSON schema — add `session_id` (timestamp-based UUID), populate `messages[]` at submit + response boundaries, save as `{session_id}.json`; `last_session.json` becomes pointer to latest
2. **Serialization**: Strip Rich renderables to plain text on save; re-render as Rich on load
3. **CLI**: `register_global("--continue", "-c")` → `_launch_tui(continue=True)`; `ohm session continue` action reads + resumes last
4. **Exit**: After `self.exit()`, print `OHM_LOGO` (plain ASCII) + resume instructions to stdout
5. **TUI browser**: Modal listing saved sessions (reuse ModalMenu pattern) → select → replay + continue
6. **TDD**: Write persistence tests before implementation

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/ohm/cli/app.py` | Major | Message capture, session ID, exit banner, restore, browser modal |
| `src/ohm/cli/registry.py` | Medium | Add `--continue`/`-c` global flag |
| `src/ohm/commands/session.py` | Medium | Add `continue` action |
| `src/ohm/cli/main.py` | Minor | Pass continue flag to TUI |
| `tests/test_session.py` | New | Persistence + resume tests |
| `tests/test_cli.py` | New | CLI session command tests |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Rich renderables don't serialize to JSON | High | Strip to plain text on save; re-render on load |
| `last_session.json` migration loses data | Medium | Keep as pointer; never delete old format |
| Async message capture intersects streaming | Medium | Append at submit/response-end boundaries only |

## Rollback Plan

Revert `registry.py` flags, revert `app.py` message tracking + exit banner, revert `session.py` continue action. Restore `last_session.json` as sole session file. Old-format sessions remain readable — no data loss.

## Dependencies

- `strands-agents>=1.50.1` (already installed)
- No new external dependencies

## Success Criteria

- [ ] `ohm -c` resumes last session with full message history visible in ChatArea
- [ ] Messages survive TUI restart: send → quit → `ohm -c` → message shown
- [ ] TUI exit prints OHM logo + `ohm -c continue last session`
- [ ] `ohm session continue` works identically to `ohm -c`
- [ ] In-TUI browser lists sessions, selecting one loads + continues
- [ ] All session tests pass (`uv run pytest`)
