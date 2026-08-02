# TUI Commands Specification

## Purpose

Single-source TUI command catalog backed by `CommandRegistry`: CLI↔TUI parity, skills surfacing, consistent keybinding, filtering, modal, navigation behavior across Ctrl+K palette and `/` dropdown.

## Requirements

### Requirement: CLI↔TUI Command Parity (R1)

Every subcommand from `register_all` MUST map to exactly one class — `real action`, `display-only`, or `tui_irrelevant`; none MAY be omitted. Classes: real `session`/`skills`/`skill`; display-only `config`/`test`/`run`/`status`/`goal`/`loop`; irrelevant `doctor`/`mcp`/`cron`/`init`/`serve`/`plugin`/`--version`/`-h`.

#### Scenario: No command lost

- GIVEN a `Registry` populated by `register_all`
- WHEN the parity test enumerates its subcommands
- THEN each name resolves to exactly one mapping class
- AND the classified count equals the registered count

### Requirement: Single Command Catalog (R2)

The Ctrl+K palette and `/` dropdown MUST render the identical set from the shared pure builder `palette_entries(skills)`, sourced from the wired `CommandRegistry`; entries with a real action MUST dispatch it (`/sessions`, `/session list|continue|clear`).

#### Scenario: Palette and dropdown agree

- GIVEN a catalog of N entries, no skills
- WHEN both surfaces are rendered
- THEN both show the same N entries in the same order

#### Scenario: Real action dispatch

- GIVEN `/session list` selected in either surface
- WHEN executed
- THEN `session_browser` runs, not a display-only notification

### Requirement: Skills Surfacing (R3)

`palette_entries(skills)` MUST append one `/skill <name>` entry per skill AFTER all catalog entries, in both surfaces; selecting `/skill <name>` MUST inject the skill's instructions (real action).

#### Scenario: Skills appended last

- GIVEN N catalog entries and skills `[python, debug]`
- WHEN `palette_entries(skills)` is called
- THEN entries N+1 and N+2 are `/skill python` and `/skill debug`

### Requirement: Ctrl+J Newline Insertion (R4)

In the chat input, Ctrl+J MUST insert a newline at the cursor and MUST NOT submit or clear. Ctrl+M MUST submit like Enter (alias symmetry).

#### Scenario: Newline without submit

- GIVEN chat input containing `line1`
- WHEN Ctrl+J is pressed
- THEN text becomes `line1\n`; no submit occurs

#### Scenario: Ctrl+M submits

- GIVEN non-empty chat input
- WHEN Ctrl+M is pressed
- THEN input submits as Enter does

### Requirement: Palette Filter Input (R5)

The palette MUST expose a live filter Input; typing MUST narrow the visible list by name/description and reset selection to the first entry.

#### Scenario: Filter narrows

- GIVEN the palette shows all entries
- WHEN the user types `sess`
- THEN only matching entries remain; the first is selected

### Requirement: Modal Single-Toggle Guard (R6)

Repeated hotkeys (F3, F2, Ctrl+K, settings, quit) MUST NOT push a second modal while one is open.

#### Scenario: F3 does not stack

- GIVEN `SessionBrowser` is top screen
- WHEN F3 is pressed again
- THEN no second push; screen-stack length unchanged

### Requirement: Modal Screen Presentation (R7)

The command palette and model selector MUST render as `ModalScreen`-style dialogs: translucent dim over the app, centered dialog.

#### Scenario: Dim and centered

- GIVEN palette or model selector open
- THEN the app behind is dimmed; the dialog is centered

### Requirement: Model Selector Branch Navigation (R8)

Left/right arrows MUST collapse/expand the selected provider's model branch in the expanded set.

#### Scenario: Right expands

- GIVEN a collapsed provider is selected
- WHEN right is pressed
- THEN the provider index is added to the expanded set

#### Scenario: Left collapses

- GIVEN an expanded provider is selected
- WHEN left is pressed
- THEN the provider index is removed from the expanded set

### Requirement: Dead Command Sources Retired (R9)

TUI command surfaces MUST NOT source from `FAKE_COMMANDS`; `GLOBAL_BINDINGS`, `FAKE_HOTKEYS`, `get_filtered_commands`, and the unused `filter_commands` MUST be removed.

#### Scenario: No UI-path references

- GIVEN the TUI modules
- WHEN scanned for `FAKE_COMMANDS`, `GLOBAL_BINDINGS`, `FAKE_HOTKEYS`
- THEN no UI-code references exist; `get_filtered_commands`/`filter_commands` absent
