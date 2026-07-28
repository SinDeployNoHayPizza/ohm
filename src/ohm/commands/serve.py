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
        "--port", "-p",
        type=int,
        default=8080,
        help="Port (default: 8080)",
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

    print(f"[serve] OHM v{__version__} — headless mode")
    print(f"[serve]   host:    {args.host}")
    print(f"[serve]   port:    {args.port}")
    print(f"[serve]   workers: {args.workers}")
    print(f"[serve]   reload:  {args.reload}")
    print(f"[serve]")
    print(f"[serve] => Server would start on http://{args.host}:{args.port}")
    print(f"[serve] => API endpoints:")
    print(f"[serve]     POST /v1/run       Execute a prompt")
    print(f"[serve]     POST /v1/goal      Set an autonomous goal")
    print(f"[serve]     GET  /v1/status     System status")
    print(f"[serve]     GET  /v1/health     Health check")
    print(f"[serve]     GET  /v1/models     List available models")
    return 0
