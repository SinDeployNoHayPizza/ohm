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
    registry = Registry()
    register_all(registry)
    result = registry.parse(argv)
    return registry.dispatch(result)


if __name__ == "__main__":
    sys.exit(main())
