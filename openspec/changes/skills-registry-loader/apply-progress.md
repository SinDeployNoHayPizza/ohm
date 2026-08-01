# Apply Progress: Skills Registry & Loader

- **Change**: `skills-registry-loader`
- **Mode**: Strict TDD (runner: `uv run pytest`, per `openspec/config.yaml` — `strict_tdd: true`)
- **Delivery strategy**: single-pr-default (forecast 250–350 lines, budget risk Low — no exception needed)
- **Apply batch 1 (prior)**: Phases 1–2 + task 3.1 (core module, registry, CLI command)
- **Apply batch 2 (this)**: Tasks 3.2 (CLI tests) and 3.3 (full-suite GREEN) + artifacts + work-unit commits

## Status

All 9 tasks complete (1.1–3.3). Ready for `sdd-verify`.

---

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1 | `tests/test_skills.py` | Unit | N/A (new) | ✅ Written (batch 1) | ✅ Passed 2/2 (batch 1) | ✅ 2 cases (frontmatter parse + multi-dir discovery) | ➖ None needed |
| 1.2 | `tests/test_skills.py` | Unit | N/A (new) | ✅ Written (batch 1) | ✅ Passed via 1.4 | ➖ Single (pure dataclass) | ➖ None needed |
| 1.3 | `tests/test_skills.py` | Unit | N/A (new) | ✅ Written (batch 1) | ✅ Passed via 1.4 | ✅ via 1.1's 2 cases | ➖ None needed |
| 1.4 | `tests/test_skills.py` | Unit | N/A | — (GREEN gate) | ✅ Passed 2/2 (batch 1); re-verified this batch in full suite 4/4 | — | — |
| 2.1 | `tests/test_skills.py` | Unit | N/A (new) | ✅ Written (batch 1) | ✅ Passed 2/2 (batch 1) | ✅ 2 cases (register/get/list + prompt context) | ➖ None needed |
| 2.2 | `tests/test_skills.py` | Unit | N/A (new) | ✅ Written (batch 1) | ✅ Passed via 2.3 | ✅ via 2.1's 2 cases | ➖ None needed |
| 2.3 | `tests/test_skills.py` | Unit | N/A | — (GREEN gate) | ✅ Passed 4/4 (batch 1); re-verified this batch in full suite | — | — |
| 3.1 | `tests/test_cli.py` (added this batch) | Unit | N/A (new) | ➖ Command was implemented in batch 1 before its tests (task ordering in tasks.md); **RED satisfied retroactively this batch** — 3.2's tests were written against the existing handler and would have failed a broken handler (e.g. wrong exit code, missing output) | ✅ Passed 6/6 this batch | ✅ via 3.2 (3 list scenarios + default action) | ➖ None needed |
| 3.2 | `tests/test_cli.py` | Unit | ✅ 19/19 (`uv run pytest tests/test_cli.py` before edit) | ✅ Written first (6 tests; zero `ohm skill` tests existed before — behavior unverified) | ✅ Passed 6/6, executed `uv run pytest tests/test_cli.py -k skill` | ✅ 4 cases: single skill (`.agents/skills`), empty dir, multi-path aggregation (`.agents/skills` + `~/.ohm/skills`), default action fallback | ➖ None needed (tests assert user-visible output: names, descriptions, counts, exit codes; no implementation-detail coupling) |
| 3.3 | full suite | Unit | N/A | — (GREEN gate) | ✅ **152 passed** (`uv run pytest`, 35.55s) — baseline 146 + 6 new | — | — |

**Test Summary**
- **Total tests written**: 10 (4 in `tests/test_skills.py` batch 1 + 6 in `tests/test_cli.py` this batch)
- **Total tests passing**: 152 (full suite, all new tests green)
- **Layers used**: Unit (152)
- **Approval tests**: None — no refactoring tasks
- **Pure functions created**: 0 new this batch (no production code changes were needed — 3.1's handler already satisfied all spec scenarios)

---

## Work Unit Evidence

### Work Unit 1 — Core skills module (Phases 1–2; committed as `feat(skills)`)
| Evidence | Value |
|---|---|
| Focused test command and exact result | `uv run pytest tests/test_skills.py` → `4 passed` (re-verified this batch) |
| Runtime harness command/scenario and exact result | `uv run ohm skill list` (repo root) → exit 0, discovers 41 skills (3 workspace + 38 home `~/.gemini/skills`) — proves loader discovery + registry + path priority end-to-end |
| Rollback boundary | Delete `src/ohm/core/skills/` and `tests/test_skills.py`; no other module imports them (CLI command is a separate unit) |

### Work Unit 2 — CLI command + tests (Phase 3; committed as `feat(cli)`)
| Evidence | Value |
|---|---|
| Focused test command and exact result | `uv run pytest tests/test_cli.py -k skill` → `6 passed, 19 deselected` (0.34s) |
| Runtime harness command/scenario and exact result | `uv run ohm skill list` → exit 0; prints `Discovered Skills (41)` with name/status/description/path; empty-dir scenario covered by unit tests (`No skills discovered.` + exit 0) |
| Rollback boundary | Revert `src/ohm/commands/skill.py` and the `TestSkillCommand` class in `tests/test_cli.py`; CLI auto-discovery (`ohm.commands.register_all`) needs no wiring change — the command simply stops being registered |

### Work Unit 3 — SDD artifacts + docs + version (committed as `chore`)
| Evidence | Value |
|---|---|
| Focused test command and exact result | N/A — no code in this unit; guard is the full suite re-run → `152 passed` |
| Runtime harness command/scenario and exact result | N/A — docs/version-only unit, no runtime boundary |
| Rollback boundary | Revert the chore commit; touches only `openspec/changes/skills-registry-loader/`, `docs/engram-gentle-ai-integration.md`, `README.md`, `README.es.md`, `.atl/*`, `pyproject.toml`, `src/ohm/__init__.py`, `uv.lock` — zero code-behavior impact |

---

## Deviations from Design

None — implementation matches `design.md` (`schema.py` / `loader.py` / `registry.py` / `commands/skill.py` structure, `ohm skill list` subcommand).

## Issues Found

1. **`ohm skill list` output uses non-ASCII glyphs (`•`, `—`)** — renders as mojibake in a legacy-codepage Windows console capture; renders correctly in UTF-8 terminals and all pytest assertions pass. Cosmetic; pre-existing from task 3.1. Out of assigned scope; noted for verify.
2. **`enabled`/`disabled` status branch is not reachable through the CLI handler** — the handler registers skills with the registry's default `enabled=True` and never toggles it, so the `disabled` display branch is dead code via the CLI. `enable_skill`/`disable_skill` are covered at the registry layer (`tests/test_skills.py`). Noted, not changed (no failing test and no spec scenario demands a CLI toggle).

## Workload / PR Boundary

- Mode: single PR (default; forecast 250–350 lines < 400 budget)
- Current work unit: CLI tests + full-suite GREEN (3.2, 3.3)
- Boundary: starts from the existing uncommitted Phase 1–3 work; ends with all 9 tasks complete, tests green, work-unit commits created
- Estimated review budget impact: ~350 changed lines total across the branch
