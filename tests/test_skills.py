"""Tests for Skills Loader and Registry."""

from pathlib import Path
import pytest

from ohm.core.skills.schema import Skill
from ohm.core.skills.loader import SkillLoader
from ohm.core.skills.registry import SkillRegistry


class TestSkillLoader:
    def test_parse_skill_md_with_yaml_frontmatter(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            "---\nname: my-skill\ndescription: Test skill description\n---\n# My Skill\n\nInstructions go here.",
            encoding="utf-8",
        )

        skill = SkillLoader.parse_skill_file(skill_md)
        assert skill is not None
        assert skill.name == "my-skill"
        assert skill.description == "Test skill description"
        assert "Instructions go here." in skill.instructions

    def test_discover_skills_in_directories(self, tmp_path):
        skills_dir = tmp_path / ".agents" / "skills"
        s1 = skills_dir / "skill-a"
        s1.mkdir(parents=True)
        (s1 / "SKILL.md").write_text("---\nname: skill-a\ndescription: Skill A\n---\nBody A", encoding="utf-8")

        s2 = skills_dir / "skill-b"
        s2.mkdir(parents=True)
        (s2 / "SKILL.md").write_text("---\nname: skill-b\ndescription: Skill B\n---\nBody B", encoding="utf-8")

        discovered = SkillLoader.discover_skills([skills_dir])
        assert "skill-a" in discovered
        assert "skill-b" in discovered
        assert discovered["skill-a"].description == "Skill A"


class TestSkillRegistry:
    def test_registry_register_and_get(self):
        registry = SkillRegistry()
        skill = Skill(name="demo", description="Demo Skill", path=Path("/fake"), instructions="Do stuff")
        registry.register(skill)

        assert registry.get_skill("demo") == skill
        assert len(registry.list_skills()) == 1

    def test_build_system_prompt_context(self):
        registry = SkillRegistry()
        skill = Skill(name="demo", description="Demo Skill", path=Path("/fake"), instructions="Do stuff")
        registry.register(skill)

        prompt = registry.build_system_prompt_context()
        assert "Demo Skill" in prompt
        assert "Do stuff" in prompt
