"""Registry for managing active skills and injecting prompt context."""

from __future__ import annotations

from ohm.core.skills.schema import Skill


class SkillRegistry:
    """Manages active skills and formats skill instructions for agent execution."""

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        """Register a skill in the registry."""
        self._skills[skill.name] = skill

    def get_skill(self, name: str) -> Skill | None:
        """Get a skill by name."""
        return self._skills.get(name)

    def list_skills(self) -> list[Skill]:
        """Return a list of all registered skills."""
        return list(self._skills.values())

    def enable_skill(self, name: str) -> bool:
        """Enable a skill."""
        skill = self.get_skill(name)
        if skill:
            skill.enabled = True
            return True
        return False

    def disable_skill(self, name: str) -> bool:
        """Disable a skill."""
        skill = self.get_skill(name)
        if skill:
            skill.enabled = False
            return True
        return False

    def build_system_prompt_context(self) -> str:
        """Build formatted Markdown system prompt section for active enabled skills."""
        enabled_skills = [s for s in self._skills.values() if s.enabled]
        if not enabled_skills:
            return ""

        sections = ["## Active Skills\n"]
        for skill in enabled_skills:
            sections.append(f"### {skill.name}: {skill.description}\n{skill.instructions}\n")

        return "\n".join(sections)
