"""Loader for discovering and parsing SKILL.md packages."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

import yaml

from ohm.core.skills.schema import Skill

logger = logging.getLogger(__name__)


def default_skill_search_paths() -> list[Path]:
    """Default skill search locations (project-local first, then user-global).

    Evaluated per call so tests can patch ``Path.home()`` and/or ``chdir``.
    """
    return [
        Path(".agents/skills"),
        Path(".ohm/skills"),
        Path.home() / ".ohm" / "skills",
        Path.home() / ".gemini" / "skills",
    ]


# DD-08: single source shared by the TUI (``OhmApp.on_mount``) and the CLI
# ``skill`` command.  Callable on purpose — resolves paths per call.
DEFAULT_SKILL_SEARCH_PATHS = default_skill_search_paths


class SkillLoader:
    """Parses SKILL.md files and discovers skill packages across directories."""

    @classmethod
    def parse_skill_file(cls, path: Path) -> Skill | None:
        """Parse a single SKILL.md file into a Skill object."""
        if not path.is_file():
            return None

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.warning("Failed to read skill file %s: %s", path, exc)
            return None

        name = path.parent.name
        description = f"Skill {name}"
        instructions = content
        metadata: dict = {}

        # Parse YAML frontmatter if present
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                raw_yaml = parts[1]
                instructions = parts[2].strip()
                try:
                    metadata = yaml.safe_load(raw_yaml) or {}
                    if isinstance(metadata, dict):
                        name = metadata.get("name", name)
                        description = metadata.get("description", description)
                except Exception as exc:
                    logger.warning("Failed to parse YAML frontmatter in %s: %s", path, exc)

        return Skill(
            name=name,
            description=description,
            path=path.parent,
            instructions=instructions,
            metadata=metadata,
        )

    @classmethod
    def discover_skills(cls, search_paths: Sequence[Path]) -> dict[str, Skill]:
        """Discover skills in search directories (highest priority first)."""
        skills: dict[str, Skill] = {}

        for search_dir in search_paths:
            if not search_dir.is_dir():
                continue

            for item in search_dir.iterdir():
                if item.is_dir():
                    skill_md = item / "SKILL.md"
                    if skill_md.is_file():
                        skill = cls.parse_skill_file(skill_md)
                        if skill and skill.name not in skills:
                            skills[skill.name] = skill

        return skills
