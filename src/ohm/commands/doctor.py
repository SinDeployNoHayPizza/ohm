"""OHM CLI - doctor subcommand."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import sys
from pathlib import Path


def register(registry) -> None:
    registry.register_subcommand(
        name="doctor",
        help_text="Check environment health and configuration",
        handler=execute,
        args_setup=add_arguments,
    )


def add_arguments(parser: argparse._ActionsContainer) -> None:
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output in JSON format",
    )


def _check_python() -> tuple[str, str]:
    v = platform.python_version()
    return ("ok", f"Python {v}")


def _check_ohm() -> tuple[str, str]:
    from ohm import __version__
    return ("ok", f"OHM {__version__}")


def _check_terminal() -> tuple[str, str]:
    cols = shutil.get_terminal_size((80, 24)).columns
    rows = shutil.get_terminal_size((80, 24)).lines
    color = sys.stdout.isatty()
    return ("ok", f"Terminal: {cols}x{rows}, color={'true' if color else 'false'}")


def _check_dependencies() -> tuple[str, str]:
    missing = []
    for pkg in ["textual", "rich"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        return ("error", f"Missing: {', '.join(missing)}")
    return ("ok", "Dependencies: textual, rich")


def _check_config() -> tuple[str, str]:
    from ohm.core.config import GLOBAL_CONFIG, PROJECT_CONFIG
    parts: list[str] = []
    if GLOBAL_CONFIG.exists():
        parts.append(f"global: {GLOBAL_CONFIG}")
    if PROJECT_CONFIG.exists():
        parts.append(f"project: {PROJECT_CONFIG}")
    if parts:
        return ("ok", f"Config: {', '.join(parts)}")
    return ("warn", "Config: no config files found (using defaults)")


def _check_env() -> tuple[str, str]:
    """Check .env file and API keys."""
    from ohm.core.config import _load_dotenv
    dotenv = Path(".env")
    keys_found: list[str] = []

    # Check .env file
    env_data = _load_dotenv(dotenv)
    for key, value in env_data.items():
        if value and key.endswith("_API_KEY"):
            provider = key.replace("_API_KEY", "").lower()
            keys_found.append(provider)

    # Also check os.environ
    for var in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"]:
        if os.environ.get(var):
            provider = var.replace("_API_KEY", "").lower()
            if provider not in keys_found:
                keys_found.append(provider)

    if keys_found:
        return ("ok", f"API keys: {', '.join(keys_found)}")
    return ("warn", "API keys: none found (set in .env or environment)")


def _check_sessions() -> tuple[str, str]:
    from ohm.core.config import SESSIONS_DIR
    if SESSIONS_DIR.exists():
        writable = True
        try:
            test_file = SESSIONS_DIR / ".write_test"
            test_file.touch()
            test_file.unlink()
        except OSError:
            writable = False
        if writable:
            return ("ok", f"Sessions: {SESSIONS_DIR} (writable)")
        return ("error", f"Sessions: {SESSIONS_DIR} (not writable)")
    return ("warn", f"Sessions: {SESSIONS_DIR} (not found)")


def _check_providers() -> tuple[str, str]:
    """Check provider health via Provider.check_health()."""
    from ohm.core.config import get_config
    from ohm.core.provider import KNOWN_PROVIDERS, ProviderStatus

    cfg = get_config()
    healthy: list[str] = []
    unhealthy: list[str] = []

    for name in KNOWN_PROVIDERS:
        try:
            provider = cfg.resolve_provider(name)
        except ValueError:
            continue
        status = provider.check_health()
        if status == ProviderStatus.HEALTHY:
            healthy.append(name)
        else:
            unhealthy.append(name)

    parts: list[str] = []
    if healthy:
        parts.append(f"healthy: {', '.join(healthy)}")
    if unhealthy:
        parts.append(f"unhealthy: {', '.join(unhealthy)}")

    return ("ok" if healthy else "warn", f"Providers: {'; '.join(parts) if parts else 'none checked'}")


def execute(args: argparse.Namespace) -> int:
    checks = [
        _check_python(),
        _check_ohm(),
        _check_terminal(),
        _check_dependencies(),
        _check_config(),
        _check_env(),
        _check_sessions(),
        _check_providers(),
    ]

    if args.json:
        import json
        result = {
            "checks": [
                {"status": status, "message": msg}
                for status, msg in checks
            ]
        }
        print(json.dumps(result, indent=2))
        return 0

    icons = {"ok": "[ok]", "warn": "[warn]", "error": "[error]"}
    passed = sum(1 for s, _ in checks if s == "ok")
    warnings = sum(1 for s, _ in checks if s == "warn")
    errors = sum(1 for s, _ in checks if s == "error")

    from ohm import __version__
    print(f"OHM Doctor v{__version__}\n")
    for status, msg in checks:
        print(f"  {icons[status]} {msg}")
    print(f"\n{passed} passed, {warnings} warning{'s' if warnings != 1 else ''}, {errors} error{'s' if errors != 1 else ''}")

    return 0 if errors == 0 else 3
