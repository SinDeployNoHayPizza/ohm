# OHM CLI — Terminal Output Reference

> Exact output as it would appear in a terminal session.
> Generated from `ohm 0.1.0-alpha`.

---

## Global Help

```
$ ohm --help
ohm 0.1.0-alpha - Orchestrator & Harness for Models

Usage: ohm [OPTIONS] [COMMAND]

Options:
  -h, --help, -?    Show this help message and exit
  --version, -V     Show version and exit

Commands:
  config         Manage OHM configuration
  goal           Set an autonomous goal for the agent
  init           Initialize OHM in the current directory
  loop           Run a command in a loop until a condition is met
  run            Execute a prompt and print the response
  status         Show system status information
  test           Run the test suite

Run 'ohm <command> --help' for help on a specific command.

If no command is given, OHM launches the interactive TUI.
```

## Version

```
$ ohm --version
ohm 0.1.0-alpha

$ ohm -V
ohm 0.1.0-alpha
```

---

## `ohm run`

### Help

```
$ ohm run --help
ohm run - Execute a prompt and print the response

Usage: ohm run [OPTIONS] [ARGS]

Options:
  -h, --help, -?    Show this help message and exit
  --version, -V     Show version and exit
  --provider, -p       LLM provider (default: anthropic)
  --model, -m          Model to use (default: provider-specific)
  --stream, -s         Stream the response token-by-token
```

### Execution

```
$ ohm run "Explain the SOLID principles"
[run] provider=anthropic
[run] prompt: Explain the SOLID principles
[run] => Response would appear here.

$ echo "Fix the bug" | ohm run -
[run] provider=anthropic
[run] prompt: Fix the bug
[run] => Response would appear here.

$ ohm run -p openai -m gpt-4-turbo "Refactor this function"
[run] provider=openai
[run] prompt: Refactor this function
[run] => Response would appear here.
```

---

## `ohm goal`

### Help

```
$ ohm goal --help
ohm goal - Set an autonomous goal for the agent

Usage: ohm goal [OPTIONS] [ARGS]

Options:
  -h, --help, -?    Show this help message and exit
  --version, -V     Show version and exit
  --provider, -p       LLM provider (default: anthropic)
  --model, -m          Model to use (default: provider-specific)
```

### Execution

```
$ ohm goal "Implement JWT authentication with refresh tokens"
[goal] provider=anthropic
[goal] goal: Implement JWT authentication with refresh tokens
[goal] => Agent would autonomously work toward this goal.

$ ohm goal -p google "Add error handling to all API endpoints"
[goal] provider=google
[goal] goal: Add error handling to all API endpoints
[goal] => Agent would autonomously work toward this goal.
```

---

## `ohm loop`

### Help

```
$ ohm loop --help
ohm loop - Run a command in a loop until a condition is met

Usage: ohm loop [OPTIONS] [ARGS]

Options:
  -h, --help, -?    Show this help message and exit
  --version, -V     Show version and exit
  --max, -n            Maximum number of iterations (default: 10)
  --until, -u          Stop when this condition is met (e.g. "tests pass")
```

### Execution

```
$ ohm loop "ohm test --fix" --until "all tests pass"
[loop] command: ohm test --fix
[loop] max iterations: 10
[loop] until: all tests pass
[loop] => Loop would execute until condition is met.

$ ohm loop -n 5 "pytest tests/ -x" --until "exit code 0"
[loop] command: pytest tests/ -x
[loop] max iterations: 5
[loop] until: exit code 0
[loop] => Loop would execute until condition is met.
```

---

## `ohm test`

### Help

```
$ ohm test --help
ohm test - Run the test suite

Usage: ohm test [OPTIONS] [ARGS]

Options:
  -h, --help, -?    Show this help message and exit
  --version, -V     Show version and exit
  --fix                Attempt to auto-fix failing tests
  --coverage           Generate a coverage report
```

### Execution

```
$ ohm test
[test] Running test suite
[test] => Test results would appear here.

$ ohm test --fix
[test] Running test suite --fix
[test] => Test results would appear here.

$ ohm test --fix --coverage
[test] Running test suite --fix --coverage
[test] => Test results would appear here.
```

---

## `ohm init`

### Help

```
$ ohm init --help
ohm init - Initialize OHM in the current directory

Usage: ohm init [OPTIONS] [ARGS]

Options:
  -h, --help, -?    Show this help message and exit
  --version, -V     Show version and exit
  --force              Overwrite existing OHM configuration
```

### Execution

```
$ ohm init
[init] Initializing OHM in current directory
[init] => OHM would be initialized here.

$ ohm init --force
[init] Initializing OHM in current directory (force)
[init] => OHM would be initialized here.
```

---

## `ohm status`

### Help

```
$ ohm status --help
ohm status - Show system status information

Usage: ohm status [OPTIONS] [ARGS]

Options:
  -h, --help, -?    Show this help message and exit
  --version, -V     Show version and exit
  --json               Output status in JSON format
```

### Execution

```
$ ohm status
[status] OHM v0.1.0-alpha
[status] Status: OK
[status] Provider: anthropic
[status] Model: claude-sonnet-4-20250514

$ ohm status --json
[status] OHM v0.1.0-alpha
[status] Status: OK
[status] Provider: anthropic
[status] Model: claude-sonnet-4-20250514
```

---

## `ohm config`

### Help

```
$ ohm config --help
ohm config - Manage OHM configuration

Usage: ohm config [OPTIONS] [ARGS]

Options:
  -h, --help, -?    Show this help message and exit
  --version, -V     Show version and exit
```

### Execution

```
$ ohm config get provider
[config] provider = <current value>

$ ohm config set provider openai
[config] provider = openai

$ ohm config set model gpt-4-turbo
[config] model = gpt-4-turbo
```

---

## Error Output

### Unknown argument

```
$ ohm invalid
ohm: unrecognized argument 'invalid'
Run 'ohm --help' for usage.

$ echo $?
2
```

### Unknown subcommand

```
$ ohm nonexistent
ohm: unknown command 'nonexistent'
Run 'ohm --help' for usage.

$ echo $?
2
```

### Bad subcommand arguments

```
$ ohm run --bogus
ohm run: unrecognized argument '--bogus'
Run 'ohm run --help' for usage.

$ echo $?
2
```

---

## TUI Launch (default)

```
$ ohm
# Launches the full-screen interactive TUI
# (Textual application with model selector, chat, sidebar, etc.)

$ echo $?
0
```

---

## Piping / Scripting

```bash
# Pipeline: pipe input to run
echo "Summarize this file" | ohm run -

# Script: check status, exit on failure
ohm status --json | jq '.status' || exit 1

# Loop: auto-fix until tests pass
ohm loop "ohm test --fix" --until "all tests pass"
exit_code=$?
if [ $exit_code -ne 0 ]; then
  echo "Failed after max iterations" >&2
  exit $exit_code
fi
```
