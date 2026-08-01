# Spec: Skills Registry & Loader

## Domain: skills-registry

### Requirements

1. **Skill Discovery**:
   - The loader must discover skills in multiple target directories in priority order:
     1. Local workspace `.agents/skills/<skill-name>/`
     2. Local workspace `.ohm/skills/<skill-name>/`
     3. User home `~/.ohm/skills/<skill-name>/`
     4. System shared `~/.gemini/skills/<skill-name>/`
   - Each skill directory must contain a valid `SKILL.md` frontmatter or header.

2. **Skill Manifest Schema**:
   - `name`: Unique lowercase identifier (e.g. `python-debugger`).
   - `description`: Human-readable summary of what the skill does.
   - `path`: Absolute Path to the skill folder.
   - `instructions`: Full text instructions from `SKILL.md`.

3. **Skill Registry Management**:
   - `SkillRegistry` must maintain active skills, enable/disable skills dynamically, and format prompt context for `Agent`.
