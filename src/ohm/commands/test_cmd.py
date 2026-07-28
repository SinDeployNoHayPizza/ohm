"""ohm test - Run the test suite."""

from __future__ import annotations

import argparse


def register_args(parser: argparse._ActionsContainer) -> None:
    """Add arguments for the ``test`` subcommand."""
    parser.add_argument(
        "--fix",
        action="store_true",
        default=False,
        help="Attempt to auto-fix failing tests",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        default=False,
        help="Generate a coverage report",
    )


def register(registry) -> None:
    """Register the ``test`` subcommand with the CLI registry."""
    registry.register_subcommand(
        name="test",
        help_text="Run the test suite",
        handler=handler,
        args_setup=register_args,
    )


def handler(args: argparse.Namespace) -> int:
    """Execute the ``test`` command."""
    flags = []
    if args.fix:
        flags.append("--fix")
    if args.coverage:
        flags.append("--coverage")
    flags_str = " ".join(flags)
    print(f"[test] Running test suite{' ' + flags_str if flags_str else ''}")
    print("[test] => Test results would appear here.")
    return 0
