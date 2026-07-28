# OHM CLI Reference

> **Version**: 0.1.0-alpha
> **Status**: Design / Reference Document

---

## Overview

OHM provides both an interactive TUI and a non-interactive CLI. When invoked without
arguments, OHM launches the full-screen TUI. When invoked with a subcommand, OHM
executes the command, prints output to stdout, and exits with a standard exit code.

```
ohm [OPTIONS] [COMMAND [ARGS...]]
```

- **No arguments** → launches interactive TUI
- **With subcommand** → executes and exits (pipeline-friendly)
- **Exit codes** follow Unix/OS conventions

---

## Global Options

| Flag | Description |
|------|-------------|
| `-h`, `--help`, `-?` | Show help message and exit |
| `--version`, `-V` | Show version and exit |

These flags work at both the top level and on any subcommand:

```bash
ohm --version        # ohm 0.1.0-alpha
ohm run --help       # help for the run command
ohm test -?          # same as --help
```

---

## Exit Codes

| Code | Constant | Meaning |
|------|----------|---------|
| `0` | `EXIT_SUCCESS` | Command completed successfully |
| `1` | `EXIT_GENERAL_ERROR` | General error (keyboard interrupt, unexpected failure) |
| `2` | `EXIT_USAGE_ERROR` | Invalid arguments or unknown subcommand |
| `3` | `EXIT_RUNTIME_ERROR` | Command failed during execution |

---

## Commands

### `ohm run`

Execute a prompt against an LLM and print the response.

```
ohm run [OPTIONS] "prompt"
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--provider` | `-p` | `anthropic` | LLM provider to use |
| `--model` | `-m` | provider-specific | Model identifier |
| `--stream` | `-s` | `false` | Stream response token-by-token |

**Examples:**

```bash
ohm run "Explain the SOLID principles"
ohm run -p openai -m gpt-4-turbo "Refactor this function"
ohm run --stream "Write a unit test for AuthService"
echo "Fix the bug" | ohm run -
```

**Output:** The agent's response is printed to stdout. Metadata (tokens, cost,
latency) is printed to stderr when `--verbose` is enabled.

**Exit codes:** `0` on success, `3` if the LLM call fails.

---

### `ohm goal`

Set an autonomous goal for the agent. The agent decomposes the goal into subtasks
and executes them without further user input.

```
ohm goal [OPTIONS] "description"
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--provider` | `-p` | `anthropic` | LLM provider to use |
| `--model` | `-m` | provider-specific | Model identifier |

**Examples:**

```bash
ohm goal "Implement JWT authentication with refresh tokens"
ohm goal -p google "Add comprehensive error handling to all API endpoints"
```

**Output:** Prints the task breakdown and execution progress to stdout.

**Exit codes:** `0` when all subtasks complete, `3` if any subtask fails irrecoverably.

---

### `ohm loop`

Run a command in a loop until a condition is met or the maximum iteration count
is reached. Designed for test-fix-retry workflows.

```
ohm loop [OPTIONS] "command"
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--max` | `-n` | `10` | Maximum number of iterations |
| `--until` | `-u` | — | Stop condition (e.g. `"tests pass"`) |

**Examples:**

```bash
ohm loop "ohm test --fix" --until "all tests pass"
ohm loop -n 5 "pytest tests/ -x" --until "exit code 0"
```

**Output:** Per-iteration results are printed to stdout (tests passed/failed,
fixes applied, duration).

**Exit codes:** `0` if the condition is met, `3` if max iterations reached
without meeting the condition.

---

### `ohm test`

Run the project's test suite.

```
ohm test [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--fix` | Attempt to auto-fix failing tests using the LLM |
| `--coverage` | Generate a coverage report after tests complete |

**Examples:**

```bash
ohm test
ohm test --fix
ohm test --fix --coverage
```

**Output:** Test results (passed/failed/skipped) are printed to stdout.

**Exit codes:** `0` if all tests pass, `3` if any tests fail.

---

### `ohm init`

Initialize OHM configuration in the current directory. Creates the `.ohm/`
directory and default configuration files.

```
ohm init [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--force` | Overwrite existing OHM configuration |

**Examples:**

```bash
ohm init
ohm init --force
```

**Output:** Prints the paths of created configuration files.

**Exit codes:** `0` on success, `2` if already initialized (without `--force`).

---

### `ohm status`

Show system status: provider health, model in use, token usage, active sessions,
and system resources.

```
ohm status [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--json` | Output status in JSON format |

**Examples:**

```bash
ohm status
ohm status --json
```

**Output (default):**

```
OHM v0.1.0-alpha
Status: OK
Provider: anthropic
Model: claude-sonnet-4-20250514
```

**Exit codes:** `0` on success.

---

### `ohm config`

Manage OHM configuration. Read or write configuration values.

```
ohm config [SUBCOMMAND] [ARGS]
```

**Subcommands:**

| Subcommand | Usage | Description |
|------------|-------|-------------|
| `get` | `ohm config get <key>` | Print a configuration value |
| `set` | `ohm config set <key> <value>` | Set a configuration value |

**Examples:**

```bash
ohm config get provider
ohm config set provider openai
ohm config set model gpt-4-turbo
```

**Exit codes:** `0` on success, `2` if key is missing or invalid.

---

## Architecture: Adding a New Command

Each subcommand is a single Python module in `src/ohm/commands/`. The module
exposes a `register(registry)` function that registers the command with the CLI
registry. Commands are **auto-discovered** at startup via `pkgutil.iter_modules`.

### Template

```python
# src/ohm/commands/my_command.py
"""OHM CLI - my-command subcommand."""

from __future__ import annotations
import argparse


def register(registry) -> None:
    """Register the 'my-command' subcommand."""
    registry.register_subcommand(
        name="my-command",
        help_text="Short description shown in --help",
        handler=execute,
        args_setup=add_arguments,
    )


def add_arguments(parser: argparse._ActionsContainer) -> None:
    """Add command-specific arguments to the subparser."""
    parser.add_argument(
        "--my-flag", "-f",
        action="store_true",
        default=False,
        help="Description of this flag",
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Positional argument",
    )


def execute(args: argparse.Namespace) -> int:
    """Execute the command. Returns an exit code (0-3)."""
    if args.my_flag:
        print(f"Flag is set, target={args.target}")
    else:
        print("Running with defaults")
    return 0  # EXIT_SUCCESS
```

### Rules

1. **One file = one command.** File name matches the command name
   (`my_command.py` → `ohm my-command`).
2. **`register()` is the entry point.** The registry calls it automatically.
3. **`execute()` returns an int.** Use constants from
   `ohm.cli.registry`: `EXIT_SUCCESS`, `EXIT_GENERAL_ERROR`,
   `EXIT_USAGE_ERROR`, `EXIT_RUNTIME_ERROR`.
4. **Output goes to stdout.** Errors and diagnostics go to stderr.
5. **No side effects at import time.** All logic lives inside `execute()`.

### File Structure

```
src/ohm/
├── __init__.py              # __version__
├── cli/
│   ├── main.py              # Entry point: parse → dispatch → exit
│   ├── registry.py          # Registry, parser builder, exit codes
│   ├── app.py               # TUI application (Textual)
│   └── widgets/             # TUI widgets
├── commands/
│   ├── __init__.py          # Auto-discovery via pkgutil
│   ├── base.py              # BaseCommand ABC (optional)
│   ├── run.py               # ohm run
│   ├── goal.py              # ohm goal
│   ├── loop.py              # ohm loop
│   ├── test_cmd.py          # ohm test
│   ├── init.py              # ohm init
│   ├── status.py            # ohm status
│   └── config.py            # ohm config
└── core/
    ├── agent.py             # Agent logic
    ├── provider.py          # LLM provider abstraction
    └── models.py            # Data models
```

### Entry Point

Registered in `pyproject.toml`:

```toml
[project.scripts]
ohm = "ohm.cli.main:main"
```

---

## Stdio Contract

| Stream | Content |
|--------|---------|
| **stdout** | Command output (responses, status, JSON) |
| **stderr** | Errors, diagnostics, warnings |
| **stdin** | Interactive prompts (future), piped input |

Commands that produce machine-readable output (e.g. `ohm status --json`) write
only JSON to stdout with no extra text. Human-readable output is not guaranteed
to be stable — use `--json` for scripting.
