"""ohm status - Show real system status information."""

from __future__ import annotations

import argparse
import platform
import shutil
import sys
from pathlib import Path


def register_args(parser: argparse._ActionsContainer) -> None:
    """Add arguments for the ``status`` subcommand."""
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        default=False,
        help="Output status in JSON format",
    )


def register(registry) -> None:
    """Register the ``status`` subcommand with the CLI registry."""
    registry.register_subcommand(
        name="status",
        help_text="Show system status information",
        handler=handler,
        args_setup=register_args,
    )


def handler(args: argparse.Namespace) -> int:
    """Execute the ``status`` command."""
    from ohm import __version__
    from ohm.core.config import get_config, GLOBAL_CONFIG, PROJECT_CONFIG, SESSIONS_DIR

    cfg = get_config()

    # Gather real data
    python_version = platform.python_version()
    platform_name = platform.system().lower()
    terminal_cols, terminal_rows = shutil.get_terminal_size((80, 24))

    # Config status
    global_ok = GLOBAL_CONFIG.exists()
    project_ok = PROJECT_CONFIG.exists()

    # API key detection
    api_key_status = {}
    from ohm.core.config import _API_KEY_ENV
    import os
    for provider, env_vars in _API_KEY_ENV.items():
        if provider == "ollama":
            api_key_status[provider] = "local"
        elif any(os.environ.get(v) for v in env_vars):
            api_key_status[provider] = "configured"
        else:
            api_key_status[provider] = "missing"

    # Available provider (first one with a key)
    active_provider = cfg.provider
    active_model = cfg.model

    # Session count
    session_count = 0
    if SESSIONS_DIR.exists():
        session_count = len(list(SESSIONS_DIR.glob("*.json")))

    # Strands availability
    strands_ok = False
    try:
        import strands
        strands_ok = True
    except ImportError:
        pass

    # Textual availability
    textual_ok = False
    try:
        import textual
        textual_ok = True
    except ImportError:
        pass

    if args.as_json:
        import json
        status = {
            "version": __version__,
            "python": python_version,
            "platform": platform_name,
            "provider": active_provider,
            "model": active_model,
            "theme": cfg.theme,
            "providers": api_key_status,
            "config": {
                "global": global_ok,
                "project": project_ok,
            },
            "sessions": session_count,
            "terminal": f"{terminal_cols}x{terminal_rows}",
            "strands": strands_ok,
            "textual": textual_ok,
        }
        print(json.dumps(status, indent=2))
    else:
        print(f"OHM v{__version__}\n")

        print(f"  Python:   {python_version}")
        print(f"  Platform: {platform_name}")
        print(f"  Terminal: {terminal_cols}x{terminal_rows}")
        print()

        print(f"  Provider: {active_provider}")
        print(f"  Model:    {active_model}")
        print(f"  Theme:    {cfg.theme}")
        print()

        print("  Providers:")
        for p, status in api_key_status.items():
            icon = {"configured": "[ok]", "local": "[ok]", "missing": "[--]"}[status]
            print(f"    {icon} {p}: {status}")
        print()

        print(f"  Config:")
        print(f"    Global:  {'[ok]' if global_ok else '[--]'} {GLOBAL_CONFIG}")
        print(f"    Project: {'[ok]' if project_ok else '[--]'} {PROJECT_CONFIG}")
        print()

        print(f"  Sessions: {session_count}")
        print(f"  Strands:  {'[ok]' if strands_ok else '[--]'}")
        print(f"  Textual:  {'[ok]' if textual_ok else '[--]'}")

    return 0
