"""OHM CLI - cron subcommand."""

from __future__ import annotations

import argparse


def register(registry) -> None:
    registry.register_subcommand(
        name="cron",
        help_text="Manage scheduled tasks (list, add, remove, pause, resume)",
        handler=execute,
        args_setup=add_arguments,
    )


def add_arguments(parser: argparse._ActionsContainer) -> None:
    sub = parser.add_subparsers(dest="cron_command", help="Cron commands")

    sub.add_parser("list", help="List scheduled tasks")

    add_p = sub.add_parser("add", help="Schedule a task")
    add_p.add_argument("expression", help="Cron expression (e.g. '0 */6 * * *')")
    add_p.add_argument("--command", "-c", required=True, help="Command to run")
    add_p.add_argument("--name", "-n", help="Task name")

    remove_p = sub.add_parser("remove", help="Remove a scheduled task")
    remove_p.add_argument("task_id", help="Task ID")

    run_p = sub.add_parser("run", help="Run a task now")
    run_p.add_argument("task_id", help="Task ID")

    pause_p = sub.add_parser("pause", help="Pause a scheduled task")
    pause_p.add_argument("task_id", help="Task ID")

    resume_p = sub.add_parser("resume", help="Resume a scheduled task")
    resume_p.add_argument("task_id", help="Task ID")


def execute(args: argparse.Namespace) -> int:
    cmd = getattr(args, "cron_command", None)

    if cmd == "list":
        print("[cron] Scheduled tasks:")
        print("  ID   EXPRESSION      COMMAND                  STATUS")
        print("  ---  --------------  -----------------------  -------")
        print("  001  0 */6 * * *     ohm status --json         active")
        print("  002  30 2 * * 1      ohm test --fix --coverage paused")
        return 0

    if cmd == "add":
        name = getattr(args, "name", None) or "unnamed"
        print(f"[cron] Adding task '{name}'...")
        print(f"[cron]   expression: {args.expression}")
        print(f"[cron]   command: {args.command}")
        print(f"[cron] => Task would be scheduled.")
        return 0

    if cmd == "remove":
        print(f"[cron] Removing task '{args.task_id}'...")
        print(f"[cron] => Task '{args.task_id}' would be removed.")
        return 0

    if cmd == "run":
        print(f"[cron] Running task '{args.task_id}' now...")
        print(f"[cron] => Task would execute.")
        return 0

    if cmd == "pause":
        print(f"[cron] Pausing task '{args.task_id}'...")
        print(f"[cron] => Task '{args.task_id}' would be paused.")
        return 0

    if cmd == "resume":
        print(f"[cron] Resuming task '{args.task_id}'...")
        print(f"[cron] => Task '{args.task_id}' would be resumed.")
        return 0

    print("[cron] Usage: ohm cron {list|add|remove|run|pause|resume}")
    return 2
