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

    def test_registry_enable_skill(self):
        registry = SkillRegistry()
        skill = Skill(name="demo", description="Demo Skill", path=Path("/fake"), instructions="Do stuff")
        registry.register(skill)
        registry.disable_skill("demo")
        assert skill.enabled is False  # precondition: skill is disabled

        assert registry.enable_skill("demo") is True
        assert skill.enabled is True

    def test_registry_enable_skill_unknown_name_returns_false(self):
        registry = SkillRegistry()

        assert registry.enable_skill("missing") is False

    def test_registry_disable_skill(self):
        registry = SkillRegistry()
        skill = Skill(name="demo", description="Demo Skill", path=Path("/fake"), instructions="Do stuff")
        registry.register(skill)
        assert skill.enabled is True  # precondition: default is enabled

        assert registry.disable_skill("demo") is True
        assert skill.enabled is False

    def test_registry_disable_skill_unknown_name_returns_false(self):
        registry = SkillRegistry()

        assert registry.disable_skill("missing") is False

    def test_build_system_prompt_context_excludes_disabled_skills(self):
        registry = SkillRegistry()
        active = Skill(name="active", description="Active Skill", path=Path("/a"), instructions="Active body")
        dormant = Skill(name="dormant", description="Dormant Skill", path=Path("/d"), instructions="Dormant body")
        registry.register(active)
        registry.register(dormant)
        registry.disable_skill("dormant")

        prompt = registry.build_system_prompt_context()
        assert "Active Skill" in prompt
        assert "Active body" in prompt
        assert "dormant" not in prompt
        assert "Dormant Skill" not in prompt
        assert "Dormant body" not in prompt

    def test_build_system_prompt_context_empty_when_all_disabled(self):
        registry = SkillRegistry()
        skill = Skill(name="solo", description="Solo Skill", path=Path("/s"), instructions="Solo body")
        registry.register(skill)
        registry.disable_skill("solo")

        assert registry.build_system_prompt_context() == ""
