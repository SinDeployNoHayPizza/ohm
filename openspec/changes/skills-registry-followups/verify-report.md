```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:55882d3dd1060cf010c6b0e24db4a0a4d2fdf36a1fa9878b30154916e11b3760
verdict: pass_with_warnings
blockers: 0
critical_findings: 0
requirements: 8/8
scenarios: 10/10
test_command: uv run pytest tests/ -q --junitxml=C:\Users\Admin\AppData\Local\Temp\opencode\ohm-followups-rem-ed-evidence.xml
test_exit_code: 0
test_output_hash: sha256:55882d3dd1060cf010c6b0e24db4a0a4d2fdf36a1fa9878b30154916e11b3760
build_command: uv run python -m compileall src
build_exit_code: 0
build_output_hash: sha256:F100D952CEC2169A8273762B502679F2BC9177D48EECB72082455179FE230500
```

## Verification Report

**Change**: skills-registry-followups (FU-001..FU-008)
**Version**: N/A (delta spec, no version field)
**Mode**: Strict TDD (per `openspec/config.yaml` — `strict_tdd: true`, runner `uv run pytest`; strict-tdd-verify.md loaded)
**Branch**: feature/skills-registry-followups @ HEAD `664642e` (working tree clean at verification start; verification made zero code edits)
**Spec**: `specs/skills-registry/spec.md` — 7 ADDED + 1 MODIFIED requirements, 10 formal scenarios
**Review gate**: orchestrator-declared "Review authority approved (lineage `review-8fdea294d6214fc0`, post-apply gate allow, bound)". NOTE: no native review artifacts exist in either store for this change (no `openspec/changes/skills-registry-followups/reviews/*.json`, no Engram `sdd/skills-registry-followups/review/*` topics); review approval is taken from the orchestrator launch context only.

### Completeness
| Metric | Value |
|--------|-------|
| Tasks total | 16 (tasks.md 1.1–4.4) |
| Tasks complete | 16 (all `[x]`; grep `- [x]` = 16, `- [ ]` = 0) |
| Tasks incomplete | 0 |

> Note: apply-progress prose says "14/14", but its own TDD Cycle Evidence table lists all 16 task rows and tasks.md has 16 checked boxes — a counting label mismatch in prose only, no evidence gap.

### Build & Tests Execution
**Build**: ✅ Passed — `uv run python -m compileall src` → exit 0 (SHA-256 `F100D9…30500`). No packaging build tool configured; compileall is the build-equivalent check (same convention as the archived verify-report).

**Tests**: ✅ **212 passed / 0 failed / 0 skipped** — `uv run pytest tests/ -q --junitxml=C:\Users\Admin\AppData\Local\Temp\opencode\ohm-followups-rem-ed-evidence.xml`, exit 0 (SHA-256 `55882D…3760`). JUnit parse: `tests=212 failures=0 errors=0 skipped=0`. Exactly matches apply-progress claim "212 passed (205 baseline + 7 new)". All 7 new tests + 1 renamed test confirmed present in the JUnit evidence and passing:
`test_skill_inspect_displays_skill_details`, `test_skill_inspect_unknown_returns_one`, `test_skill_handler_unknown_action_returns_one`, `test_skill_list_output_is_ascii_only`, `test_discover_skills_path_is_absolute`, `test_discover_skills_priority_override_first_wins`, `test_parse_skill_file_header_only_falls_back_to_dirname`, `test_parse_skill_file_with_yaml_frontmatter` (renamed, FU-006).

**Runtime harness (end-to-end CLI proof)**:
| Command | Exit | Evidence |
|---------|------|----------|
| `uv run ohm skill inspect library-skills` | **0** | Full detail block: `Skill: library-skills`, `Status: enabled`, `Description: …`, `Path: D:\2026\python\ohm\.agents\skills\library-skills` (absolute), `Instructions:` + body. Hash `F91DE9…F22C` |
| `uv run ohm skill inspect bogus` | **1** | `Skill not found: bogus` on stdout. Hash `57438C…27E8` |
| `uv run ohm skill list` | **0** | `Discovered Skills (41):`; 41/41 `Path:` lines absolute (`relativeOrNoDrive=0`); framing glyphs ASCII (`-`, no `•`/`—`); raw file bytes begin clean `44 69 73 63 6F…` ("Discovered Skills"). Hash `95252E…E910` |

**Priority override live proof**: `library-skills` resolves from `.agents\skills\library-skills` (workspace copy wins over `~/.gemini/skills`); `building-pydantic-ai-agents` shows its first-wins source with `path.parent.resolve()` following the Library-Skills managed symlink to `.venv\Lib\site-packages\pydantic_ai\.agents\skills\…` — resolve() symlink normalization is documented design D2 behavior, path remains absolute and points at the folder containing `SKILL.md`.

**Coverage**: ➖ Not available (`config.yaml` → `coverage_available: false`; no `pytest-cov`). Skipped per strict-tdd module — informational, not a failure.

### Spec Compliance Matrix
| Requirement | Scenario | Test / Proof | Result |
|-------------|----------|--------------|--------|
| R1 (ADDED) Skill Inspection | Inspect a known skill | `tests/test_cli.py::TestSkillInspectCommand::test_skill_inspect_displays_skill_details` + harness `inspect library-skills` → 0 | ✅ COMPLIANT |
| R1 (ADDED) Skill Inspection | Inspect an unknown skill | `tests/test_cli.py::TestSkillInspectCommand::test_skill_inspect_unknown_returns_one` + harness `inspect bogus` → 1 | ✅ COMPLIANT |
| R2 (ADDED) ASCII-Safe Skill Output | List output is ASCII-only | `tests/test_cli.py::TestSkillCommand::test_skill_list_output_is_ascii_only` (ASCII fixture, non-empty guard + codepoint ≤ 0x7E scan) | ✅ COMPLIANT (see W-2 for real-world boundary) |
| R3 (ADDED) Priority Override | Same-name skill across search paths | `tests/test_skills.py::TestSkillLoader::test_discover_skills_priority_override_first_wins` (.agents desc A wins over .ohm desc B) + live harness | ✅ COMPLIANT |
| R4 (ADDED) Absolute Skill Path | Discovered skill path is absolute | `tests/test_skills.py::TestSkillLoader::test_discover_skills_path_is_absolute` (relative search dir → `is_absolute()`, exact resolved path, `SKILL.md` present) + harness 41/41 absolute | ✅ COMPLIANT |
| R5 (ADDED) Skill Parsing Entry Point | Canonical parse name is used | `rg "parse_skill_md" src/ohm tests/` → **ZERO matches**; `parse_skill_file` used in loader.py:38/89, test_skills.py:44/75/113 | ✅ COMPLIANT |
| R6 (ADDED) Defensive Unknown Skill Action | Handler called with unknown action | `tests/test_cli.py::TestSkillCommand::test_skill_handler_unknown_action_returns_one` — direct `handler(Namespace(skill_action="unknown"))` → 1 + message | ✅ COMPLIANT |
| R7 (ADDED) Clean Imports | Ruff reports no unused imports | `uv run ruff check src/ohm/core/skills/registry.py src/ohm/core/skills/loader.py src/ohm/commands/skill.py tests/test_cli.py tests/test_skills.py` → **"All checks passed!" exit 0** (see W-1 for full-project scope) | ✅ COMPLIANT |
| R8 (MODIFIED) Skill Discovery | Frontmatter skill discovery | `test_parse_skill_file_with_yaml_frontmatter` + `test_discover_skills_in_directories` (frontmatter name/description/instructions; 4-path order verified loader.py:16-26) | ✅ COMPLIANT |
| R8 (MODIFIED) Skill Discovery | Header-only SKILL.md fallback | `tests/test_skills.py::TestSkillLoader::test_parse_skill_file_header_only_falls_back_to_dirname` (dirname name, `Skill {name}` desc, `metadata == {}` — headers NOT metadata, full text as instructions) | ✅ COMPLIANT |

**Compliance summary**: **10/10 scenarios compliant**; **8/8 requirements fully proven**.

### Correctness (Static Evidence)
| Requirement | Status | Notes |
|------------|--------|-------|
| R1 Skill Inspection | ✅ Implemented | `register_args` adds `inspect` subparser + positional `name` (skill.py:28-30); `handler` branch via `registry.get_skill` — found → detail block + 0, missing → `Skill not found: {name}` + 1 (skill.py:58-71). Sub-action: `CLI_TUI_MAPPING`/15-subcommand parity untouched (TestCliTuiParity 6/6 pass) |
| R2 ASCII-Safe Output | ✅ Implemented | skill.py:54 `•`→`-`; no non-ASCII in changed production output paths (grep `[^\x00-\x7F]` on skill.py: zero; only hit is a docstring comment in loader.py:30, not output) |
| R3 Priority Override | ✅ Implemented (pre-existing, now proven) | loader.py:90 `if skill and skill.name not in skills` over priority-ordered paths — first-wins by construction; regression test added |
| R4 Absolute Skill Path | ✅ Implemented | loader.py:71 `path=path.parent.resolve()`; invariant absolute; sole src consumer skill.py:55 prints it |
| R5 Canonical parse name | ✅ Implemented | `parse_skill_file` canonical in code/callers/tests; `parse_skill_md` zero references in src+tests |
| R6 Unknown-action exit 1 | ✅ Implemented (pre-existing, now proven) | skill.py:73-74 `print` + `return 1`; test proves the branch (dispatch-level usage-exit 2 untouched) |
| R7 Clean Imports | ✅ Implemented | registry.py:5 `Sequence` import removed; 9 F401 dropped from test_cli.py, `pytest` dropped from test_skills.py; scoped ruff exit 0 |
| R8 Frontmatter-only discovery | ✅ Implemented (code matched delta wording) | loader.py:49-66 — no frontmatter → dirname/generic desc/full text; headers never parsed as metadata; regression test added |

### Coherence (Design)
| Decision | Followed? | Notes |
|----------|-----------|-------|
| D1 `inspect` subparser + handler branch via `get_skill` | ✅ Yes | skill.py:28-30, 58-71; detail block field order matches D1 exactly (Skill/Status/Description/Path/Instructions) |
| D2 Absolute `Skill.path` via `resolve()` | ✅ Yes | loader.py:71; symlink normalization observed live (venv managed-symlink target shown) — documented D2 behavior |
| D3 ASCII glyph replacement (`•`/`—` → `-`) | ✅ Yes (framing) | skill.py:54; user-authored text NOT sanitized per D3 boundary — W-2 |
| D4 Priority override first-wins — test-only | ✅ Yes | loader unchanged; `test_discover_skills_priority_override_first_wins` added |
| D5 `parse_skill_file` canonical naming | ✅ Yes | method renamed `test_parse_skill_file_with_yaml_frontmatter`; zero `parse_skill_md` refs in src+tests |
| D6 Unknown-action direct-invocation test | ✅ Yes | `test_skill_handler_unknown_action_returns_one`; exit semantics 2=usage / 1=general untouched |
| D7 Header-only fallback — spec delta + test | ✅ Yes | `test_parse_skill_file_header_only_falls_back_to_dirname`; delta spec wording matches code |

### TDD Compliance
| Check | Result | Details |
|-------|--------|---------|
| TDD Evidence reported | ✅ | "TDD Cycle Evidence" table present in apply-progress (Engram #242), all 16 task rows |
| All tasks have tests | ✅ | 16/16 tasks reference existing test files (4.1-4.3 are lint tasks — reference ruff gate) |
| RED confirmed (tests exist) | ✅ | All 7 new test methods verified on disk in tests/test_cli.py + tests/test_skills.py, and present in fresh JUnit XML |
| GREEN confirmed (tests pass) | ✅ | 212/212 full suite pass on fresh execution; focused 51/51 (44 baseline + 7 new) arithmetic consistent |
| Triangulation adequate | ✅ | 1.1 (3 asserts), 2.1 (7 asserts), 2.4 (found+not-found pair), 3.1 (fixture + real-world duplicate), 3.3 (exit-1 vs dispatch exit-2), 1.3 (non-empty guard + codepoint scan); only 3.4 (rename) and lint rows are single-case — appropriate |
| Safety Net for modified files | ✅ | 12/12 (test_skills.py) and 32/32 (test_cli.py) pre-edit baselines documented; consistent with 44 baseline focused files |
| TDD ordering | ✅ | RED steps documented with concrete pre-fix failures (path-not-absolute, U+2022/U+2014 > 0x7E, inspect fell to unknown-action, wrong message); 3.1/3.2/3.3 honestly labeled regression (code already correct) |

**TDD Compliance**: 7/7 checks passed

---

### Test Layer Distribution
| Layer | Tests | Files | Tools |
|-------|-------|-------|-------|
| Unit | 212 (7 new + 1 renamed in this change) | 13 files (2 changed) | pytest |
| Integration | 0 | 0 | not installed |
| E2E | 0 | 0 | not installed |
| **Total** | **212** | **13** | |

Layer cross-reference: config.yaml declares `unit: pytest`, `integration: false`, `e2e: false`; no render/screen/playwright patterns in the suite — consistent with capabilities. The 7 new tests are all unit-level (direct handler/loader calls with capsys/tmp_path) — appropriate for CLI/loader logic per strict module (SUGGESTION only if integration tools existed; they don't).

---

### Changed File Coverage
**Coverage analysis skipped — no coverage tool detected** (`config.yaml` → `coverage_available: false`; no `pytest-cov`). Not a failure per strict-tdd module.

---

### Assertion Quality
**Assertion quality**: ✅ All assertions verify real behavior. All 7 new + 1 renamed tests audited (Step 5f):
- Every test calls production code (`SkillLoader.parse_skill_file` / `discover_skills`, `skill.handler` with real discovery + real registry).
- No tautologies, no type-only-alone assertions, no implementation-detail coupling, no ghost loops. `test_skill_list_output_is_ascii_only` carries an explicit non-empty guard (`assert "skill-a" in out`) before its codepoint scan, with a code comment naming the ghost-loop trap.
- Empty-check `assert skill.metadata == {}` in the header-only test is accompanied by 3 value assertions in the same test (name, description, exact instructions text) — not an orphan empty check.
- Mock ratio fine: only `monkeypatch.chdir` + `Path.home` environment stubs (setup, not behavior mocking); `test_skill_list_shows_disabled_status` (pre-existing) uses 1 discovery stub vs 3 behavior assertions.
- Triangulation has variance: exit-0 vs exit-1, known vs unknown, absolute-path equality, first-wins desc A vs desc B, frontmatter vs header-only.

---

### Quality Metrics
**Linter**: ⚠️ Scoped to the five change-touched files: `uv run ruff check` → **"All checks passed!" exit 0** (zero F401 — FU-003 satisfied for skill sources + tests). Full-project `uv run ruff check src/ohm tests` → exit 1 with **59 pre-existing errors** (35 F401, 16 F541, 3 F841, 2 F821, 1 E402, 1 E713, 1 F811) — **all in files untouched by this change** (app.py, chat.py, status.py, test_session.py, test_config.py, test_agent.py, etc.). None of the 59 are in the five change files. Ruff is not configured as the project gate in `pyproject.toml`/`config.yaml`; reported as WARNING (informational per strict module).
**Type Checker**: ➖ Not configured (`config.yaml` → `type_checker: ""`).

### Issues Found

**CRITICAL** — NONE.

**WARNING**
1. **Full-project `uv run ruff check src/ohm tests` exits 1** (59 errors: 35 F401 + 24 others) in files outside this change's scope (TUI widgets, other commands, unrelated test files). FU-003's GIVEN clause ("the skill sources and their tests") is satisfied — scoped run on the five change files is clean, exit 0, and none of the 59 full-project hits touch them. Pre-existing debt, not introduced by this change (archived verify already noted 11 pre-existing F401; this change removed exactly those 11 from its five files). If a whole-repo ruff gate is ever enforced, it will fail today.
2. **Real-world `ohm skill list` output can still carry non-ASCII from user-authored description text** (D3 documented boundary): live harness capture shows exactly 1 codepoint > 0x7E — an em-dash (U+2014, verified in the source `pydantic_ai` bundled SKILL.md description; renders as mojibake `�` on this legacy-codepage console). Framing glyphs and all 41 `Path:` lines are ASCII-clean; the spec scenario is fixture-defined and passes. The literal scenario wording ("every character's code point ≤ 0x7E" for "a discovered skill") is not met for skills whose authored description contains non-ASCII. Recommend either sanitizing user-authored text or explicitly scoping the spec wording — spec/design boundary tension, not a defect in the shipped fix.

**SUGGESTION**
3. apply-progress prose says "14/14 tasks complete" while tasks.md has 16 checked boxes and the TDD table lists 16 rows — update the summary count label for consistency at archive.
4. `path.parent.resolve()` follows managed symlinks (observed: `building-pydantic-ai-agents` displays its venv target rather than the `.agents/skills` symlink). Behavior is documented D2 and spec-compliant (absolute, contains SKILL.md), but users may find the resolved target surprising; a `--no-follow` option or doc note could clarify.
5. Loader.py:30 docstring contains an em-dash (comment only, never CLI output) — harmless, but a UTF-8-passim cleanup would keep the whole changed-file tree pure-ASCII if desired.

### Verdict
**PASS WITH WARNINGS** — all 10/10 spec scenarios COMPLIANT with fresh runtime evidence, 8/8 requirements proven, **212/212 tests pass** (exit 0, SHA-256 `55882D…3760`), build-equivalent `compileall` exit 0, scoped ruff zero-F401, and all three CLI runtime-harness checks prove end-to-end behavior (`inspect` known → 0, unknown → 1, `list` → 41 absolute-path ASCII-framing entries). Strict TDD evidence validated: 16/16 rows, RED confirmed on disk, GREEN confirmed by fresh execution, assertion quality clean. Two WARNINGs — pre-existing full-project ruff debt outside the change's five files, and the documented D3 boundary (user-authored description text not sanitized, 1 non-ASCII em-dash observed from a third-party skill) — neither blocks archive. No code was modified by this verification. Next phase: **sdd-archive**.
