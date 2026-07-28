"""Tests for OHM CLI registry and commands."""

import argparse
import pytest

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
        from ohm.commands.config import register, handler
        assert callable(handler)

    def test_status_command_imports(self):
        from ohm.commands.status import register, handler
        assert callable(handler)

    def test_session_command_imports(self):
        from ohm.commands.session import register, handler
        assert callable(handler)

    def test_doctor_command_imports(self):
        from ohm.commands.doctor import register, execute
        assert callable(execute)

    def test_init_command_imports(self):
        from ohm.commands.init import register, handler
        assert callable(handler)

    def test_run_command_imports(self):
        from ohm.commands.run import register, handler
        assert callable(handler)

    def test_goal_command_imports(self):
        from ohm.commands.goal import register, handler
        assert callable(handler)
