# Delta for mcp-server

New capability (no existing `openspec/specs/mcp-server/spec.md`). Adds the MCP server surface: FastMCP core with injectable agent factory, 7 stateless tools, stdio/HTTP transports, `ohm mcp serve` + `ohm serve --protocol mcp` wiring, and a `mcp_server:` config section. No modified, removed, or renamed requirements.

## ADDED Requirements

### Requirement: Server Builder with Injectable Agent Factory (MCP-1)

`build_mcp_server(agent_factory=...)` MUST return a configured FastMCP instance; tools MUST resolve agents through the injected factory, and MUST NOT require live API keys. The default factory MUST construct production agents from OHMConfig.

#### Scenario: Fake factory injected

- GIVEN a test injecting a fake agent factory into `build_mcp_server`
- WHEN a tool that runs an agent is invoked
- THEN the fake factory is called and no API key is required

#### Scenario: Default factory

- GIVEN `build_mcp_server()` with no factory argument
- WHEN the server is built
- THEN the default factory constructs agents from OHMConfig

### Requirement: Tool Registration (MCP-2)

The server MUST register exactly seven tools: `run_prompt`, `run_goal`, `get_status`, `list_sessions`, `get_session`, `list_skills`, `list_models`. It MUST NOT register resources, prompts, subscriptions, or config-mutation tools in Stage 1. All tools MUST be stateless.

#### Scenario: Seven tools listed

- GIVEN a built server
- WHEN `list_tools` is called
- THEN exactly the seven named tools are returned

#### Scenario: No resources or prompts

- GIVEN a built server
- WHEN `list_resources` and `list_prompts` are called
- THEN both return empty lists

### Requirement: run_prompt Tool (MCP-3)

`run_prompt` MUST accept a prompt and optional provider/model/system_prompt arguments, run it through the agent factory, and return AgentResponse fields (content, tokens_used, latency_ms, success, error).

#### Scenario: Successful run

- GIVEN a configured provider
- WHEN `run_prompt` is called with a prompt
- THEN the result contains response content, token usage, latency, and success=true

#### Scenario: Unconfigured provider

- GIVEN no API key for the default provider
- WHEN `run_prompt` is called
- THEN the result has success=false and a descriptive error message

### Requirement: run_goal Tool (MCP-4)

`run_goal` MUST accept a goal and optional provider/model arguments, run the established autonomous-goal loop, and return AgentResponse fields.

#### Scenario: Goal completes

- GIVEN a configured provider
- WHEN `run_goal` is called with a goal
- THEN the result reports the goal outcome with success=true

#### Scenario: Goal with unconfigured provider

- GIVEN no API key
- WHEN `run_goal` is called
- THEN the result has success=false and a descriptive error message

### Requirement: get_status Tool (MCP-5)

`get_status` MUST return current OHM status: version, provider, model, provider API-key status, and session count.

#### Scenario: Status returned

- GIVEN a built server
- WHEN `get_status` is called
- THEN the result contains version, provider, model, and session count fields

### Requirement: Sessions Tools (MCP-6)

`list_sessions` MUST return persisted session identifiers; `get_session` MUST return the requested session's content or a clean error result when it does not exist.

#### Scenario: Sessions listed

- GIVEN persisted sessions in the session store
- WHEN `list_sessions` is called
- THEN the result contains those session identifiers

#### Scenario: Missing session

- GIVEN a session id that does not exist
- WHEN `get_session` is called with that id
- THEN the result is a clean error (success=false, descriptive message)

### Requirement: Skills and Models Tools (MCP-7)

`list_skills` MUST return skills from the skill registry; `list_models` MUST return the provider catalog, optionally filtered by provider.

#### Scenario: Skills returned

- GIVEN a registry with known skills
- WHEN `list_skills` is called
- THEN the result contains the registered skill names

#### Scenario: Models filtered by provider

- GIVEN a provider filter
- WHEN `list_models` is called with that provider
- THEN the result contains only models for that provider

### Requirement: Stdio Transport (MCP-8)

The server MUST provide a `run_stdio()` entry point; `ohm mcp serve` MUST use stdio when `--transport` is omitted.

#### Scenario: Default stdio

- GIVEN `ohm mcp serve` with no transport flag
- WHEN the command runs
- THEN the stdio transport starts and answers MCP requests on stdin/stdout

### Requirement: HTTP Transport with Explicit Port (MCP-9)

The server MUST provide `run_http(host, port)` over streamable HTTP. CLI dispatchers MUST pass the port explicitly — never rely on the FastMCP default (8000), which differs from the documented 3000.

#### Scenario: Documented port honored

- GIVEN `ohm mcp serve --transport http --port 3000` or `ohm serve --protocol mcp --port 3000`
- WHEN the command runs
- THEN the HTTP transport binds port 3000

#### Scenario: Port from config

- GIVEN `mcp_server: {transport: http, port: 3000}` and no --port flag
- WHEN `ohm mcp serve` runs
- THEN the HTTP transport binds the configured port

### Requirement: serve --protocol mcp Alias (MCP-10)

`ohm serve --protocol mcp` MUST route to the same core server with the given host/port, honoring README:251. Without `--protocol mcp`, `ohm serve` MUST keep today's behavior.

#### Scenario: Alias starts MCP server

- GIVEN `ohm serve --protocol mcp --port 3000`
- WHEN the command runs
- THEN an MCP server starts on port 3000

#### Scenario: Default protocol unchanged

- GIVEN `ohm serve` without --protocol mcp
- WHEN the command runs
- THEN behavior is unchanged from today

### Requirement: mcp_server Config Section (MCP-11)

OHMConfig MUST support a server-side `mcp_server:` section (transport, host, port) distinct from the client-side `mcp:` key. CLI arguments MUST override config values.

#### Scenario: Config drives server

- GIVEN `mcp_server: {transport: http, port: 3000}` in config
- WHEN `ohm mcp serve` runs without transport/port flags
- THEN the server uses transport http and port 3000

#### Scenario: CLI overrides config

- GIVEN `mcp_server: {port: 3000}` in config and `--port 4000` on the CLI
- WHEN `ohm mcp serve --transport http --port 4000` runs
- THEN port 4000 is used

### Requirement: Error Isolation (MCP-12)

No tool MUST raise an exception that terminates the MCP session; every failure (unconfigured provider, missing session, invalid argument) MUST surface as a clean error result and leave the server responsive.

#### Scenario: Session survives a tool error

- GIVEN an unconfigured provider
- WHEN `run_prompt` fails cleanly and `get_status` is called next
- THEN the second call succeeds on the same server
