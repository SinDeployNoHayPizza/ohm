# Tasks: Skills Registry Follow-ups (FU-001..FU-008)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~130 (range 100-180) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | All 8 follow-ups (inspect CLI, abs path, ASCII glyphs, F401 cleanup, regression tests) | PR 1 | `uv run pytest tests/test_skills.py tests/test_cli.py` | `uv run ohm skill inspect python-debugger` → exit 0; `uv run ohm skill inspect bogus` → exit 1 | Revert commit touching skill.py, loader.py, registry.py, tests/test_*.py |

## Phase 1: Loader & Output Foundation

- [x] 1.1 RED — tests/test_skills.py: add `test_discover_skills_path_is_absolute`: chdir(tmp_path), discover via relative search path; assert `skill.path.is_absolute()` and it points at the `SKILL.md` folder
- [x] 1.2 GREEN — loader.py:71: change `path=path.parent` to `path=path.parent.resolve()`
- [x] 1.3 RED — tests/test_cli.py: add `test_skill_list_output_is_ascii_only`: capture list output; assert every char codepoint ≤ 0x7E
- [x] 1.4 GREEN — skill.py:50: replace `•` and `—` glyphs with ASCII `-`

## Phase 2: CLI inspect (FU-001)

- [x] 2.1 RED — tests/test_cli.py: add `test_skill_inspect_displays_skill_details`: fixture skill; `handler(Namespace(skill_action="inspect", name=...))` → exit 0; output shows name, description, absolute path, enabled state, instructions
- [x] 2.2 RED — tests/test_cli.py: add `test_skill_inspect_unknown_returns_one`: unknown name → exit 1 + "Skill not found: bogus"
- [x] 2.3 GREEN — skill.py `register_args`: add `inspect` subparser with positional `name` argument
- [x] 2.4 GREEN — skill.py `handler`: `inspect` branch via `registry.get_skill(name)`; found → print detail block + return 0; missing → print not-found message + return 1

## Phase 3: Regression & Defensive Tests (test-only)

- [x] 3.1 tests/test_skills.py: add `test_discover_skills_priority_override_first_wins` — same name `foo` in `.agents/skills` (desc A) and `.ohm/skills` (desc B) via `DEFAULT_SKILL_SEARCH_PATHS()`; assert A wins (FU-004)
- [x] 3.2 tests/test_skills.py: add `test_parse_skill_file_header_only_falls_back_to_dirname` — no frontmatter → dirname name, `Skill {name}` desc, full text as instructions; headers NOT metadata (FU-007)
- [x] 3.3 tests/test_cli.py: add `test_skill_handler_unknown_action_returns_one` — direct `handler(Namespace(skill_action="unknown"))` → exit 1 + "Unknown skill action" message; exit-2 usage semantics untouched (FU-008)
- [x] 3.4 tests/test_skills.py: rename `test_parse_skill_md_with_yaml_frontmatter` → `test_parse_skill_file_with_yaml_frontmatter` (FU-006)

## Phase 4: Cleanup & Verification (FU-003)

- [x] 4.1 registry.py: remove unused `from typing import Sequence` (line 5)
- [x] 4.2 Remove F401 unused imports: 9 in tests/test_cli.py; `import pytest` in tests/test_skills.py
- [x] 4.3 Verify: `uv run ruff check src/ohm/core/skills/registry.py src/ohm/commands/skill.py tests/test_cli.py tests/test_skills.py` reports 0 F401
- [x] 4.4 Verify: `uv run pytest` full suite green
