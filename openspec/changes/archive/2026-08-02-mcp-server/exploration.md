# Exploration: MCP Server Implementation

> SDD explore artifact for change `mcp-server` (Phase 2 Core Engine roadmap item, README line 560).
> Scope: investigate current MCP/serve surface and propose what a Stage 1 MCP server should provide. Exploration only — no code modified.

## Curiosity Map

- How is the `mcp` Python SDK used in the codebase today (server, client, or not at all)?
- What does `ohm serve` actually do today vs what the README promises (`ohm serve --protocol mcp --port 3000`)?
- What is `ohm mcp` today, and what is its relationship to `serve`?
- Which OHM core capabilities would an MCP server expose as tools/resources (agent run/stream, sessions, skills, providers, config, status)?
- What FastMCP surface does the installed SDK expose (tools, resources, prompts, transports, test hooks)?
- Where would MCP server config live in the existing config system?
- How does the CLI registry work, so new `serve --protocol mcp` wiring follows conventions?
- What tests exist for serve/mcp today?

## Current State

### 1. MCP SDK — dependency present, zero usage

- `pyproject.toml:9` declares `mcp[cli]>=1.28.1` as a direct dependency; installed version is **1.28.1**.
- **Zero imports** of `mcp` anywhere in `src/` or `tests/` (grep for `import mcp` / `from mcp` → no matches). The dependency is dormant — installed but unused.
- The `cli` extra is fully installed: `uvicorn`, `sse_starlette`, `starlette`, `fastmcp`, `mcp.server.sse`, `mcp.server.streamable_http` all importable. HTTP transports require no new dependencies.
- FastMCP (`mcp.server.fastmcp.FastMCP`) is available with the full surface:
  - `@mcp.tool(name, title, description, ...)` decorator + `add_tool`/`remove_tool`
  - `@mcp.resource(...)` + `add_resource` (resources and templates)
  - `@mcp.prompt(...)` + `add_prompt`
  - `run(transport='stdio'|'sse'|'streamable-http')`, `run_stdio_async()`, `run_streamable_http_async()`, `run_sse_async()`
  - In-process test hooks: `call_tool()`, `list_tools()`, `read_resource()`, `list_resources()`, `list_prompts()` — these make strict-TDD unit testing possible with no network/server process.
  - `__init__(host='127.0.0.1', port=8000, mount_path='/', streamable_http_path='/mcp', ...)` — streamable HTTP endpoint defaults to `/mcp` on port 8000.

### 2. `ohm serve` — print placeholder, NO `--protocol` flag

`src/ohm/commands/serve.py` (59 lines) registers `serve` with `--host` (default `127.0.0.1`), `--port` (default `8080`), `--workers`, `--reload`, then **prints** the endpoints it would serve: `POST /v1/run`, `POST /v1/goal`, `GET /v1/status`, `GET /v1/health`, `GET /v1/models`. It is a REST-API placeholder, not an MCP surface.

**README:251 promises `ohm serve --protocol mcp --port 3000` — this flag does not exist.** The `--protocol` flag is pure documentation today; implementing MCP server must either add the flag to `serve.py` or correct the README (a contract deviation).

### 3. `ohm mcp` — client-side connection manager placeholder

`src/ohm/commands/mcp.py` (73 lines) registers `mcp` with subcommands `list`, `add`, `remove`, `status`, `connect` — all `print` placeholders. Semantics are **client-side**: managing MCP servers OHM connects TO (docs/configuration.md:219-233 documents `mcp:` config with `command`/`args`/`url` entries). `mcp.py` does NOT serve MCP.

### 4. Config surface

- `OHMConfig.mcp: dict[str, Any] = field(default_factory=dict)` (`core/config.py:149`) with default `{}` (`DEFAULTS["mcp"]`, line 52) — serialized via `to_dict()` (line 201) and merged in `load_config` (line 277).
- Docs document `mcp:` as **client-side** server registrations. There is **no server-side MCP config** (transport/host/port/path) anywhere.
- Config priority: env (`OHM_*`) > project `.ohm/config.yaml` > global `~/.ohm/config.yaml` > built-in defaults.

### 5. OHM capabilities available to expose

| Capability | Source | Notes |
|---|---|---|
| Run a prompt | `core/agent.py:221` `Agent.run(prompt)` → `AgentResponse` (content, tokens_used, latency_ms, success, error) | Async-safe (wraps strands in `run_in_executor`); per-call `AgentConfig(provider, model, system_prompt, tools, base_url)` |
| Stream a prompt | `core/agent.py:263` `Agent.stream(prompt)` — async iterator of event dicts | Strands event shape (`contentBlockDelta`); streaming over MCP needs progress notifications (defer) |
| Run a goal | `commands/goal.py:36` `GOAL_SYSTEM_PROMPT` + `Agent.run` | Established pattern for autonomous-goal prompts |
| Status | `commands/status.py:84-104` real status dict: version, provider, model, provider API-key status, session count, strands/textual availability, metrics snapshot | Reusable logic; `--json` shape exists |
| List/get sessions | `commands/session.py:71-170` `_list_session_files()`, `_load_session()`, `_load_last_session()` — persisted JSON in `~/.ohm/sessions/` | Read-only data → natural MCP **resources** |
| List/get skills | `core/skills/registry.py` `SkillRegistry.list_skills()/get_skill()`; loader discovers from skill paths | Read-only → resources or tools |
| Providers/models | `core/provider.py` `KNOWN_PROVIDERS`, `PROVIDER_CATALOG`, `resolve_context_window()` | Catalog is static data |
| Config | `core/config.py` `get_config()` / `OHMConfig.to_dict()` | `to_dict()` already JSON-ready |

### 6. CLI registry conventions

- Auto-discovery: `commands/__init__.py:register_all` imports every module in `src/ohm/commands/` and calls its `register(registry)`.
- Each subcommand module = one file with `register(registry)` + `register_args`/`add_arguments` + `handler(args) -> int`.
- **Parity constraint**: `tests/test_cli.py:411-420` asserts `CLI_TUI_MAPPING` TUI_IRRELEVANT set is EXACTLY `{"doctor", "mcp", "cron", "init", "serve", "plugin", "--version", "-h"}`. Adding a NEW top-level subcommand breaks this test and requires updating `CLI_TUI_MAPPING` + `docs/cli-help-outputs.md`. Adding `serve` as a **sub-subcommand of the existing `mcp` command** touches none of those.
- `docs/cli-help-outputs.md` is the golden help output; any help-text change must be reflected there.
- `mcp` and `serve` are both already `TUI_IRRELEVANT` in the mapping.

### 7. Existing tests

- No tests exist for `serve.py` or `mcp.py` (grep for `serve|mcp` in tests → only the parity test line).
- Established TDD patterns: `monkeypatch` + `FakeStrandsAgent` (`tests/test_agent.py:290`) and agent factory injection (`tests/test_commands.py:40-48` `monkeypatch.setattr("ohm.core.agent.Agent", factory)`) — the same pattern applies to MCP tool tests.
- Branch state: `feature/mcp-server` checked out, HEAD `b6e7155` (v0.1.11 bump). Clean tree.
- OpenSpec specs today: observability, provider-abstraction, provider-config, skills-registry, tui-commands (no mcp spec yet → new `openspec/specs/mcp-server/spec.md` on archive).

## Affected Areas

- `src/ohm/commands/mcp.py` — add `serve` sub-subcommand (transport/port/host args) dispatching to the FastMCP core; keep client-side placeholder subcommands intact.
- `src/ohm/commands/serve.py` — add `--protocol mcp` flag routing to the same FastMCP core (honors README:251); REST placeholder path preserved for future REST work.
- `src/ohm/core/mcp_server.py` (NEW) — FastMCP server builder: tool/resource registration + `run_stdio_async()` / `run_streamable_http_async()` entry points; the single source of truth for both CLI surfaces.
- `src/ohm/core/config.py` — optional server config section (e.g. `mcp_server: {transport, host, port, path}`); must not collide with client-side `mcp:` semantics.
- `tests/` — NEW `tests/test_mcp_server.py` (tool registration, `call_tool` behavior with fake agent, resource reads, config-driven transport args) + CLI tests for `mcp serve` and `serve --protocol mcp` arg parsing; update `docs/cli-help-outputs.md` if help text changes.
- `pyproject.toml` — unchanged (mcp[cli] already present).
- `README.md:251` — must stay true; `docs/configuration.md` — document server-side config section if added.

## Approaches

1. **A — FastMCP core module + `ohm mcp serve` subcommand** — New `core/mcp_server.py` builds a FastMCP instance exposing OHM as tools (`run_prompt`, `run_goal`, `get_status`, `list_sessions`, `get_session`, `list_skills`, `get_skill`, `list_models`, `get_config`) with optional session resources; `mcp.py` gains `serve` sub-subcommand with `--transport stdio|http`, `--host`, `--port`. stdio default (local MCP clients: Claude Desktop, opencode).
   - Pros: stdio-first is the most universal client story; in-process `call_tool()` enables clean strict-TDD; no parity-test churn; `mcp` command is the natural home; config plumbing optional in Stage 1.
   - Cons: README promise (`ohm serve --protocol mcp`) stays unfulfilled unless `serve` also routes here.
   - Effort: **Medium** (~250-400 lines with tests).

2. **B — Wire `ohm serve --protocol mcp`** — Add `--protocol {http,mcp}` to `serve.py`; `--protocol mcp` launches FastMCP instead of printing REST endpoints.
   - Pros: fulfills the README promise exactly; `--port 3000` maps to FastMCP's `port`.
   - Cons: couples two server philosophies (REST API vs MCP) into one command whose help text says "HTTP API server"; stdio transport has no natural home here (`serve` implies network); conflation grows messy when the REST surface is real.
   - Effort: **Low** for the flag + dispatch, but architecturally muddier.

3. **C — Both: `ohm mcp serve` AND `ohm serve --protocol mcp` alias** — Implement the FastMCP core once (approach A), then add `--protocol mcp` to `serve.py` as a thin alias that constructs the same core with the given host/port.
   - Pros: primary UX is `ohm mcp serve` (stdio default for agent clients), README promise honored via the alias; single source of truth; `serve --protocol mcp --port 3000` works as documented.
   - Cons: two CLI entry points to document/test; slight surface duplication (both thin).
   - Effort: **Medium** (core + two thin dispatchers).

## Recommendation

**Approach C — implement the FastMCP core once, expose it two ways.** Recommended shape for Stage 1:

1. **`src/ohm/core/mcp_server.py`** — builds a `FastMCP` instance with:
   - Tools: `run_prompt(prompt, provider?, model?, system_prompt?)` → AgentResponse fields; `run_goal(goal, provider?, model?)`; `get_status()`; `list_sessions()`; `get_session(session_id)`; `list_skills()`; `get_skill(name)`; `list_models(provider?)`; `get_config()`.
   - Resources (read-only data, Stage 1 optional): `ohm://sessions/{session_id}` template + `ohm://status` — sessions/skills are read-only data and map naturally.
   - `build_mcp_server(agent_factory=...)` with an injectable agent factory so strict-TDD tests use a fake agent (existing `test_commands.py` pattern) — no API keys in tests.
   - `run_stdio()` / `run_http(host, port)` entry points delegating to `run_stdio_async()` / `run_streamable_http_async()`.
2. **`src/ohm/commands/mcp.py`** — add `serve` sub-subcommand: `ohm mcp serve [--transport stdio|http] [--host 127.0.0.1] [--port 3000]`. stdio default. No parity-test changes (sub-subcommand of existing `mcp`).
3. **`src/ohm/commands/serve.py`** — add `--protocol {http,mcp}` (default `http`, preserving today's placeholder behavior). `--protocol mcp` routes to the same `core/mcp_server.py` with host/port — fulfilling README:251 `ohm serve --protocol mcp --port 3000`.
4. **Streaming deferred to Stage 2** — MCP tools are request/response; token streaming would require progress notifications. Stage 1 `run_prompt` returns the complete `AgentResponse.content`. Non-streaming keeps the diff inside the review budget.
5. **Client-side `ohm mcp {list|add|remove|status|connect}` stays a placeholder** — real client-side connection management is a separate change; don't scope-creep it in.

Rationale: the SDK is already a direct dependency with HTTP extras installed; FastMCP's in-process `call_tool()` gives a real strict-TDD story without network or API keys; the sub-subcommand avoids the CLI parity test; and the `serve --protocol mcp` alias honors the documented contract at near-zero extra cost. Exposing OHM as tools (run/goal/status/sessions/skills/models/config) is exactly what an MCP client (Claude, opencode, etc.) needs to drive OHM.

## Risks

- **CRITICAL — tools must not require live API keys in tests**: `Agent.run` hits real providers. Every tool must take an injectable agent factory (existing monkeypatch pattern) or tests fail without `ANTHROPIC_API_KEY`. `run_prompt` must also return a clean error result when the provider is unconfigured, not crash the MCP session.
- **WARNING — README contract**: `ohm serve --protocol mcp` is documented (README:251); if the `--protocol` flag is NOT added to `serve.py`, the README must be corrected instead — a documented deviation that review will flag.
- **WARNING — CLI parity test**: adding a new top-level subcommand requires updating `CLI_TUI_MAPPING` (`core/commands.py:283`), the parity test (`tests/test_cli.py:411-420`), and `docs/cli-help-outputs.md`. Adding `serve` under `mcp` avoids all three.
- **WARNING — config semantics collision**: the existing `mcp:` key is documented client-side (docs/configuration.md:219). A server config section must use a distinct name (e.g. `mcp_server:`) or explicitly extend `mcp:` with a clear sub-key — silently reusing `mcp:` would break the documented client config.
- **WARNING — concurrency/state model**: Agent is per-call; `session.py` persistence is file-based and global (not per MCP connection). Decide in spec: stateless tools (each call a fresh Agent) vs session-scoped continuation. Recommendation: stateless in Stage 1, session continuation via explicit `session_id` parameter later.
- **WARNING — HTTP default port mismatch**: FastMCP default port is 8000; README documents 3000. The dispatcher must pass `--port` through explicitly rather than relying on FastMCP defaults.
- **WARNING — PR budget**: core module + two thin CLI dispatchers + tests should fit the 400-line budget if streaming/resources/prompts are kept minimal; slicing option: (1) core + tools + tests, (2) CLI wiring + docs.

## Open Questions (for proposal/spec)

1. Exact tool list — include all nine above, or trim (e.g. defer `list_models`/`get_config`)?
2. Resources in Stage 1 (session/status) or tools only?
3. Streaming: defer to Stage 2 (recommended) or include progress notifications now?
4. Server config section: new `mcp_server:` key vs extending `mcp:` — or CLI-args-only for Stage 1 (recommended: CLI-args-only, config later)?
5. Keep `ohm mcp` client-side subcommands as placeholders in this change (recommended) or also wire them to real config?
6. Auth on HTTP transport (FastMCP supports `auth_server_provider`) — out of scope for Stage 1?

## Ready for Proposal

Yes. Evidence is complete: the MCP SDK is installed and unused, both CLI surfaces are print placeholders, the README promise is unfulfilled, and the core capabilities (Agent, sessions, skills, providers, config, status) are all real and injectable for testing. The orchestrator should tell the user the recommended shape — FastMCP core module + `ohm mcp serve` (stdio default) + `serve --protocol mcp` alias honoring README:251 — and ask the open questions above, especially streaming deferral and whether the session/skills resources are in scope.
