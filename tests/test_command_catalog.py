"""Unit tests for the TUI command catalog builder (R2/R3, FU-009..FU-016).

The palette and the ``/`` dropdown both render the output of the pure
``palette_entries(commands, skills)`` builder, so its ordering and
classification contract is tested directly here.
"""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from ohm.core.commands import (
    Command,
    CommandCategory,
    CommandKind,
    CommandRegistry,
    PaletteEntry,
    palette_entries,
)
from ohm.core.skills.schema import Skill


def _cmd(
    name: str,
    description: str = "desc",
    *,
    hotkey: str | None = None,
    kind: CommandKind = CommandKind.DISPLAY_ONLY,
    action: str | None = None,
    payload: str | None = None,
    cli_equivalent: str | None = None,
) -> Command:
    """Build a minimal Command with catalog-relevant fields set."""
    return Command(
        name=name,
        description=description,
        category=CommandCategory.CORE,
        hotkey=hotkey,
        kind=kind,
        action=action,
        payload=payload,
        cli_equivalent=cli_equivalent,
    )


class TestPaletteEntries:
    """R2/R3: the pure builder contract shared by palette and dropdown."""

    def test_empty_commands_and_no_skills(self):
        assert palette_entries([]) == []

    def test_catalog_keeps_registration_order(self):
        cmds = [_cmd("/run"), _cmd("/fix"), _cmd("/test")]
        entries = palette_entries(cmds)
        assert [e.name for e in entries] == ["/run", "/fix", "/test"]

    def test_skills_appended_last_sorted_by_name(self):
        cmds = [_cmd("/run"), _cmd("/fix")]
        entries = palette_entries(
            cmds,
            skills={"python": object(), "debug": object()},
        )
        assert [e.name for e in entries] == [
            "/run",
            "/fix",
            "/skill debug",
            "/skill python",
        ]

    def test_skill_entries_are_real_actions_with_payload(self):
        (entry,) = palette_entries([], skills=["python"])
        assert entry.name == "/skill python"
        assert entry.kind is CommandKind.REAL
        assert entry.action == "skill_run"
        assert entry.payload == "python"
        assert entry.hotkey is None

    def test_skill_entries_accept_skill_objects(self):
        skill = Skill(
            name="debug",
            description="Debug helper",
            path=Path("/skills/debug"),
            instructions="Body",
        )
        (entry,) = palette_entries([], skills=[skill])
        assert entry.name == "/skill debug"
        assert entry.payload == "debug"

    def test_catalog_kind_and_action_preserved(self):
        cmds = [_cmd("/sessions", kind=CommandKind.REAL, action="session_browser")]
        (entry,) = palette_entries(cmds)
        assert entry.kind is CommandKind.REAL
        assert entry.action == "session_browser"

    def test_catalog_cli_equivalent_recorded(self):
        (entry,) = palette_entries([_cmd("/run", cli_equivalent="run")])
        # cli_equivalent is registry-side provenance; the entry still carries
        # the TUI name and kind so both surfaces render it identically.
        assert entry.name == "/run"
        assert entry.kind is CommandKind.DISPLAY_ONLY

    def test_real_registry_skills_appended_after_all_catalog_entries(self):
        """R3 scenario: entries N+1..N+2 are the sorted /skill entries."""
        cmds = CommandRegistry().get_all()
        entries = palette_entries(cmds, skills=["python", "debug"])
        assert len(entries) == len(cmds) + 2
        assert entries[-2].name == "/skill debug"
        assert entries[-1].name == "/skill python"
        for entry in entries[: len(cmds)]:
            assert not entry.name.startswith("/skill ")


class TestPaletteEntry:
    def test_entry_is_frozen_and_hashable(self):
        entry = PaletteEntry(
            name="/run",
            description="Execute a prompt",
            hotkey="Ctrl+Enter",
            action=None,
            payload=None,
            kind=CommandKind.DISPLAY_ONLY,
        )
        with pytest.raises(FrozenInstanceError):
            entry.name = "/fix"
        hash(entry)  # frozen dataclass is hashable
