"""OHM CLI - skills subcommand."""

from __future__ import annotations

import argparse


def register(registry) -> None:
    registry.register_subcommand(
        name="skills",
        help_text="Manage agent skills (list, install, remove, search)",
        handler=execute,
        args_setup=add_arguments,
    )


def add_arguments(parser: argparse._ActionsContainer) -> None:
    sub = parser.add_subparsers(dest="skills_command", help="Skills commands")

    sub.add_parser("list", help="List installed skills")
    install_p = sub.add_parser("install", help="Install a skill")
    install_p.add_argument("name", help="Skill name or URL")
    remove_p = sub.add_parser("remove", help="Remove a skill")
    remove_p.add_argument("name", help="Skill name")
    search_p = sub.add_parser("search", help="Search for skills")
    search_p.add_argument("query", help="Search query")


def execute(args: argparse.Namespace) -> int:
    cmd = getattr(args, "skills_command", None)

    if cmd == "list":
        print("[skills] Installed skills:")
        print("  - python-debugger")
        print("  - git-ops")
        print("  - code-review")
        return 0

    if cmd == "install":
        print(f"[skills] Installing '{args.name}'...")
        print(f"[skills] => Skill '{args.name}' would be installed.")
        return 0

    if cmd == "remove":
        print(f"[skills] Removing '{args.name}'...")
        print(f"[skills] => Skill '{args.name}' would be removed.")
        return 0

    if cmd == "search":
        print(f"[skills] Searching for '{args.query}'...")
        print(f"[skills] => Results would appear here.")
        return 0

    print("[skills] Usage: ohm skills {list|install|remove|search}")
    return 2
