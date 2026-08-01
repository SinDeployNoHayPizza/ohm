"""CLI command for managing and listing skills."""

from __future__ import annotations

import argparse

from ohm.core.skills.loader import DEFAULT_SKILL_SEARCH_PATHS, SkillLoader
from ohm.core.skills.registry import SkillRegistry


def register(registry) -> None:
    """Register skill subcommand with CLI registry."""
    registry.register_subcommand(
        name="skill",
        help_text="Manage and list discovered skills",
        handler=handler,
        args_setup=register_args,
    )


def register_args(parser: argparse.ArgumentParser) -> None:
    """Register CLI arguments for `ohm skill`."""
    subparsers = parser.add_subparsers(dest="skill_action", help="Skill action")

    # `ohm skill list`
    subparsers.add_parser("list", help="List discovered skills")


def handler(args: argparse.Namespace) -> int:
    """Execute `ohm skill` action."""
    action = getattr(args, "skill_action", "list") or "list"

    # DD-08: single source shared with the TUI (OhmApp.on_mount)
    search_paths = DEFAULT_SKILL_SEARCH_PATHS()

    discovered = SkillLoader.discover_skills(search_paths)
    registry = SkillRegistry()
    for skill in discovered.values():
        registry.register(skill)

    if action == "list":
        skills = registry.list_skills()
        if not skills:
            print("No skills discovered.")
            return 0

        print(f"Discovered Skills ({len(skills)}):\n")
        for s in skills:
            status = "enabled" if s.enabled else "disabled"
            print(f"  • {s.name:<24} ({status}) — {s.description}")
            print(f"    Path: {s.path}")
        return 0

    print(f"Unknown skill action: {action}")
    return 1
