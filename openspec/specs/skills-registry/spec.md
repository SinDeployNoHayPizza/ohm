# Skills Registry Specification

> **Status**: IMPLEMENTED & STABLE — synced from change `skills-registry-loader` (archived 2026-07-31). Verify verdict: PASS WITH WARNINGS; post-archive follow-ups tracked in Engram `sdd/skills-registry-loader/archive-report`.

## Purpose

Discover, validate, register, and load declarative skill packages (`SKILL.md`, tool configurations, prompt templates) dynamically into the agent runtime.

## Requirements

### Requirement: Skill Discovery

The loader MUST discover skills in multiple target directories in priority order:

1. Local workspace `.agents/skills/<skill-name>/`
2. Local workspace `.ohm/skills/<skill-name>/`
3. User home `~/.ohm/skills/<skill-name>/`
4. System shared `~/.gemini/skills/<skill-name>/`

Each skill directory MUST contain a valid `SKILL.md` frontmatter or header.

### Requirement: Skill Manifest Schema

- `name`: Unique lowercase identifier (e.g. `python-debugger`).
- `description`: Human-readable summary of what the skill does.
- `path`: Absolute Path to the skill folder.
- `instructions`: Full text instructions from `SKILL.md`.

### Requirement: Skill Registry Management

`SkillRegistry` MUST maintain active skills, enable/disable skills dynamically, and format prompt context for `Agent`.
