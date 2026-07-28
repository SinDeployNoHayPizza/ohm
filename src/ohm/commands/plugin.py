"""OHM CLI - plugin subcommand."""

from __future__ import annotations

import argparse


def register(registry) -> None:
    registry.register_subcommand(
        name="plugin",
        help_text="Manage plugins (list, install, remove, info)",
        handler=execute,
        args_setup=add_arguments,
    )


def add_arguments(parser: argparse._ActionsContainer) -> None:
    sub = parser.add_subparsers(dest="plugin_command", help="Plugin commands")

    sub.add_parser("list", help="List installed plugins")

    install_p = sub.add_parser("install", help="Install a plugin")
    install_p.add_argument("name", help="Plugin name or URL")

    remove_p = sub.add_parser("remove", help="Remove a plugin")
    remove_p.add_argument("name", help="Plugin name")

    info_p = sub.add_parser("info", help="Show plugin details")
    info_p.add_argument("name", help="Plugin name")


def execute(args: argparse.Namespace) -> int:
    cmd = getattr(args, "plugin_command", None)

    if cmd == "list":
        print("[plugin] Installed plugins:")
        print("  - logfire-instrumentation  v1.2.0  (observability)")
        print("  - pydantic-ai-agents       v0.1.0  (agent framework)")
        return 0

    if cmd == "install":
        print(f"[plugin] Installing '{args.name}'...")
        print(f"[plugin] => Plugin '{args.name}' would be installed.")
        return 0

    if cmd == "remove":
        print(f"[plugin] Removing '{args.name}'...")
        print(f"[plugin] => Plugin '{args.name}' would be removed.")
        return 0

    if cmd == "info":
        print(f"[plugin] Plugin: {args.name}")
        print(f"[plugin]   version: 0.1.0")
        print(f"[plugin]   status:  active")
        print(f"[plugin] => Full details would appear here.")
        return 0

    print("[plugin] Usage: ohm plugin {list|install|remove|info}")
    return 2
