"""CLI entry point - parses arguments and dispatches to commands.

When invoked with no subcommand, OHM launches the interactive TUI.
"""

from __future__ import annotations

import sys

from ohm.cli.registry import Registry
from ohm.commands import register_all


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]``).

    Returns:
        Exit code following Unix conventions (0 = success).
    """
    # Bootstrap observability (OBS-1/OBS-2): apply log_level/log_format from
    # config. Never blocks startup — logging is best-effort.
    try:
        from ohm.core.config import get_config
        from ohm.core.observability import setup_logging

        setup_logging(get_config())
    except Exception:  # noqa: BLE001
        pass

    registry = Registry()

    # Global flags
    registry.register_global(
        "--continue", "-c",
        dest="continue_",
        action="store_true",
        default=False,
        help="Resume the last session",
    )

    register_all(registry)
    result = registry.parse(argv)
    return registry.dispatch(result)


if __name__ == "__main__":
    sys.exit(main())
