"""ohm goal - Set an autonomous goal for the agent."""

from __future__ import annotations

import argparse
import asyncio
import sys
import time


def register_args(parser: argparse._ActionsContainer) -> None:
    """Add arguments for the ``goal`` subcommand."""
    parser.add_argument("description", help="Goal description for the agent")
    parser.add_argument(
        "--provider", "-p",
        default="anthropic",
        help="LLM provider (default: anthropic)",
    )
    parser.add_argument(
        "--model", "-m",
        default=None,
        help="Model to use (default: provider-specific)",
    )


def register(registry) -> None:
    """Register the ``goal`` subcommand with the CLI registry."""
    registry.register_subcommand(
        name="goal",
        help_text="Set an autonomous goal for the agent",
        handler=handler,
        args_setup=register_args,
    )


GOAL_SYSTEM_PROMPT = (
    "You are OHM, an autonomous coding agent. "
    "You have been given a high-level goal. "
    "Break it into concrete steps, then execute each step using your tools "
    "(shell, file_read, file_write, calculator). "
    "Report your progress and final result."
)


def handler(args: argparse.Namespace) -> int:
    """Execute the ``goal`` command. Returns exit code."""
    from ohm.core.agent import Agent, AgentConfig

    model_info = f"model={args.model}" if args.model else "model=provider-default"
    print(f"[goal] provider={args.provider} {model_info}", file=sys.stderr)
    print(f"[goal] goal: {args.description}", file=sys.stderr)

    config = AgentConfig(
        provider=args.provider,
        model=args.model or "",
        system_prompt=GOAL_SYSTEM_PROMPT,
    )
    agent = Agent(config)

    try:
        print("[goal] Agent working...", file=sys.stderr)
        t0 = time.monotonic()
        response = asyncio.run(agent.run(args.description))
        latency = (time.monotonic() - t0) * 1000

        if response.success:
            print(response.content)
            print(f"\n[goal] Completed in {latency:.0f}ms", file=sys.stderr)
            return 0
        else:
            print(f"[goal] Agent error: {response.error}", file=sys.stderr)
            return 1

    except KeyboardInterrupt:
        print("\n[goal] Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"[goal] Error: {exc}", file=sys.stderr)
        return 1
