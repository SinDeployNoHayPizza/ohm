# Follow-ups

Tracking list for known, non-blocking issues and pending improvements across OHM.
Items are logged when a change is archived with warnings or when a review surfaces
a low-severity defect that is out of scope for the current work.

Source of truth for archived-change follow-ups: `openspec/changes/archive/<date>-<change>/archive-report.md`.

## Open

| ID | Change | Severity | Description | Proposed fix |
|----|--------|----------|-------------|--------------|
| FU-001 | skills-registry-loader | WARNING | `ohm skill inspect <name>` (design.md:9) is not implemented; `load_skills()` implemented as `register()`. | Implement `inspect` subcommand or update design; align naming. |
| FU-002 | skills-registry-loader | WARNING | Mojibake: non-ASCII glyphs `•`/`—` at `src/ohm/commands/skill.py:55` render as `�` in legacy-codepage Windows console captures. Correct in UTF-8 terminals. Cosmetic. | Replace glyphs with ASCII-safe alternatives (`-`, `*`) or force UTF-8 output. |
| FU-003 | skills-registry-loader | WARNING | 11 pre-existing ruff F401 unused imports: `src/ohm/core/skills/registry.py:5` (`typing.Sequence`) + 10 in `tests/test_cli.py`, `tests/test_skills.py`. Ruff is not a configured gate. | Remove unused imports if a lint gate is enabled. |
| FU-004 | skills-registry-loader | SUGGESTION | No unit test for same-name skill priority override across sources. | Add registry-layer test. |
| FU-005 | skills-registry-loader | SUGGESTION | `Skill.path` is never asserted in tests. | Assert path in loader tests. |
| FU-006 | skills-registry-loader | SUGGESTION | Naming drift: `parse_skill_md()` (tasks.md 1.1) vs `parse_skill_file()` (code). | Rename to match, or update tasks/design. |
| FU-007 | skills-registry-loader | SUGGESTION | Header-only `SKILL.md` handling wording vs design.md:7. | Align implementation or design wording. |
| FU-008 | skills-registry-loader | SUGGESTION | `src/ohm/commands/skill.py:59-60` unknown-action branch untested. | Add CLI test for unknown subcommand. |
| FU-009 | tui-command-unification (planned) | BUG | TUI and CLI command lists are not unified: some CLI commands have TUI counterparts (executed differently), others (version, CLI help) are TUI-irrelevant. Needs a guard test proving no command is lost. | Unify command list; keep CLI-only commands apart; add parity test. |
| FU-010 | tui-command-unification (planned) | BUG | TUI has two command lists: Ctrl+P modal and `/`-prefixed input menu — they must show the same set (plus skills at the end of each listing). | Single source of truth for both surfaces. |
| FU-011 | tui-command-unification (planned) | BUG | Evaluate Ctrl+J as `input_newline`: inserts a line break without confirming the input. | Confirm widget supports it; wire keybinding. |
| FU-012 | tui-command-unification (planned) | BUG | Command modal has no filter/search input. | Add filter input to command modal. |
| FU-013 | tui-command-unification (planned) | BUG | Pressing F3 multiple times doesn't close the modal (or stacks new modals) — requires same number of Esc presses. | Guard modal against re-open/stack; single-toggle behavior. |
| FU-014 | tui-command-unification (planned) | BUG | Skills commands missing from the command modal and the `/` popup menu. | Register skills commands in both surfaces. |
| FU-015 | tui-command-unification (planned) | BUG | Session modal is visually better (no opaque side dimming); apply the same visual style to model and command modals. | Align modal styling. |
| FU-016 | tui-command-unification (planned) | BUG | Model modal lacks collapse/expand of branches (left/right arrow keys). | Add collapse/expand navigation. |

## Resolved

| ID | Change | Resolution |
|----|--------|------------|
| — | — | — |
