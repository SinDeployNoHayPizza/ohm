# OHM Configuration Guide

How OHM loads, merges, and uses configuration from multiple sources.

## Configuration Hierarchy

OHM merges config from 4 sources. Highest priority wins:

```
Environment variables (OHM_*)
  └─> Project config (.ohm/config.yaml)
      └─> Global config (~/.ohm/config.yaml)
          └─> Built-in defaults
```

**Example**: If global config sets `provider: anthropic` but your `.env` has `OHM_PROVIDER=openai`, OHM uses `openai`.

## Quick Start

```bash
# 1. Copy the example env file
cp example.env .env

# 2. Edit .env with your API keys
# ANTHROPIC_API_KEY=sk-ant-...

# 3. Initialize project config
ohm init

# 4. Verify everything works
ohm doctor
```

## File Locations

| File | Purpose | Tracked in Git? |
|------|---------|-----------------|
| `~/.ohm/config.yaml` | Global defaults for all projects | No (user home) |
| `.ohm/config.yaml` | Project-specific overrides | No (in `.gitignore`) |
| `.env` | API keys and secrets | No (in `.gitignore`) |
| `example.env` | Reference template for `.env` | **Yes** |

## Configuration Files

### Global Config (`~/.ohm/config.yaml`)

Your personal defaults across all projects:

```yaml
provider: anthropic
model: claude-sonnet-4-6
max_tokens: 4096
temperature: 0.7
sandbox: true
tools:
  - file_read
  - file_write
  - editor
  - calculator
  - current_time
  - http_request
  - think
```

### Project Config (`.ohm/config.yaml`)

Project-specific overrides. Created with `ohm init`:

```yaml
# This project uses Gemini for cost efficiency
provider: gemini
model: gemini-2.5-flash
temperature: 0.3

# Custom tools for this project
tools:
  - file_read
  - file_write
  - editor
  - calculator
  - http_request
```

### Environment Variables (`.env`)

API keys and runtime settings. Never commit this file.

```env
# API Keys
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-proj-...
GEMINI_API_KEY=AIza...

# OHM overrides (optional)
OHM_PROVIDER=anthropic
OHM_MODEL=claude-sonnet-4-6
OHM_LOG_LEVEL=DEBUG
```

## Config Keys Reference

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `provider` | string | `anthropic` | LLM provider to use |
| `model` | string | `claude-sonnet-4-6` | Model ID (provider-specific) |
| `max_tokens` | int | `4096` | Max tokens to generate |
| `temperature` | float | `0.7` | Randomness (0=deterministic, 1=creative) |
| `sandbox` | bool | `true` | Run tools in sandbox mode |
| `system_prompt` | string | `null` | Custom system prompt override |
| `tools` | list | See below | Tools to load from strands_tools |
| `mcp` | dict | `{}` | MCP server configurations |
| `log_level` | string | `INFO` | Logging level |

## Providers

### Anthropic (Claude)

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
```

Models: `claude-sonnet-4-6`, `claude-sonnet-4-20250514`, `claude-3-opus-20240229`

### OpenAI (GPT)

```env
OPENAI_API_KEY=sk-proj-...
```

Models: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`

### Google Gemini

```env
GEMINI_API_KEY=AIza...
```

Models: `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-2.0-flash`

### Amazon Bedrock

Uses AWS credentials (not a single key):

```env
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1
```

Models: `global.anthropic.claude-sonnet-4-6`

### Ollama (Local)

No API key needed. Just install and run Ollama:

```bash
ollama pull llama3.2
```

```env
OLLAMA_HOST=http://localhost:11434
```

Models: `llama3.2`, `mistral`, `codellama`

## Tools

Default tools loaded on Windows:

| Tool | Description |
|------|-------------|
| `file_read` | Read files from disk |
| `file_write` | Write/create files |
| `editor` | Edit files with search/replace |
| `calculator` | Math operations |
| `current_time` | Get date/time |
| `http_request` | Make HTTP calls |
| `think` | Deep reasoning |

Additional tools on Linux/macOS: `shell`, `python_repl`

Override in config:

```yaml
tools:
  - file_read
  - file_write
  - calculator
  # Add/remove as needed
```

## CLI Commands

```bash
# Show resolved config
ohm config show

# Get a specific value
ohm config get provider

# Set a value (writes to global config)
ohm config set provider gemini
ohm config set temperature 0.3

# Show config file locations
ohm config path

# Initialize project config
ohm init

# Initialize global config
ohm init --global

# Check environment health
ohm doctor
ohm doctor --json
```

## MCP Server Configuration

Add MCP servers in your config:

```yaml
mcp:
  codegraph:
    command: codegraph
    args: ["serve"]
  context7:
    url: http://localhost:3001
  custom-server:
    command: python
    args: ["-m", "my_mcp_server"]
```

### OHM as an MCP Server

To run OHM itself as an MCP server, use the `mcp_server` section — distinct
from the client-side `mcp:` key above:

```yaml
mcp_server:
  transport: stdio   # or http
  host: 127.0.0.1    # used by the http transport
  port: 3000         # used by the http transport
```

Start the server with:

```bash
ohm mcp serve                        # stdio transport (default)
ohm mcp serve --transport http --port 3000
ohm serve --protocol mcp --port 3000 # alias
```

Any omitted keys fall back to the defaults (`stdio`, `127.0.0.1`, `3000`),
and explicit CLI flags always win over the config.

## Troubleshooting

**Config not loading?**
```bash
ohm doctor          # Check config status
ohm config path     # See expected locations
ohm config show     # See resolved values
```

**Wrong provider being used?**
```bash
ohm config show | grep provider   # Check resolved provider
echo $OHM_PROVIDER                # Check env override
```

**API key not found?**
```bash
ohm doctor --json    # Check which keys are detected
# Keys are loaded from:
#   1. os.environ (already set in shell)
#   2. .env file in current directory
#   3. example.env is NOT loaded (it's a template)
```
