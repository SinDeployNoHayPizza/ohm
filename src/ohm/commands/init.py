"""ohm init - Initialize OHM in the current directory."""

from __future__ import annotations

import argparse
from pathlib import Path


def register_args(parser: argparse._ActionsContainer) -> None:
    """Add arguments for the ``init`` subcommand."""
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Overwrite existing OHM configuration",
    )
    parser.add_argument(
        "--global",
        action="store_true",
        default=False,
        dest="global_init",
        help="Initialize global config (~/.ohm/config.yaml)",
    )


def register(registry) -> None:
    """Register the ``init`` subcommand with the CLI registry."""
    registry.register_subcommand(
        name="init",
        help_text="Initialize OHM in the current directory",
        handler=handler,
        args_setup=register_args,
    )


_INIT_TEMPLATE = """\
# OHM Project Configuration
# Docs: docs/configuration.md
# See also: example.env for API keys

# Provider: anthropic | openai | gemini | bedrock | ollama
provider: anthropic

# Model (provider-specific, see docs for options)
model: claude-sonnet-4-6

# Generation settings
max_tokens: 4096
temperature: 0.7

# Sandbox mode (tools run in isolation)
sandbox: true

# Tools to load (strands_tools modules)
tools:
  - file_read
  - file_write
  - editor
  - calculator
  - current_time
  - http_request
  - think

# MCP servers (optional)
# mcp:
#   my-server:
#     command: my-mcp-server
#     args: ["--flag"]
"""


def handler(args: argparse.Namespace) -> int:
    """Execute the ``init`` command."""
    if args.global_init:
        return _init_global(args.force)
    return _init_project(args.force)


def _init_project(force: bool) -> int:
    """Create .ohm/ directory with config.yaml in current directory."""
    from ohm.core.config import PROJECT_DIR, PROJECT_CONFIG

    if PROJECT_CONFIG.exists() and not force:
        print(f"[init] Config already exists: {PROJECT_CONFIG}")
        print("[init] Use --force to overwrite")
        return 0

    PROJECT_DIR.mkdir(exist_ok=True)
    PROJECT_CONFIG.write_text(_INIT_TEMPLATE, encoding="utf-8")

    print(f"[init] Created {PROJECT_DIR}/")
    print(f"[init] Created {PROJECT_CONFIG}")
    print("[init] Edit the config file to customize your settings")
    print("[init] Set API keys in .env (see example.env)")
    return 0


def _init_global(force: bool) -> int:
    """Create ~/.ohm/ directory with config.yaml."""
    from ohm.core.config import GLOBAL_DIR, GLOBAL_CONFIG, SESSIONS_DIR

    if GLOBAL_CONFIG.exists() and not force:
        print(f"[init] Global config already exists: {GLOBAL_CONFIG}")
        print("[init] Use --force to overwrite")
        return 0

    GLOBAL_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    GLOBAL_CONFIG.write_text(_INIT_TEMPLATE, encoding="utf-8")

    print(f"[init] Created {GLOBAL_DIR}/")
    print(f"[init] Created {GLOBAL_CONFIG}")
    print(f"[init] Created {SESSIONS_DIR}/")
    return 0
