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

## Resolved

| ID | Change | Resolution |
|----|--------|------------|
| FU-001 | skills-registry-followups | Implemented in change `skills-registry-followups`: `ohm skill inspect <name>` subcommand (exit 0 known / 1 unknown) wired in `src/ohm/commands/skill.py`; `load_skills()`/`register()` naming retained, `inspect` added alongside. |
| FU-002 | skills-registry-followups | Implemented: replaced non-ASCII glyphs `•`/`—` with ASCII-safe `-` in `src/ohm/commands/skill.py` output; `test_skill_list_output_is_ascii_only` guards it. |
| FU-003 | skills-registry-followups | Implemented: removed all 11 ruff F401 unused imports (`src/ohm/core/skills/registry.py` + 10 across tests); ruff check clean on change files. |
| FU-004 | skills-registry-followups | Implemented: `test_discover_skills_priority_override_first_wins` proves same-name priority override (loader `discover_skills` first-wins across sources). |
| FU-005 | skills-registry-followups | Implemented: `Skill.path` is now absolute via `path.parent.resolve()` in `parse_skill_file` (spec-compliant "Absolute Path"); `test_discover_skills_path_is_absolute` asserts it. |
| FU-006 | skills-registry-followups | Implemented: parser entry point renamed to `parse_skill_file` (canonical name); no dangling `parse_skill_md` references in src/tests. |
| FU-007 | skills-registry-followups | Implemented: canonical `skills-registry` spec wording aligned — frontmatter-only parsing + directory-name fallback (header-only SKILL.md handled); `test_parse_skill_file_header_only_falls_back_to_dirname` covers it. |
| FU-008 | skills-registry-followups | Implemented: `test_skill_handler_unknown_action_returns_one` covers the unknown-action branch via direct handler call (dispatch-level exit-2 semantics preserved). |
| FU-009 | tui-command-unification | Implemented in change `tui-command-unification` slice 1: single command catalog (`CLI_TUI_MAPPING` in `src/ohm/core/commands.py`), parity bijection tests prove no command lost. |
| FU-010 | tui-command-unification | Implemented: single `_dispatch_command` (`src/ohm/cli/app.py:390`) shared by palette and dropdown; both surfaces render the same catalog plus skills appended last. |
| FU-011 | tui-command-unification | Implemented: Ctrl+J wired as `input_newline` (inserts `\n` without confirming), Ctrl+M submits — `_on_key` handling in `src/ohm/cli/input.py:20-32`, tested. |
| FU-012 | tui-command-unification | Implemented: command modal has filter input (`Input#palette-filter`) with live filtering in `src/ohm/cli/widgets/modal_menu.py`. |
| FU-013 | tui-command-unification | Implemented: `_is_open` screen-stack guard — repeat toggle pops, re-open is no-op (single-toggle behavior); tested for F3/settings/quit. |
| FU-014 | tui-command-unification | Implemented: skills commands registered in both palette and `/` dropdown via shared catalog; `test_skills_appended_last_sorted_by_name`. |
| FU-015 | tui-command-unification | Implemented: command and model modals converted to `ModalScreen` (same visual style as session modal) in `src/ohm/cli/widgets/modal_menu.py`. |
| FU-016 | tui-command-unification | Implemented: left/right arrow collapse/expand branch navigation in model modal; `TestBranchNavigation` (5 cases) + keys tests. |
