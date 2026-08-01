# Tasks: Skills Registry & Loader

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 250–350 |
| 400-line budget risk | Low |
| Delivery strategy | TDD |

---

## Phase 1: Skill Data Structures & Loader (Strict TDD)

- [x] 1.1 **RED** Write `tests/test_skills.py` testing `SkillLoader.parse_skill_md()` and `discover_skills()`
- [x] 1.2 Implement `Skill` dataclass in `src/ohm/core/skills/schema.py`
- [x] 1.3 Implement `SkillLoader` in `src/ohm/core/skills/loader.py`
- [x] 1.4 **GREEN** Run `uv run pytest tests/test_skills.py`

## Phase 2: Skill Registry & Prompt Integration

- [x] 2.1 **RED** Add tests in `tests/test_skills.py` for `SkillRegistry` (register, enable/disable, build prompt context)
- [x] 2.2 Implement `SkillRegistry` in `src/ohm/core/skills/registry.py`
- [x] 2.3 **GREEN** Run `uv run pytest tests/test_skills.py`

## Phase 3: CLI Command & Integration

- [x] 3.1 Implement `ohm skill` CLI command in `src/ohm/commands/skill.py`
- [x] 3.2 Add tests in `tests/test_cli.py` for `ohm skill list`
- [x] 3.3 **GREEN** Run full `uv run pytest`
