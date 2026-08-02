# Proposal: TUI Command Unification (FU-009..FU-016)

## Intent
TUI command surfaces are fragmented — four sources (`FAKE_COMMANDS`, orphaned `CommandRegistry`, dead `GLOBAL_BINDINGS`/`FAKE_HOTKEYS`, CLI `Registry`), none authoritative. Palette and `/` dropdown duplicate one list; neither appends skills; CLI↔TUI parity unguarded. Unify behind `CommandRegistry`; fix FU-009..FU-016.

## Scope
**In** (per FU):
- FU-009 parity mapping + guard test; FU-010 one catalog for palette + `/` dropdown
- FU-011 Ctrl+J newline in `_SubmitTextArea._on_key` (+ Ctrl+M decision); FU-012 palette filter Input
- FU-013 single-toggle guard (`App.screen_stack`) for F3/F2/Ctrl+K modals
- FU-014 skills appended last in both surfaces (`/skill <name>` → inject instructions)
- FU-015 `ModalMenu`/`ModelSelector` → `ModalScreen` subclasses (translucent dim, centered)
- FU-016 left/right collapse/expand in `ModelSelector`
- Delete dead: `GLOBAL_BINDINGS`, `FAKE_HOTKEYS`, `get_filtered_commands`, unused `filter_commands`; retire `FAKE_COMMANDS` from UI paths

**Out**: real execution for display-only commands (`/test` runner; `/config`→SettingsModal); CLI-side behavior; provider internals.

## CLI↔TUI Mapping
| CLI | TUI | Type |
|---|---|---|
| session list/continue/clear | `/session list/continue/clear` | real action |
| config | `/config` | display-only |
| test, run, status, goal, loop | `/test` `/run` `/status` `/goal` `/loop` | display-only |
| skills, skill | `/skill <name>` dynamic | real (FU-014) |
| doctor, mcp, cron, init, serve, plugin | — | TUI-irrelevant |
| --version, -h | — | TUI-irrelevant |

## Approach (ratified: Approach 1 + ModalScreen)
1. Extend `CommandRegistry`: add `action` + `cli_only`/`tui_irrelevant`; register session commands; wire orphaned `self.commands`
2. Shared pure `palette_entries(skills)` builder → catalog + skills last; consumed by both surfaces
3. FU-015: both widgets → `ModalScreen` (dim via `DEFAULT_CSS`; unifies FU-013 guard)
4. FU-011/012/016 widget fixes; FU-013 `screen_stack` guard
5. Delete dead lists; parity test imports `register_all`

## Capabilities
- **New**: `tui-commands` — single-source catalog, palette/`/` parity, skills surfacing, keybinding semantics (Ctrl+J), modal guard, model-selector navigation
- **Modified**: None (provider/skills specs unchanged)

## Affected Areas
| Area | Impact |
|---|---|
| `src/ohm/core/commands.py` | Modified — catalog + `action` field |
| `src/ohm/cli/app.py` | Modified — wire registry, guards, dropdown, CSS |
| `src/ohm/cli/widgets/modal_menu.py` | Modified — ModalScreen + filter Input |
| `src/ohm/cli/widgets/model_selector.py` | Modified — ModalScreen + left/right |
| `src/ohm/cli/widgets/input.py` | Modified — Ctrl+J |
| `src/ohm/cli/keybindings.py`, `src/ohm/utils/fake_data.py` | Removed — dead lists |
| `tests/test_cli.py`, `tests/cli/test_input.py` | Modified — parity + widget tests |

## Risks
| Risk | L | Mitigation |
|---|---|---|
| Textual 8.2.8 drift (no `input_newline`; ctrl+j=newline) | High | Code vs verified APIs; widget tests |
| 8 FUs vs 400-line budget | High | Sized slices; size:exception; manual-test gate |
| FU-015 conversion churn | Med | Direction ratified; backdrop (Option B) fallback |
| Ctrl+M alias / terminal Ctrl+J coalescing | Med | Explicit `_on_key` handling; smoke test |

## Rollback Plan
Revert branch `feature/tui-command-unification` (per-slice if chained). No data migration. FU-015 fallback: keep widgets + dim backdrop.

## Dependencies
- Textual 8.2.8 (verified: `KEY_ALIASES`, `TextArea.insert`, `App.screen_stack`)
- CLI `register_all`; `SkillLoader.discover_skills` paths (skill.py:34-39)

## Success Criteria
- [ ] Parity test: every CLI subcommand mapped (real/display-only/irrelevant); none lost
- [ ] Palette + dropdown render identical sets; skills appended last
- [ ] Ctrl+J inserts newline; repeated F3/F2/Ctrl+K never stacks
- [ ] Filter Input live; left/right expand/collapse; FU-015 dim+center
- [ ] `uv run pytest` green

## Phase Notes (sdd-spec)
- Parity test asserts mapping-table relationships, not CLI behavior
- Builders pure/injectable; keybinding + modal-guard Given/When/Then; update widget tests for ModalScreen conversion
- Open: Ctrl+M alias handling; `/config`→SettingsModal wiring (default: display-only)
