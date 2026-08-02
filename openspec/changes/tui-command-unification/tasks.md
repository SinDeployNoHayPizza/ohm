# Tasks: TUI Command Unification (FU-009..FU-016)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | S1: ~450-550 · S2: ~380-450 · S3: ~150-220 · Total: ~980-1220 |
| 400-line budget risk | Total: High · S1: High · S2: Med-High · S3: Low-Med |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (slice 1) → PR 2 (slice 2) → PR 3 (slice 3) |
| Delivery strategy | ask-on-risk (default; not passed) |
| Chain strategy | pending — user choice |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Catalog + parity + skills (R1/R2/R3, R9 lists) | PR 1 | `uv run pytest tests/test_command_catalog.py tests/test_cli.py` | N/A — pure builder + registry bijection; pytest-only | Revert commands.py/loader.py/skill.py hunks + catalog test files |
| 2 | Widget fixes (R4/R5/R6/R8) | PR 2 | `uv run pytest tests/cli/test_input.py tests/cli/test_modal_menu.py tests/cli/test_model_selector.py` | Headless `App.run_test()`: pilot.press ctrl+j/ctrl+m/F3; type filter; left/right | Revert input.py/modal_menu.py/model_selector.py + app.py guard hunks |
| 3 | FU-015 ModalScreen (R7) | PR 3 | `uv run pytest tests/cli/` | Headless run_test asserting ModalScreen + CSS dim/center | Revert conversion hunks; backdrop restyle fallback retained |

Base chain: PR 1 base = feature/tui-command-unification; PR 2 base = PR 1 branch; PR 3 base = PR 2 branch.

## Slice 1: Catalog + Parity + Skills (R1/R2/R3)

- [x] 1.1 RED: `tests/test_command_catalog.py` — `palette_entries` empty, catalog-then-skills-sorted ordering, kinds, payload
- [x] 1.2 GREEN: `src/ohm/core/commands.py` — add `CommandKind`, `Command` fields (kind/action/payload/cli_equivalent), frozen `PaletteEntry`, pure `palette_entries(commands, skills=None)`; register 4 session commands (browser + list/continue/clear) as REAL
- [x] 1.3 RED: `tests/test_cli.py` — R1 parity: `register_all(Registry())` names biject with `CLI_TUI_MAPPING` keys; count equal; none omitted
- [x] 1.4 GREEN: `src/ohm/core/commands.py` — add `CLI_TUI_MAPPING` (15 subcommands + `--version`/`-h`)
- [x] 1.5 RED: R3 scenario — `/skill python`/`/skill debug` appended at N+1..N+2
- [x] 1.6 GREEN: `src/ohm/core/skills/loader.py` — hoist `DEFAULT_SKILL_SEARCH_PATHS`; `commands/skill.py` reuses; `OhmApp._skills` loaded once in `on_mount`
- [x] 1.7 GREEN: `src/ohm/cli/app.py` — wire `self.commands`, dropdown from `palette_entries` (R2 agree), `_dispatch_command` (DD-12), `action_skill_run` (FU-014)
- [x] 1.8 R9: delete `src/ohm/cli/keybindings.py`; strip `FAKE_COMMANDS`/`FAKE_HOTKEYS` from `utils/fake_data.py`; drop FAKE_COMMANDS import in app.py; grep-clean

## Slice 2: Widget Fixes (R4/R5/R6/R8)

- [x] 2.1 RED: `tests/cli/test_input.py` — headless: ctrl+j inserts `\n` without submit; ctrl+m submits as enter
- [x] 2.2 GREEN: `src/ohm/cli/widgets/input.py` `_on_key` — ctrl+m submit, ctrl+j `insert("\n")`; delete `get_filtered_commands`
- [x] 2.3 RED: `tests/cli/test_modal_menu.py` — `_apply_filter` narrows by name/description; resets index 0
- [x] 2.4 GREEN: `modal_menu.py` — `Input#palette-filter` + Static list; `Input.Changed → _apply_filter` (DD-10)
- [x] 2.5 RED: R6 — repeated F3 never pushes second modal; `_is_open` reads `screen_stack`
- [x] 2.6 GREEN: `app.py` — `_is_open(T)` guard: toggle modals pop on repeat, push modals no-op (DD-09)
- [x] 2.7 RED: `tests/cli/test_model_selector.py` — right adds provider to `_expanded`; left removes (R8)
- [x] 2.8 GREEN: `model_selector.py` — left/right bindings → collapse/expand (DD-11)

## Slice 3: FU-015 ModalScreen Conversion (R7)

- [x] 3.1 RED: modal/model tests assert ModalScreen subclass + dim + centered (R7 scenario)
- [x] 3.2 GREEN: `modal_menu.py` → `CommandPalette(ModalScreen)`; `dismiss(entry)` selection contract
- [x] 3.3 GREEN: `model_selector.py` → `ModelSelector(ModalScreen)` wrapping render list; drop modal-wrap CSS in app.py
- [x] 3.4 VERIFY: `uv run pytest` full green; smoke: palette, `/`, ctrl+j, F3/F2/Ctrl+K no stack, left/right nav
