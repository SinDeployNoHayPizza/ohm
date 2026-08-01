# Exploration: TUI Command Unification (FU-009..FU-016)

## Current State

### Four command sources exist; none is authoritative
- `FAKE_COMMANDS` (`src/ohm/utils/fake_data.py:72-94`) — 20 entries, the *de facto* TUI source. Both the Ctrl+K palette and the `/` dropdown read it. Only 4 entries have a `key` field wired to real `OhmApp` actions (`/sessions`→`session_browser`, `/session list`→`session_browser`, `/session continue`→`session_continue`, `/session clear`→`session_clear`); the other 16 are display-only (ModalMenu falls back to `notify("Command: X")`).
- `CommandRegistry` (`src/ohm/core/commands.py:30-163`) — 16 hardcoded default `/` commands. Instantiated in `OhmApp.__init__` (`app.py:234`) but **never used anywhere** (grep confirms no other `self.commands` reference). Orphaned.
- `GLOBAL_BINDINGS` (`src/ohm/cli/keybindings.py:17-34`) — 15 entries, **dead code** (never imported). Also the source of the "Ctrl+P" naming drift: it claims `ctrl+p → switch_provider`, but the real binding in `app.py:183` is `ctrl+k → command_palette` and no `action_switch_provider` exists.
- `FAKE_HOTKEYS` (`fake_data.py:266-285`) — 17 entries, **never referenced**.
- CLI `Registry` (`src/ohm/cli/registry.py`) + auto-discovery (`src/ohm/commands/__init__.py` `register_all`) — the real CLI: **15 subcommands** — `doctor, config, mcp, loop, cron, init, session, run, serve, plugin, test, skills, skill, status, goal` — plus TUI-irrelevant `--version`/`-h` (`registry.py:124-130, 228-236`).

### The two TUI surfaces (FU-010)
- **Ctrl+K command palette**: `ModalMenu` (`src/ohm/cli/widgets/modal_menu.py`) — a render-only `Widget` toggled by `OhmApp.action_command_palette` (`app.py:365-375`) via `show()/hide()` + `-visible` class. `render()` lists `filtered_commands`; `show()` resets to `FAKE_COMMANDS.copy()` (`modal_menu.py:109`). No skills appended.
- **`/`-prefixed input menu**: `#command-dropdown` Static, filtered in `on_input_changed` (`app.py:527-550`), executed in `_handle_input_submit` (`app.py:552-593`) against `FAKE_COMMANDS`. No skills appended.
- Both already source `FAKE_COMMANDS`, so "two lists" is really "two renderings of one list + duplicate filter logic + neither appends skills". Additional dead filter impls: `ModalMenu.filter_commands`/`filter_query` (never called) and `CommandInput.get_filtered_commands` (`input.py:135-142`, never called).

### FU-009 parity reality
CLI-only commands with no TUI counterpart: `version`, `help`, `init`, `doctor`, `mcp`, `serve`, `cron`, `plugin`, `skills`, `skill`, `run`, `status`, `test`, `goal`, `loop`. Real 1:1-ish overlaps: `ohm session list|continue|clear` ↔ `/session list|continue|clear`; `ohm config` ↔ `/config` (display-only); `ohm test` ↔ `/test` (display-only). **No parity test exists**; `tests/test_cli.py` only covers CLI registry/commands.

### Keyboard fact for FU-011 (verified against installed Textual 8.2.8)
- `textual/keys.py` `KEY_ALIASES`: `"ctrl+j": ["newline"]`, `"enter": ["ctrl+m"]` — Ctrl+J is the *newline* alias, **not** Enter.
- `TextArea` (`textual/widgets/_text_area.py:224+` BINDINGS) has **no** ctrl+j/newline binding; its insert handler (`_on_key` ~line 1818) inserts `"\n"` only for `key == "enter"` (`insert_values = {"enter": "\n"}`). **No `input_newline` action exists anywhere in textual 8.2.8** (rg: zero hits).
- `_SubmitTextArea._on_key` (`input.py:20-30`) intercepts only `event.key == "enter"` → submit. **Net effect: Ctrl+J currently does nothing** (falls through, not stopped, not submitted). Latent quirk: `ctrl+m` (Enter alias) also bypasses the submit check.

### F3 stacking (FU-013)
`action_session_browser` (`app.py:382-406`) calls `self.push_screen(SessionBrowser())` **unconditionally** → each F3 pushes a new modal; Esc pops one per press. Same unconditional-push pattern in `action_settings` (`app.py:377-380`) and `action_quit_ohm` (`app.py:314-323`). By contrast Ctrl+K palette and F2 model selector already use single-toggle `is_shown` guards. Textual 8.2.8 exposes `App.screen_stack` (`textual/app.py:1206`).

### FU-014 skills
Skills are discoverable via `SkillLoader.discover_skills(search_paths)` (`core/skills/loader.py:59-75`) with paths in `commands/skill.py:34-39` (`.agents/skills`, `.ohm/skills`, `~/.ohm/skills`, `~/.gemini/skills`). The TUI **never loads skills** — neither palette nor `/` menu shows them.

### FU-015 modal styling (verified rendering)
`SessionBrowser`/`SettingsModal` are `ModalScreen` subclasses → inherit `ModalScreen.DEFAULT_CSS` `background: $background 60%` (`textual/screen.py:2158+`) — translucent dim of the app + centered dialog (`align: center middle`). `ModalMenu`/`ModelSelector` are plain `Widget`s — opaque `background: $surface` boxes, `display:none`-toggled, docked bottom via `#modal-wrap`/`#model-selector-wrap` (`layer: modal`, `app.py:154-177`), **no backdrop at all**. The FU-015 parenthetical is imprecise ("no opaque side dimming") but the intent is unambiguous: *align model/command modals to the session-modal presentation*.

### FU-016 collapse/expand
`ModelSelector` (`model_selector.py`) binds only `space → toggle_expand` (`:42`, action `:225-230`); `_expanded: set[int]` holds provider indices. No left/right bindings exist.

## Affected Areas
- `src/ohm/cli/app.py` — command palette toggle (365-375), `/` dropdown filter+execute (527-593), F2/F3 push/toggle (382-493), unused `self.commands` (234), modal wrap CSS (154-177).
- `src/ohm/cli/widgets/modal_menu.py` — source of `FAKE_COMMANDS`; dead `filter_commands`; no filter Input; no skills; styling.
- `src/ohm/cli/widgets/input.py` — `_SubmitTextArea._on_key` (FU-011), dead `get_filtered_commands`.
- `src/ohm/cli/widgets/model_selector.py` — left/right expand bindings (FU-016), styling (FU-015).
- `src/ohm/core/commands.py` — `Command`/`CommandRegistry`: candidate canonical catalog (needs `action` field + session/skills entries).
- `src/ohm/core/skills/{loader,registry,schema}.py` — skills discovery for FU-014.
- `src/ohm/cli/keybindings.py`, `src/ohm/utils/fake_data.py` (FAKE_COMMANDS/FAKE_HOTKEYS) — dead lists to retire or repurpose.
- `src/ohm/cli/screens/session_browser.py` — styling reference (FU-015), stacking guard target (FU-013).
- `tests/test_cli.py`, `tests/cli/test_input.py` — conventions: widgets/registries tested directly, no running app; parity + palette tests go here.

## Approaches (core problem: FU-009 / FU-010 / FU-014 — single source of truth)

1. **Extend and wire the existing `CommandRegistry` (`core/commands.py`)**
   Add `action: str | None` field to `Command`; register the 4 real session commands + explicit `cli_only`/`tui_irrelevant` flags; make `OhmApp` use its already-instantiated `self.commands` (app.py:234); ModalMenu and `/` dropdown both query a shared pure builder (e.g. `CommandRegistry.palette_entries(skills: list[Skill] | None)`) that merges catalog + skills appended last; delete dead lists (`GLOBAL_BINDINGS`, `FAKE_HOTKEYS`, `get_filtered_commands`, unused `filter_commands`); parity test imports `register_all` + this catalog.
   - Pros: reuses existing class and the orphaned instance (clearly the original intent); smallest new-code surface; pure functions are trivially TDD-testable; one list everywhere.
   - Cons: catalog lives in `core/` but lists TUI actions (mild layering smell); skills stay dynamic (loader), so the builder must inject them; touches 3 consumers.
   - Effort: Medium.

2. **New dedicated `command_catalog.py` module (fresh canonical catalog)**
   A pure-Python catalog of all TUI commands with explicit metadata (`cli_equivalent`, `tui_irrelevant`, `action`), plus shared builders for palette/`/`-menu listings (skills appended), consumed by both surfaces; retire `FAKE_COMMANDS` from UI paths; parity test against CLI registry.
   - Pros: cleanest semantics; explicit CLI↔TUI mapping table per entry; no fake-data provenance; isolates the UI-command domain.
   - Cons: bigger diff (new module + 3-consumer migration); would coexist with or duplicate `core/commands.py` unless it is retired; higher effort and review load.
   - Effort: High.

## Per-FU concrete fixes

- **FU-011** — `input.py` `_SubmitTextArea._on_key`: add `elif event.key == "ctrl+j":` → `event.stop(); event.prevent_default(); self.insert("\n")` (`TextArea.insert` exists, `_text_area.py:2465`). Do **not** bind to `input_newline` — it does not exist in textual 8.2.8. Optionally also treat `ctrl+m` as submit for alias symmetry. Effort: Low.
- **FU-012** — give `ModalMenu` a `compose()` yielding an `Input` + the list area, wire `@on(Input.Changed) → filter_commands` (method already exists, `modal_menu.py:120-132`); or lightweight: reuse `app.py:527` `on_input_changed` to call `filter_commands` while the palette is shown. Effort: Low-Med.
- **FU-013** — guard pushes: in `action_session_browser` (and `action_settings`, `action_quit_ohm`), `if not any(isinstance(s, SessionBrowser) for s in self.screen_stack): push` — repeat F3 then pops/returns to top. Applies the Ctrl+K/F2 single-toggle behavior to screen modals. Effort: Low.
- **FU-014** — shared builder loads skills once (e.g. `SkillLoader.discover_skills(skill.py:34-39 paths)` cached in `OhmApp`) and appends entries (e.g. `/skill <name>`) after the catalog in **both** surfaces; wire to a real action (e.g. inject skill instructions into the agent prompt / chat). Effort: Low-Med.
- **FU-015** — align `ModalMenu`/`ModelSelector` with the `ModalScreen` presentation (translucent dim + centered dialog). Option A (preferred by consistency): convert both to `ModalScreen` subclasses pushed via `push_screen` — dim comes free; also unifies FU-013 guarding. Option B (minimal): add a dim backdrop layer behind the existing widgets. Option A requires updating `action_command_palette`/`action_model_selector` and widget-level tests. Effort: Med.
- **FU-016** — `model_selector.py` BINDINGS: add `Binding("left", "collapse")` + `Binding("right", "expand")` (or map both to `toggle_expand`); add actions that `discard`/`add` the current provider in `_expanded`. Effort: Low.

## Recommendation

**Approach 1** (extend + wire the existing `CommandRegistry`) — it resurrects an orphaned class and an unused instance already in `OhmApp`, delivering the single source of truth for Ctrl+K palette, `/` menu, and skills with the least new code, and it makes FU-009's parity test a pure catalog-vs-CLI comparison. Sequence the change as: (1) catalog unification + parity test (FU-009/010/014), (2) small widget fixes (FU-011/012/013/016), (3) modal styling (FU-015). Confirm the FU-015 direction (convert-to-`ModalScreen` vs backdrop restyle) and the CLI↔TUI mapping table during proposal — both are judgment calls the user should ratify.

## Risks

- **Textual 8.2.8 API drift**: code was written against the 0.80-era API; verified today: `ModalScreen` dims via `$background 60%`, `ctrl+j`→`newline` alias, no `input_newline`, `TextArea.insert` exists. Any design assuming `input_newline` will fail.
- **FU-015 ambiguity**: the follow-up's parenthetical does not match the actual rendering (session modal *does* dim, widget modals don't). Direction must be ratified in proposal.
- **FU-009 semantics**: "CLI counterparts executed differently" needs an explicit mapping table (e.g. does `/config` open `SettingsModal`? does `/test` call the test runner?); without it the parity test can only assert *documented* relationships, not behavior.
- **Scope/400-line budget**: 8 FUs in one change is High risk; likely needs chaining (e.g. PR 1 catalog+parity, PR 2 widget fixes, PR 3 styling). Forecast explicitly in tasks.
- **Ctrl+M quirk**: Enter's alias bypasses the submit path today; if FU-011 touches `_on_key`, decide ctrl+m handling to avoid inconsistent behavior.
- **Terminal coalescing**: Ctrl+J vs Enter may merge on some Windows terminals; unit-test the handler branch, but plan a manual smoke check.

## Ready for Proposal

Yes — exploration is complete and verified against real code (Textual 8.2.8 installed). Tell the orchestrator: propose FU-009/010/014 via Approach 1 (extend `CommandRegistry`), include the CLI↔TUI mapping table, ratify the FU-015 direction (ModalScreen conversion vs backdrop restyle), and expect a High 400-line budget risk requiring chained PRs.
