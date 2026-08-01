# Design: Skills Registry & Loader

## Architecture

Create a dedicated module `src/ohm/core/skills/`:
- `schema.py`: `Skill` dataclass (`name`, `description`, `path`, `instructions`, `enabled`).
- `loader.py`: `SkillLoader` with `discover_skills(paths: list[Path]) -> dict[str, Skill]` parsing YAML frontmatter or Markdown headers from `SKILL.md`.
- `registry.py`: `SkillRegistry` with `load_skills()`, `get_skill(name)`, `list_skills()`, and `build_system_prompt_context()`.
- **CLI Subcommand**: `src/ohm/commands/skill.py` for `ohm skill list` and `ohm skill inspect <name>`.
