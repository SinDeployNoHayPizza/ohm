"""ohm run - Execute a prompt and print the response."""

from __future__ import annotations

import argparse
import asyncio
import sys
import time


def register_args(parser: argparse._ActionsContainer) -> None:
    """Add arguments for the ``run`` subcommand."""
    parser.add_argument("prompt", help="The prompt to execute")
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
    parser.add_argument(
        "--stream", "-s",
        action="store_true",
        default=False,
        help="Stream the response token-by-token",
    )


def register(registry) -> None:
    """Register the ``run`` subcommand with the CLI registry."""
    registry.register_subcommand(
        name="run",
        help_text="Execute a prompt and print the response",
        handler=handler,
        args_setup=register_args,
    )


def handler(args: argparse.Namespace) -> int:
    """Execute the ``run`` command. Returns exit code."""
    from ohm.core.agent import Agent, AgentConfig

    model_info = f"model={args.model}" if args.model else f"model=provider-default"
    print(f"[run] provider={args.provider} {model_info}", file=sys.stderr)
    print(f"[run] prompt: {args.prompt}", file=sys.stderr)

    config = AgentConfig(
        provider=args.provider,
        model=args.model or "",
    )
    agent = Agent(config)

    try:
        if args.stream:
            return _handle_stream(agent, args.prompt)
        else:
            return _handle_run(agent, args.prompt)
    except KeyboardInterrupt:
        print("\n[run] Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"[run] Error: {exc}", file=sys.stderr)
        return 1


def _handle_run(agent: Agent, prompt: str) -> int:
    """Non-streaming execution."""
    print("[run] Calling agent...", file=sys.stderr)
    t0 = time.monotonic()
    response = asyncio.run(agent.run(prompt))
    latency = (time.monotonic() - t0) * 1000

    if response.success:
        print(response.content)
        print(f"\n[run] Done in {latency:.0f}ms", file=sys.stderr)
        return 0
    else:
        print(f"[run] Agent error: {response.error}", file=sys.stderr)
        return 1


def _handle_stream(agent: Agent, prompt: str) -> int:
    """Streaming execution — prints tokens as they arrive."""
    print("[run] Streaming...", file=sys.stderr)

    async def _stream() -> int:
        collected: list[str] = []
        try:
            async for event in agent.stream(prompt):
                # strands yields event dicts; extract text chunks
                if isinstance(event, dict):
                    if "contentBlockDelta" in event:
                        delta = event["contentBlockDelta"]
                        if isinstance(delta, dict) and "delta" in delta:
                            text = delta["delta"].get("text", "")
                            if text:
                                print(text, end="", flush=True)
                                collected.append(text)
                    elif "content" in event:
                        # Some strands versions yield content directly
                        text = str(event["content"])
                        print(text, end="", flush=True)
                        collected.append(text)
        except Exception as exc:
            print(f"\n[run] Stream error: {exc}", file=sys.stderr)
            return 1

        print()  # final newline
        return 0

    return asyncio.run(_stream())
