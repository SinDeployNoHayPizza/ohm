"""ohm config - Manage OHM configuration."""

from __future__ import annotations

import argparse
import json


def register_args(parser: argparse._ActionsContainer) -> None:
    """Add arguments for the ``config`` subcommand."""
    sub = parser.add_subparsers(dest="action", help="Config action")

    # get
    get_p = sub.add_parser("get", help="Get a config value")
    get_p.add_argument("key", nargs="?", default=None, help="Key to get (omit for all)")

    # set
    set_p = sub.add_parser("set", help="Set a config value")
    set_p.add_argument("key", help="Key to set")
    set_p.add_argument("value", help="Value to set")

    # path
    sub.add_parser("path", help="Show config file paths")

    # show
    sub.add_parser("show", help="Show resolved config")


def register(registry) -> None:
    """Register the ``config`` subcommand with the CLI registry."""
    registry.register_subcommand(
        name="config",
        help_text="Manage OHM configuration",
        handler=handler,
        args_setup=register_args,
    )


def handler(args: argparse.Namespace) -> int:
    """Execute the ``config`` command."""
    action = getattr(args, "action", None) or "show"

    if action == "get":
        return _handle_get(args)
    elif action == "set":
        return _handle_set(args)
    elif action == "path":
        return _handle_path()
    elif action == "show":
        return _handle_show()
    else:
        return _handle_show()


def _handle_get(args: argparse.Namespace) -> int:
    """Get a config value or show all."""
    from ohm.core.config import get_config
    cfg = get_config()

    key = getattr(args, "key", None)
    if key:
        value = getattr(cfg, key, None)
        if value is None:
            # Check if it's a known key
            valid = [k for k in dir(cfg) if not k.startswith("_") and not callable(getattr(cfg, k, None))]
            if key in valid:
                print(f"{key} = {getattr(cfg, key)}")
            else:
                print(f"[config] Unknown key: {key}")
                print(f"[config] Valid keys: {', '.join(valid)}")
                return 2
        else:
            print(f"{key} = {value}")
    else:
        _print_config(cfg)
    return 0


def _handle_set(args: argparse.Namespace) -> int:
    """Set a config value in global config."""
    from ohm.core.config import get_config, save_global_config, GLOBAL_CONFIG
    cfg = get_config(reload=True)

    key = args.key
    value = args.value

    # Type coercion
    if hasattr(cfg, key):
        current = getattr(cfg, key)
        if isinstance(current, bool):
            setattr(cfg, key, value.lower() in ("true", "1", "yes"))
        elif isinstance(current, int):
            try:
                setattr(cfg, key, int(value))
            except ValueError:
                print(f"[config] Error: {key} requires an integer value")
                return 2
        elif isinstance(current, float):
            try:
                setattr(cfg, key, float(value))
            except ValueError:
                print(f"[config] Error: {key} requires a numeric value")
                return 2
        else:
            setattr(cfg, key, value)

        save_global_config(cfg)
        print(f"[config] {key} = {getattr(cfg, key)}")
        print(f"[config] Saved to {GLOBAL_CONFIG}")
    else:
        print(f"[config] Unknown key: {key}")
        return 2
    return 0


def _handle_path() -> int:
    """Show config file paths."""
    from ohm.core.config import GLOBAL_CONFIG, PROJECT_CONFIG, SESSIONS_DIR
    print(f"Global config:  {GLOBAL_CONFIG}")
    print(f"Project config: {PROJECT_CONFIG}")
    print(f"Sessions dir:   {SESSIONS_DIR}")
    return 0


def _handle_show() -> int:
    """Show resolved config."""
    from ohm.core.config import get_config
    cfg = get_config()
    _print_config(cfg)
    return 0


def _print_config(cfg: object) -> None:
    """Pretty-print config values."""
    print("OHM Configuration:\n")
    for key in sorted(dir(cfg)):
        if key.startswith("_"):
            continue
        value = getattr(cfg, key, None)
        if callable(value):
            continue
        if isinstance(value, list):
            print(f"  {key}:")
            for item in value:
                print(f"    - {item}")
        elif isinstance(value, dict):
            if value:
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {{}}")
        else:
            print(f"  {key}: {value}")
