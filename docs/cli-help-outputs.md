```
$ ohm --help
ohm 0.1.0-alpha — Orchestrator & Harness for Models

Usage: ohm [OPTIONS] [COMMAND]

Options:
  -h, --help, -?         Show this help message and exit
  --version, -V          Show version and exit
  -v, --verbose          Enable verbose output
  --provider, -p NAME    Override default LLM provider
  --model, -m NAME       Override default model
  --json                 Output in JSON format (where supported)
  --no-color             Disable colored output

Commands:
  cron        Manage scheduled tasks (list, add, remove, pause, resume)
  doctor      Check environment health and configuration
  goal        Set an autonomous goal for the agent
  init        Initialize OHM in the current directory
  loop        Run a command in a loop until a condition is met
  mcp         Manage MCP server connections (list, add, remove, status)
  plugin      Manage plugins (list, install, remove, info)
  run         Execute a prompt and print the response
  serve       Run OHM as an HTTP API server (headless mode)
  skills      Manage agent skills (list, install, remove, search)
  status      Show system status information
  test        Run the test suite

Run 'ohm <command> --help' for help on a specific command.
If no command is given, OHM launches the interactive TUI.

Examples:
  ohm run "Explain the SOLID principles"
  ohm goal -p openai "Implement auth system"
  ohm test --fix --coverage
  ohm status --json
  ohm config set provider anthropic
  ohm loop "ohm test --fix" --until "all tests pass"
  ohm doctor
  ohm skills list
  ohm mcp list
  ohm cron list
  ohm plugin list
  ohm serve --port 9000
```
