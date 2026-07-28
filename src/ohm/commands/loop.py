"""ohm loop - Run a command in a loop until a condition is met."""

from __future__ import annotations

import argparse


def register_args(parser: argparse._ActionsContainer) -> None:
    """Add arguments for the ``loop`` subcommand."""
    parser.add_argument("command", help="Command to execute each iteration")
    parser.add_argument(
        "--max", "-n",
        type=int,
        dest="max_iterations",
        default=10,
        help="Maximum number of iterations (default: 10)",
    )
    parser.add_argument(
        "--until", "-u",
        default=None,
        help='Stop when this condition is met (e.g. "tests pass")',
    )


def register(registry) -> None:
    """Register the ``loop`` subcommand with the CLI registry."""
    registry.register_subcommand(
        name="loop",
        help_text="Run a command in a loop until a condition is met",
        handler=handler,
        args_setup=register_args,
    )


def handler(args: argparse.Namespace) -> int:
    """Execute the ``loop`` command."""
    until_info = f' until="{args.until}"' if args.until else ""
    print(f"[loop] command: {args.command}")
    print(f"[loop] max_iterations={args.max_iterations}{until_info}")
    print("[loop] => Would execute command in a loop.")
    return 0
