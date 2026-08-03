"""OHM CLI - mcp subcommand."""

from __future__ import annotations

import argparse


def register(registry) -> None:
    registry.register_subcommand(
        name="mcp",
        help_text="Manage MCP server connections (list, add, remove, status)",
        handler=execute,
        args_setup=add_arguments,
    )


def add_arguments(parser: argparse._ActionsContainer) -> None:
    sub = parser.add_subparsers(dest="mcp_command", help="MCP commands")

    sub.add_parser("list", help="List configured MCP servers")
    sub.add_parser("status", help="Check server health").add_argument(
        "name", nargs="?", help="Server name"
    )

    add_p = sub.add_parser("add", help="Add server config")
    add_p.add_argument("name", help="Server name")
    add_p.add_argument("--command", "-c", required=True, help="Server command")
    add_p.add_argument("--args", nargs="*", default=[], help="Command arguments")

    remove_p = sub.add_parser("remove", help="Remove server config")
    remove_p.add_argument("name", help="Server name")

    connect_p = sub.add_parser("connect", help="Connect to server")
    connect_p.add_argument("name", help="Server name")

    serve_p = sub.add_parser("serve", help="Start the OHM MCP server")
    serve_p.add_argument(
        "--transport",
        choices=("stdio", "http"),
        default=None,
        help="Transport (default: config or stdio)",
    )
    serve_p.add_argument(
        "--host",
        default=None,
        help="Bind host (default: config or 127.0.0.1)",
    )
    serve_p.add_argument(
        "--port", "-p",
        type=int,
        default=None,
        help="Bind port (default: config or 3000)",
    )


def execute(args: argparse.Namespace) -> int:
    cmd = getattr(args, "mcp_command", None)

    if cmd == "list":
        print("[mcp] Configured servers:")
        print("  codegraph   sqlite://~/.ohm/mcp/codegraph.db")
        print("  context7    http://localhost:3001")
        return 0

    if cmd == "add":
        print(f"[mcp] Adding server '{args.name}'...")
        print(f"[mcp]   command: {args.command}")
        print(f"[mcp]   args: {args.args}")
        print(f"[mcp] => Server '{args.name}' would be configured.")
        return 0

    if cmd == "remove":
        print(f"[mcp] Removing server '{args.name}'...")
        print(f"[mcp] => Server '{args.name}' would be removed.")
        return 0

    if cmd == "status":
        name = getattr(args, "name", None)
        if name:
            print(f"[mcp] Checking '{name}'...")
            print(f"[mcp] => {name}: healthy (placeholder)")
        else:
            print("[mcp] Server name required: ohm mcp status <name>")
        return 0

    if cmd == "connect":
        print(f"[mcp] Connecting to '{args.name}'...")
        print(f"[mcp] => Connection to '{args.name}' would be established.")
        return 0

    if cmd == "serve":
        # Start the OHM MCP server. Resolution order (MCP-11):
        # CLI flags > config mcp_server section > built-in defaults.
        # CF2: run_stdio/run_http block on the event loop — no asyncio.run().
        from ohm.core.config import get_config
        from ohm.core.mcp_server import _resolve_server_args, run_http, run_stdio

        cfg = get_config()
        resolved = _resolve_server_args(args, cfg)
        if resolved["transport"] == "http":
            run_http(resolved["host"], resolved["port"])
        else:
            run_stdio()
        return 0

    print("[mcp] Usage: ohm mcp {list|add|remove|status|connect|serve}")
    return 2
