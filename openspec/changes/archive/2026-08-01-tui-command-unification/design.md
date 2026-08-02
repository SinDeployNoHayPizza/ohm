# Design: TUI Command Unification (FU-009..FU-016)

## Technical Approach

Make `CommandRegistry` (`src/ohm/core/commands.py`) the single TUI command source: extend `Command` with kind/action metadata, register the 4 real session commands, expose a pure `palette_entries(commands, skills)` builder consumed by both the Ctrl+K palette and the `/` dropdown (R2/R3). Convert both modal widgets to `ModalScreen` subclasses (dim + centered free from `DEFAULT_CSS`, verified) (R7). Guard modal pushes via `App.screen_stack` (R6). Apply key/filter/nav fixes (R4/R5/R8) and delete dead lists (R9). Satisfies R1–R9.

## Data / State

- `Command` gains `kind`, `action`, `payload`, `cli_equivalent`; defaults keep the 16 existing entries as DISPLAY_ONLY.
- Module-level `CLI_TUI_MAPPING: dict[str, CommandKind]` — all 15 `register_all` subcommands + `--version`/`-h` (R1 authority).
- Frozen `PaletteEntry` + pure `palette_entries(commands, skills=None)`.
- `OhmApp._skills` loaded once in `on_mount` via `SkillLoader.discover_skills(DEFAULT_SKILL_SEARCH_PATHS)` (hoisted to `core/skills/loader.py`; `commands/skill.py` reuses).
- Deleted (grep-verified dead): `FAKE_COMMANDS`, `FAKE_HOTKEYS`, `keybindings.py`, `get_filtered_commands`, dead `filter_commands` (replaced by `_apply_filter`, keeping R9's absence scenario).

## Architecture Decisions

| # | Topic | Choice / Rationale |
|---|---|---|
| DD-01 | R4 Ctrl+M | `_on_key`: `("enter","ctrl+m")` → submit; `("ctrl+j","newline")` → `insert("\n")`, no submit. `KEY_ALIASES` verified; no `input_newline` in 8.2.8. |
| DD-02 | `/config` | Display-only per ratified mapping; SettingsModal wiring deferred. |
| DD-03 | FU-015 | ModalScreen conversion (ratified): inherited `DEFAULT_CSS` dims, subclass CSS centers. Backdrop = fallback only. |
| DD-04 | skills order | Catalog in registration order, then `/skill <name>` sorted by name — deterministic, pure-testable (R3). |
| DD-05 | mapping authority | `CLI_TUI_MAPPING` in `core/commands.py`; parity test asserts bijection vs `register_all` (R1). |
| DD-06 | kind encoding | `CommandKind` enum — a bool pair allows impossible `cli_only and tui_irrelevant`. |
| DD-07 | builder shape | Pure module fn (registry = data, fn = view); trivially TDD-testable. |
| DD-08 | skills paths | Hoist to `core/skills/loader.py`; app.py + skill.py share. |
| DD-09 | R6 guard | `_is_open(T)` via `screen_stack`. Toggle modals (palette/F2) pop on repeat; push modals (F3/settings/quit) no-op. Pop auto-restores focus. |
| DD-10 | FU-012 filter | Palette composes `Input#palette-filter` + Static list; `Input.Changed → _apply_filter` (name/description, reset index 0). |
| DD-11 | FU-016 nav | `left → collapse_provider`, `right → expand_provider`; `discard`/`add` in `_expanded` (R8). |
| DD-12 | dispatch | One `_dispatch_command(entry)`: REAL → `action_{action}`(payload); DISPLAY_ONLY → chat "Command executed". Palette + `/` submit share it. |

## Data Flow

```
CommandRegistry (get_all) ──┐          SkillLoader.discover_skills (on_mount → _skills)
CLI_TUI_MAPPING (R1) ───────┼─► palette_entries(commands, skills) → list[PaletteEntry]
                            │          (pure; R2/R3)
  Ctrl+K: push_screen(CommandPalette(entries))
      Input.Changed → _apply_filter (R5) → enter → dismiss(entry)
  "/": on_input_changed filters entries (R2); submit matches entry
          │
          ▼
  _dispatch_command(entry): REAL → OhmApp action (session_browser, skill_run(payload))
                           DISPLAY_ONLY → notify/chat message
```

## File Changes

| File | Action | Description |
|---|---|---|
| `src/ohm/core/commands.py` | Modify | `CommandKind`, `Command` fields, `PaletteEntry`, `palette_entries`, `CLI_TUI_MAPPING`, 4 session commands |
| `src/ohm/cli/app.py` | Modify | Wire `self.commands`; push/pop + R6 guards; `_dispatch_command`; `_skills`; dropdown from entries; `action_skill_run`; drop modal-wrap CSS + FAKE_COMMANDS import |
| `src/ohm/cli/widgets/modal_menu.py` | Modify | → `CommandPalette(ModalScreen)`: filter Input + Static list; `dismiss(entry)` |
| `src/ohm/cli/widgets/model_selector.py` | Modify | → `ModelSelector(ModalScreen)` wrapping render list; left/right bindings |
| `src/ohm/cli/widgets/input.py` | Modify | `_on_key` ctrl+j/ctrl+m; delete `get_filtered_commands` |
| `src/ohm/core/skills/loader.py` | Modify | `DEFAULT_SKILL_SEARCH_PATHS` |
| `src/ohm/commands/skill.py` | Modify | reuse hoisted paths (unchanged) |
| `src/ohm/cli/keybindings.py` | Delete | dead `GLOBAL_BINDINGS` |
| `src/ohm/utils/fake_data.py` | Modify | delete `FAKE_COMMANDS`, `FAKE_HOTKEYS` |
| `tests/test_cli.py` | Modify | R1 parity tests |
| `tests/test_command_catalog.py` | Create | builder unit tests (R2/R3, ordering, kinds) |
| `tests/cli/test_input.py` | Modify | R4 ctrl+j/ctrl+m, headless `run_test` |
| `tests/cli/test_modal_menu.py` | Create | R5 filter, R7 ModalScreen/CSS, R6 guard |
| `tests/cli/test_model_selector.py` | Create | R8 left/right expand/collapse |

## Interfaces / Contracts

```python
class CommandKind(Enum): REAL; DISPLAY_ONLY; TUI_IRRELEVANT

@dataclass
class Command:
    name: str; description: str; category: CommandCategory
    hotkey: str | None = None
    handler: Callable | None = None
    requires_args: bool = False
    hidden: bool = False
    kind: CommandKind = CommandKind.DISPLAY_ONLY
    action: str | None = None          # app action name, e.g. "session_browser"
    payload: str | None = None         # dynamic arg, e.g. skill name
    cli_equivalent: str | None = None  # CLI subcommand (R1)

@dataclass(frozen=True)
class PaletteEntry:
    name: str; description: str; hotkey: str | None
    action: str | None; payload: str | None; kind: CommandKind

def palette_entries(commands, skills=None) -> list[PaletteEntry]: ...
CLI_TUI_MAPPING: dict[str, CommandKind] = {...}  # 15 subcommands + --version/-h
```
Modals: `push_screen(Screen, callback)` / `pop_screen()`; selection via `dismiss(entry)`.

## Testing Strategy

| Layer | What | Approach |
|---|---|---|
| Unit | `palette_entries` | empty / ordering (catalog then skills sorted) / kinds / payload |
| Unit | parity R1 | `register_all(Registry())` names == `CLI_TUI_MAPPING` keys (bijection, equal count) |
| Unit | `_on_key` R4 | headless `App.run_test()` + `pilot.press("ctrl+j"/"ctrl+m")` |
| Unit | filter R5 | `_apply_filter` narrows, resets index 0 |
| Unit | nav R8 | expand/collapse actions mutate `_expanded` |
| Unit | guard R6 | `_is_open` on `screen_stack`; repeated F3 no second push |

## Threat Matrix

N/A — no shell, subprocess, VCS/PR automation, executable-file, or process-integration boundary is introduced (`/test` stays display-only; dispatch is TUI-internal `getattr` over a static catalog, never user-keyed). All five matrix rows N/A.

## Migration / Rollout

No data migration. Slices per proposal: (1) catalog + parity + skills; (2) widget fixes; (3) FU-015 conversion. Rollback: revert slice/branch; FU-015 fallback = backdrop restyle. Compatibility: Ctrl+M now submits (was silent fall-through); Ctrl+J gains newline; modals become pushed screens (wrap CSS deleted).

## Open Questions

- [ ] Palette list: render()-based Static body vs `ListView` — design assumes minimal Static-body change.
- [ ] `action_skill_run` injection target: system-prompt append vs chat message — minimal = chat message + prompt append.
