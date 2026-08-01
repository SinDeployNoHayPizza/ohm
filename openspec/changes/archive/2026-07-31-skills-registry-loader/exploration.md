# Exploration: Skills Registry & Loader

## Current State

- Skills exist in `.agents/skills/` and `.claude/skills/`, but OHM currently loads tools ad-hoc without formal skill lifecycle management.
- `src/ohm/commands/plugin.py` contains basic plugin listing placeholders.

## Target Architecture

- **`src/ohm/core/skills/`**:
  - `schema.py`: Skill manifest dataclass / Pydantic schema (`SkillManifest`, `ToolConfig`).
  - `loader.py`: `SkillLoader` to scan directories, parse YAML/Markdown metadata, and validate structure.
  - `registry.py`: `SkillRegistry` singleton managing active/inactive skills and providing prompt/tool injection for `Agent`.
- **CLI Commands**:
  - `ohm skill list`
  - `ohm skill install <path_or_url>`
