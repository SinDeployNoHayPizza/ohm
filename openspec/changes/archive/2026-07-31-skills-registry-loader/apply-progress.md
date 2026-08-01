# Apply Progress: Skills Registry & Loader

- **Change**: `skills-registry-loader`
- **Mode**: Strict TDD (runner: `uv run pytest`, per `openspec/config.yaml` — `strict_tdd: true`)
- **Delivery strategy**: single-pr-default (forecast 250–350 lines, budget risk Low — no exception needed)
- **Apply batch 1 (prior)**: Phases 1–2 + task 3.1 (core module, registry, CLI command)
- **Apply batch 2 (prior)**: Tasks 3.2 (CLI tests) and 3.3 (full-suite GREEN) + artifacts + work-unit commits
- **Apply batch 3 — REMEDIATION (this)**: verify CRITICAL 1 & 2 — registry-layer `enable_skill`/`disable_skill` + `enabled`-filtered prompt-context tests, CLI `(disabled)` display-branch test, and corrected evidence artifact

## Status

All 10 tasks complete (1.1–3.3). Remediation batch 3 applied: verify CRITICAL 1 (REQ-3 enable/disable untested) and CRITICAL 2 (false coverage claim) resolved — see Issues. Ready for re-verify.

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
| R1 (batch 3 — REMED) | `tests/test_skills.py` | Unit | ✅ 4/4 (`uv run pytest tests/test_skills.py` pre-edit) | ✅ Written first — tests were the only change before execution (zero production edits); executed → **passed on first run** (10/10): existing registry implementation already satisfied the new behavior tests — approval-style confirmation of previously-unproven behavior; **no defect surfaced, so no production change was required** | ✅ Passed 10/10 (`uv run pytest tests/test_skills.py`, 0.15s) | ✅ 6 cases: enable happy + missing-name, disable happy + missing-name, disabled skill excluded from prompt context, all-disabled → empty string | ➖ None needed (no production change) |
| R2 (batch 3 — REMED) | `tests/test_cli.py` | Unit | ✅ 25/25 (`uv run pytest tests/test_cli.py` pre-edit) | ✅ Written first — executed → passed on first run; `skill.py:54` `(disabled)` display branch already correct | ✅ Passed 7/7, executed `uv run pytest tests/test_cli.py -k skill` (0.23s) | ✅ pair: `(enabled)` asserted in existing test + `(disabled)` asserted in new `test_skill_list_shows_disabled_status` | ➖ None needed (no production change) |
| R3 (batch 3 — REMED) | full suite | Unit | ✅ 152 baseline (batch 2) | — (GREEN gate) | ✅ **159 passed** (`uv run pytest`, 28.54s) — 152 baseline + 7 new (6 registry + 1 CLI) | — | — |

**Test Summary**
- **Total tests written**: 17 (4 in `tests/test_skills.py` batch 1 + 6 in `tests/test_cli.py` batch 2 + 7 in batch 3 remediation)
- **Total tests passing**: 159 (full suite, all new tests green)
- **Layers used**: Unit (159)
- **Approval tests**: 7 (batch 3 remediation tests confirm existing-but-unproven enable/disable/prompt-filter/CLI-status behavior — they passed on first execution without production changes)
- **Pure functions created**: 0 (no production code changes were needed in any batch — batch 3's gap was test coverage, not code behavior)

---

## Work Unit Evidence

### Work Unit 1 — Core skills module (Phases 1–2; committed as `feat(skills)`)
| Evidence | Value |
|---|---|
| Focused test command and exact result | `uv run pytest tests/test_skills.py` → `10 passed` (4 original + 6 remediation; re-verified batch 3) |
| Runtime harness command/scenario and exact result | `uv run ohm skill list` (repo root) → exit 0, discovers 41 skills (3 workspace + 38 home `~/.gemini/skills`) — proves loader discovery + registry + path priority end-to-end |
| Rollback boundary | Delete `src/ohm/core/skills/` and `tests/test_skills.py`; no other module imports them (CLI command is a separate unit) |

### Work Unit 2 — CLI command + tests (Phase 3; committed as `feat(cli)`)
| Evidence | Value |
|---|---|
| Focused test command and exact result | `uv run pytest tests/test_cli.py -k skill` → `7 passed, 19 deselected` (6 batch 2 + 1 remediation) |
| Runtime harness command/scenario and exact result | `uv run ohm skill list` → exit 0; prints `Discovered Skills (41)` with name/status/description/path; empty-dir scenario covered by unit tests (`No skills discovered.` + exit 0) |
| Rollback boundary | Revert `src/ohm/commands/skill.py` and the `TestSkillCommand` class in `tests/test_cli.py`; CLI auto-discovery (`ohm.commands.register_all`) needs no wiring change — the command simply stops being registered |

### Work Unit 3 — SDD artifacts + docs + version (committed as `chore`)
| Evidence | Value |
|---|---|
| Focused test command and exact result | N/A — no code in this unit; guard is the full suite re-run → `152 passed` |
| Runtime harness command/scenario and exact result | N/A — docs/version-only unit, no runtime boundary |
| Rollback boundary | Revert the chore commit; touches only `openspec/changes/skills-registry-loader/`, `docs/engram-gentle-ai-integration.md`, `README.md`, `README.es.md`, `.atl/*`, `pyproject.toml`, `src/ohm/__init__.py`, `uv.lock` — zero code-behavior impact |

### Work Unit 4 — REMEDIATION: enable/disable registry + CLI status coverage (batch 3; verify CRITICAL 1 & 2)
| Evidence | Value |
|---|---|
| Focused test command and exact result | `uv run pytest tests/test_skills.py` → `10 passed` (0.15s); `uv run pytest tests/test_cli.py -k skill` → `7 passed, 19 deselected` (0.23s) |
| Runtime harness command/scenario and exact result | `uv run ohm skill list` → exit 0, `Discovered Skills (41)` — unchanged behavior confirmed; the `(disabled)` display branch is proven by unit test `test_skill_list_shows_disabled_status` (real handler + real registry, stubbed discovery source) |
| Rollback boundary | Revert `tests/test_skills.py` (6 new registry tests), `tests/test_cli.py` (`test_skill_list_shows_disabled_status`), and the `apply-progress.md` corrections — **zero production code was touched by this work unit** |

---

## Deviations from Design

Corrected in batch 3 (verify WARNING 4 — the previous "None" claim was inaccurate). Documented deltas:

1. **`ohm skill inspect <name>` (design.md:9) is NOT implemented** — only `ohm skill list` exists. Not a spec violation (spec.md names no CLI subcommand) and tasks.md never scoped `inspect`; the design element was truncated from scope. Deliberately left unimplemented in this remediation (non-trivial: new subcommand + args + output + tests); a follow-up change or a design update should reconcile it.
2. **`load_skills()` (design.md:8) implemented as `register()`** — cosmetic rename; loading responsibility moved into CLI handler wiring (`commands/skill.py:41-44`). Behavior matches design intent.
3. `SkillLoader.parse_skill_md()` (tasks.md 1.1) is implemented as `parse_skill_file()` — naming drift, docs vs code (verify SUGGESTION 9).

## Issues Found

1. **`ohm skill list` output uses non-ASCII glyphs (`•`, `—`)** — renders as mojibake in a legacy-codepage Windows console capture; renders correctly in UTF-8 terminals and all pytest assertions pass. Cosmetic; pre-existing from task 3.1. Out of assigned scope; confirmed live by verify report.
2. **REMEDIATED (verify CRITICAL 1) — REQ-3 enable/disable was UNTESTED**: `enable_skill`/`disable_skill` and the `enabled`-filtered prompt-context path now have passing runtime tests — 6 new in `tests/test_skills.py` (enable happy + missing-name → False, disable happy + missing-name → False, disabled skill excluded from prompt context, all-disabled → empty string) plus 1 new CLI test proving the `(disabled)` display branch in `commands/skill.py:54` (`test_skill_list_shows_disabled_status` in `tests/test_cli.py`). **Retraction**: the batch-2 claim that enable/disable "are covered at the registry layer (`tests/test_skills.py`)" was FALSE — the test file contained no such test; this remediation replaces that statement with real coverage. No production change was needed: the existing implementation satisfied all 7 new tests on first execution (approval-style confirmation), proving the gap was test coverage, not code behavior.

## Workload / PR Boundary

- Mode: single PR (default; forecast 250–350 lines < 400 budget)
- Current work unit: REMEDIATION batch 3 (enable/disable registry + CLI status coverage, corrected evidence)
- Boundary: starts from HEAD 8a54bb5 (all 10 tasks complete, 152 passing); ends with remediation committed, full suite 159 passing
- Estimated review budget impact: ~360 changed lines total across the branch (remediation adds ~140 lines: 6 registry tests + 1 CLI test + apply-progress corrections)
