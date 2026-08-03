"""OHM CLI - serve subcommand (headless/server mode)."""

from __future__ import annotations

import argparse


def register(registry) -> None:
    registry.register_subcommand(
        name="serve",
        help_text="Run OHM as an HTTP API server (headless mode)",
        handler=execute,
        args_setup=add_arguments,
    )


def add_arguments(parser: argparse._ActionsContainer) -> None:
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind address (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--protocol",
        choices=("http", "mcp"),
        default="http",
        help="Server protocol: http (API placeholder) or mcp (MCP server)",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=None,
        help="Port (default: 8080 for http, config or 3000 for mcp)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Worker threads (default: 1)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=False,
        help="Auto-reload on code changes (dev mode)",
    )


def execute(args: argparse.Namespace) -> int:
    from ohm import __version__

    protocol = getattr(args, "protocol", "http")

    if protocol == "mcp":
        # MCP-10: `ohm serve --protocol mcp` is the alias for the MCP
        # server. CLI flags win, then the config mcp_server section,
        # then defaults (MCP-11). CF2: run_http blocks — no asyncio.run().
        from ohm.core.config import get_config
        from ohm.core.mcp_server import _resolve_server_args, run_http

        cfg = get_config()
        resolved = _resolve_server_args(args, cfg)
        print(f"[serve] MCP server listening on http://{resolved['host']}:{resolved['port']}")
        run_http(resolved["host"], resolved["port"])
        return 0

    # http protocol (placeholder, preserved). Port resolves to 8080 when
    # omitted (today's value) — --port is None by default.
    port = args.port if args.port is not None else 8080

    print(f"[serve] OHM v{__version__} — headless mode")
    print(f"[serve]   host:    {args.host}")
    print(f"[serve]   port:    {port}")
    print(f"[serve]   workers: {args.workers}")
    print(f"[serve]   reload:  {args.reload}")
    print(f"[serve]")
    print(f"[serve] => Server would start on http://{args.host}:{port}")
    print(f"[serve] => API endpoints:")
    print(f"[serve]     POST /v1/run       Execute a prompt")
    print(f"[serve]     POST /v1/goal      Set an autonomous goal")
    print(f"[serve]     GET  /v1/status     System status")
    print(f"[serve]     GET  /v1/health     Health check")
    print(f"[serve]     GET  /v1/models     List available models")
    return 0
