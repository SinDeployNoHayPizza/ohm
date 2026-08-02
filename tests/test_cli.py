"""Tests for OHM CLI registry and commands."""

import argparse
from pathlib import Path

from ohm.cli.registry import (
    Registry,
    ParsedResult,
    EXIT_SUCCESS,
    EXIT_GENERAL_ERROR,
    EXIT_USAGE_ERROR,
    EXIT_RUNTIME_ERROR,
)


class TestRegistry:
    def test_create_registry(self):
        reg = Registry()
        assert len(reg._subcommands) == 0

    def test_register_subcommand(self):
        reg = Registry()
        reg.register_subcommand(
            name="test",
            help_text="Test command",
            handler=lambda args: 0,
        )
        assert "test" in reg._subcommands

    def test_register_overwrites_duplicate(self):
        reg = Registry()
        reg.register_subcommand(
            name="test",
            help_text="First",
            handler=lambda args: 0,
        )
        reg.register_subcommand(
            name="test",
            help_text="Second",
            handler=lambda args: 1,
        )
        assert reg._subcommands["test"].help_text == "Second"

    def test_parse_registers_command(self):
        reg = Registry()
        reg.register_subcommand(
            name="run",
            help_text="Run something",
            handler=lambda args: 0,
        )
        reg.register_subcommand(
            name="stop",
            help_text="Stop something",
            handler=lambda args: 0,
        )
        result = reg.parse(["run"])
        assert isinstance(result, ParsedResult)
        assert result.namespace.subcommand == "run"

    def test_dispatch_unknown_command(self):
        reg = Registry()
        reg.register_subcommand(
            name="run",
            help_text="Run",
            handler=lambda args: 0,
        )
        result = reg.parse(["nonexistent"])
        exit_code = reg.dispatch(result)
        assert exit_code == EXIT_USAGE_ERROR


class TestExitCodes:
    def test_values(self):
        assert EXIT_SUCCESS == 0
        assert EXIT_GENERAL_ERROR == 1
        assert EXIT_USAGE_ERROR == 2
        assert EXIT_RUNTIME_ERROR == 3


class TestCommands:
    def test_config_command_imports(self):
        from ohm.commands.config import handler
        assert callable(handler)

    def test_status_command_imports(self):
        from ohm.commands.status import handler
        assert callable(handler)

    def test_session_command_imports(self):
        from ohm.commands.session import handler
        assert callable(handler)

    def test_doctor_command_imports(self):
        from ohm.commands.doctor import execute
        assert callable(execute)

    def test_init_command_imports(self):
        from ohm.commands.init import handler
        assert callable(handler)

    def test_run_command_imports(self):
        from ohm.commands.run import handler
        assert callable(handler)

    def test_goal_command_imports(self):
        from ohm.commands.goal import handler
        assert callable(handler)

    def test_session_continue_handler_imports(self):
        from ohm.commands.session import handle_continue
        assert callable(handle_continue)


class TestContinueFlag:
    """Task 3: --continue/-c global flag."""

    def test_continue_flag_registered(self):
        """Global --continue flag parses correctly."""
        reg = Registry()
        reg.register_global(
            "--continue", "-c", dest="continue_",
            action="store_true", default=False,
            help="Resume the last session",
        )
        result = reg.parse(["--continue"])
        assert result.namespace.continue_ is True

    def test_continue_short_flag(self):
        """Short -c flag also sets continue_. """
        reg = Registry()
        reg.register_global(
            "--continue", "-c", dest="continue_",
            action="store_true", default=False,
        )
        result = reg.parse(["-c"])
        assert result.namespace.continue_ is True

    def test_continue_defaults_false(self):
        """No flag means continue_ is False."""
        reg = Registry()
        reg.register_global(
            "--continue", "-c", dest="continue_",
            action="store_true", default=False,
        )
        result = reg.parse([])
        assert result.namespace.continue_ is False


class TestSessionSubcommand:
    """Task 5: session continue sub-action."""

    def test_session_continue_subcommand_registered(self):
        """Verify the session command can route 'continue'."""
        from ohm.commands.session import register, register_args
        reg = Registry()
        register(reg)
        # Build temp parser to check sub-actions
        import argparse
        p = argparse.ArgumentParser(prog="ohm session", add_help=False)
        register_args(p)
        ns = p.parse_args(["continue"])
        assert ns.action == "continue"

    def test_session_handler_returns_int(self):
        """handler() always returns an int exit code."""
        from ohm.commands.session import handler
        import argparse
        ns = argparse.Namespace(action="list", limit=10)
        code = handler(ns)
        assert isinstance(code, int)


class TestSkillCommand:
    """Task 3.2: `ohm skill list` CLI command."""

    def test_skill_command_imports(self):
        """The skill command exposes register() and handler()."""
        from ohm.commands.skill import register, handler
        assert callable(register)
        assert callable(handler)

    def test_skill_command_registered(self):
        """`ohm skill list` parses with subcommand 'skill' and action 'list'."""
        from ohm.commands.skill import register
        reg = Registry()
        register(reg)
        result = reg.parse(["skill", "list"])
        assert result.namespace.subcommand == "skill"
        assert result.namespace.skill_action == "list"

    def test_skill_handler_defaults_to_list(self, tmp_path, monkeypatch, capsys):
        """handler() without a skill_action still lists (default action)."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

        from ohm.commands.skill import handler
        code = handler(argparse.Namespace())
        assert code == 0
        assert "No skills discovered." in capsys.readouterr().out

    def test_skill_list_displays_discovered_skills(self, tmp_path, monkeypatch, capsys):
        """`ohm skill list` prints discovered skills with status and description."""
        skill_dir = tmp_path / ".agents" / "skills" / "skill-a"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: skill-a\ndescription: Skill A description\n---\nBody A",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

        from ohm.commands.skill import handler
        code = handler(argparse.Namespace(skill_action="list"))
        out = capsys.readouterr().out

        assert code == 0
        assert "Discovered Skills (1)" in out
        assert "skill-a" in out
        assert "Skill A description" in out
        assert "(enabled)" in out

    def test_skill_list_empty_reports_no_skills(self, tmp_path, monkeypatch, capsys):
        """`ohm skill list` with no skills prints a message and exits 0."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

        from ohm.commands.skill import handler
        code = handler(argparse.Namespace(skill_action="list"))
        out = capsys.readouterr().out

        assert code == 0
        assert "No skills discovered." in out

    def test_skill_list_multiple_skills_across_paths(self, tmp_path, monkeypatch, capsys):
        """`ohm skill list` aggregates skills from workspace and home paths."""
        local_skill = tmp_path / ".agents" / "skills" / "skill-a"
        local_skill.mkdir(parents=True)
        (local_skill / "SKILL.md").write_text(
            "---\nname: skill-a\ndescription: Skill A description\n---\nBody A",
            encoding="utf-8",
        )
        home_skill = tmp_path / ".ohm" / "skills" / "skill-b"
        home_skill.mkdir(parents=True)
        (home_skill / "SKILL.md").write_text(
            "---\nname: skill-b\ndescription: Skill B description\n---\nBody B",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

        from ohm.commands.skill import handler
        code = handler(argparse.Namespace(skill_action="list"))
        out = capsys.readouterr().out

        assert code == 0
        assert "Discovered Skills (2)" in out
        assert "skill-a" in out
        assert "skill-b" in out
        assert "Skill A description" in out
        assert "Skill B description" in out

    def test_skill_list_output_is_ascii_only(self, tmp_path, monkeypatch, capsys):
        """FU-002: `ohm skill list` output uses only ASCII printable characters."""
        skill_dir = tmp_path / ".agents" / "skills" / "skill-a"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: skill-a\ndescription: Skill A description\n---\nBody A",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

        from ohm.commands.skill import handler
        code = handler(argparse.Namespace(skill_action="list"))
        out = capsys.readouterr().out

        assert code == 0
        assert "skill-a" in out  # listing ran — loop below is not a ghost loop
        assert all(ord(ch) <= 0x7E for ch in out)

    def test_skill_list_shows_disabled_status(self, tmp_path, monkeypatch, capsys):
        """A disabled skill is listed with (disabled) status (skill.py:54 branch)."""
        from ohm.core.skills.schema import Skill

        disabled = Skill(
            name="skill-a",
            description="Skill A description",
            path=tmp_path / "skill-a",
            instructions="Body A",
            enabled=False,
        )
        monkeypatch.setattr(
            "ohm.commands.skill.SkillLoader.discover_skills",
            staticmethod(lambda search_paths: {"skill-a": disabled}),
        )
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

        from ohm.commands.skill import handler
        code = handler(argparse.Namespace(skill_action="list"))
        out = capsys.readouterr().out

        assert code == 0
        assert "Discovered Skills (1)" in out
        assert "(disabled)" in out

    def test_skill_handler_unknown_action_returns_one(self, tmp_path, monkeypatch, capsys):
        """FU-008: direct handler call with unknown action returns 1 (usage exit 2 untouched)."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

        from ohm.commands.skill import handler
        code = handler(argparse.Namespace(skill_action="unknown"))
        out = capsys.readouterr().out

        assert code == 1
        assert "Unknown skill action: unknown" in out


class TestSkillInspectCommand:
    """FU-001: `ohm skill inspect <name>` CLI sub-action."""

    def test_skill_inspect_displays_skill_details(self, tmp_path, monkeypatch, capsys):
        """Inspect prints name, description, absolute path, status, and instructions; exit 0."""
        skill_dir = tmp_path / ".agents" / "skills" / "skill-a"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: skill-a\ndescription: Skill A description\n---\nBody A",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

        from ohm.commands.skill import handler
        code = handler(argparse.Namespace(skill_action="inspect", name="skill-a"))
        out = capsys.readouterr().out

        assert code == 0
        assert "Skill: skill-a" in out
        assert "Status: enabled" in out
        assert "Description: Skill A description" in out
        assert "Path:" in out
        assert str((tmp_path / ".agents" / "skills" / "skill-a").resolve()) in out
        assert "Instructions:" in out
        assert "Body A" in out

    def test_skill_inspect_unknown_returns_one(self, tmp_path, monkeypatch, capsys):
        """Inspect of an unknown skill prints a not-found message and exits 1."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

        from ohm.commands.skill import handler
        code = handler(argparse.Namespace(skill_action="inspect", name="bogus"))
        out = capsys.readouterr().out

        assert code == 1
        assert "Skill not found: bogus" in out


class TestCliTuiParity:
    """R1: every ``register_all`` subcommand maps to exactly one TUI class.

    FU-009: the TUI catalog must never silently lose a CLI surface, and no
    CLI subcommand may map to more than one class.
    """

    @staticmethod
    def _registered_cli_names() -> set[str]:
        from ohm.commands import register_all

        reg = Registry()
        register_all(reg)
        return set(reg._subcommands)

    def test_every_cli_subcommand_maps_to_exactly_one_class(self):
        from ohm.core.commands import CLI_TUI_MAPPING

        cli_names = self._registered_cli_names()
        assert len(cli_names) == 15
        assert cli_names == set(CLI_TUI_MAPPING) - {"--version", "-h"}

    def test_classified_count_equals_registered_count(self):
        from ohm.core.commands import CLI_TUI_MAPPING

        cli_names = self._registered_cli_names()
        # 15 subcommands + the two flag surfaces (--version, -h)
        assert len(CLI_TUI_MAPPING) == len(cli_names) + 2

    def test_none_omitted_all_have_explicit_kind(self):
        from ohm.core.commands import CLI_TUI_MAPPING, CommandKind

        for name, kind in CLI_TUI_MAPPING.items():
            assert isinstance(kind, CommandKind), name
        assert CLI_TUI_MAPPING["--version"] is CommandKind.TUI_IRRELEVANT
        assert CLI_TUI_MAPPING["-h"] is CommandKind.TUI_IRRELEVANT

    def test_real_class_is_exactly_session_skills_skill(self):
        from ohm.core.commands import CLI_TUI_MAPPING, CommandKind

        real = {n for n, k in CLI_TUI_MAPPING.items() if k is CommandKind.REAL}
        assert real == {"session", "skills", "skill"}

    def test_display_only_class_matches_ratified_mapping(self):
        from ohm.core.commands import CLI_TUI_MAPPING, CommandKind

        display = {
            n for n, k in CLI_TUI_MAPPING.items() if k is CommandKind.DISPLAY_ONLY
        }
        assert display == {"config", "test", "run", "status", "goal", "loop"}

    def test_irrelevant_class_is_everything_else(self):
        from ohm.core.commands import CLI_TUI_MAPPING, CommandKind

        irrelevant = {
            n for n, k in CLI_TUI_MAPPING.items() if k is CommandKind.TUI_IRRELEVANT
        }
        assert irrelevant == {
            "doctor", "mcp", "cron", "init", "serve", "plugin",
            "--version", "-h",
        }
