# Proposal: Skills Registry Follow-ups (FU-001..FU-008)

## Intent

Close the eight follow-ups from archived change `skills-registry-loader` (2026-07-31, immutable). Shipped gaps: missing `ohm skill inspect`, console mojibake, 11 unused imports, untested priority/path behavior, and spec wording over-promising header parsing. **FU-005 (user decision, authoritative):** `Skill.path` becomes an ABSOLUTE path — spec-compliant; `ohm skill list` shows absolute paths.

## Scope

### In Scope
- **FU-001**: add `ohm skill inspect <name>` via existing `SkillRegistry.get_skill`; not-found → exit 1. Keep `register()` name (archived `load_skills()` is doc-only drift).
- **FU-002**: replace `•`/`—` glyphs (skill.py:50) with ASCII `-`.
- **FU-003**: remove 11 ruff F401 imports (`registry.py:5`, `tests/test_cli.py`, `tests/test_skills.py`).
- **FU-004**: loader-layer test — same-name skill across search paths, assert first-wins (`discover_skills`, loader.py:90).
- **FU-005**: `Skill.path = path.parent.resolve()`; assert absolute in tests; `list` output reflects it.
- **FU-006**: doc note — `parse_skill_file` is canonical (code, callers, tests); archived `parse_skill_md` immutable.
- **FU-007**: delta spec — align canonical `skills-registry` wording "frontmatter or header" → frontmatter only; header-only files use dir-name fallback.
- **FU-008**: defensive test — direct `handler(Namespace(skill_action="unknown"))` → exit 1; no routing changes.

### Out of Scope
- CLI routing restructure / exit-code semantics 2→1 (FU-008); Markdown-header parsing (FU-007).
- `ohm skill --help` subaction rendering gap; ruff gate in CI; archive edits.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `skills-registry`: ADDED "Skill Inspection" requirement (FU-001: `ohm skill inspect <name>` CLI); MODIFIED "Skill Discovery" wording (FU-007: frontmatter-only + dir-name fallback).

## Approach

Isolated per-FU edits, strict TDD (config `strict_tdd: true`): tests first for inspect, priority override, path absoluteness, unknown-action. FU-001 adds subparser `inspect` (positional `name`) + handler branch via `get_skill`. FU-005 applies `resolve()` in `parse_skill_file` (loader.py:71). FU-007 lands as delta spec `specs/skills-registry/` merged at archive. Assumptions: inspect output matches `list` style; `register()`/`parse_skill_file` stay code-canonical; no ruff gate. Estimated 100-180 changed lines — single PR, far under 400.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/ohm/commands/skill.py` | Modified | `inspect` subcommand; ASCII glyphs |
| `src/ohm/core/skills/loader.py` | Modified | `path.resolve()` (priority logic untouched) |
| `src/ohm/core/skills/registry.py` | Modified | remove unused `Sequence` import |
| `tests/test_cli.py` | Modified | inspect/unknown-action tests; F401 removals |
| `tests/test_skills.py` | Modified | priority-override + path tests; F401 removal |
| `openspec/specs/skills-registry/spec.md` | Modified (archive) | FU-007 wording alignment |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| `resolve()` changes `path` semantics | Low | No consumers rely on relative paths (TUI stores dict only) |
| Inspect output format unconstrained | Low | Keep minimal, match `list` style |
| F401 drift recurs (no ruff gate) | Med | Documented; gate deferred unless user asks |
| Archive dir is `2026-07-31-skills-registry-loader` (orchestrator said 08-01) | n/a | Correct path used; never edited |

## Rollback Plan

`git revert` of the PR merge commit — restores `skill.py`, `loader.py`, `registry.py`, both test files. Delete delta spec `specs/skills-registry/` from change folder (unmerged until archive). No data migration; pure CLI/code behavior.

## Dependencies

None external. Prereq: archived `skills-registry-loader` stays immutable.

## Success Criteria

- [ ] `ohm skill inspect <name>` → details, exit 0; unknown → message, exit 1
- [ ] `ohm skill list` ASCII-clean on legacy-codepage console
- [ ] `uv run ruff check` reports 0 F401
- [ ] Priority-override test passes (first search path wins)
- [ ] Every `Skill.path` absolute (tests + list output)
- [ ] FU-007 delta spec present; full suite green
