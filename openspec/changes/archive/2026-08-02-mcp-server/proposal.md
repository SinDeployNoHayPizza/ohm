# Proposal: MCP Server — Stage 1

## Intent

Expose OHM as a Model Context Protocol server so agent clients (Claude Desktop, opencode) can drive it. Today `mcp[cli]` is an unused dependency, `ohm mcp` is a client-side placeholder, and README:251 promises `ohm serve --protocol mcp --port 3000`, which doesn't exist. OHM must be an MCP provider, not just a consumer.

## Scope

### In Scope
- `src/ohm/core/mcp_server.py` (NEW): FastMCP builder with injectable agent factory; tools `run_prompt`, `run_goal`, `get_status`, `list_sessions`, `get_session`, `list_skills`, `list_models`; `run_stdio()` / `run_http()` entry points.
- `ohm mcp serve` sub-subcommand (stdio default; `--transport`, `--host`, `--port`).
- `serve --protocol mcp` alias routing to the same core (honors README:251); `--port` passed explicitly (FastMCP default 8000 ≠ README 3000).
- `mcp_server:` config section (`transport`/`host`/`port`) in OHMConfig — distinct from client-side `mcp:`.
- Tests (`tests/test_mcp_server.py`, fake agent, no API keys) + CLI arg-parsing tests; docs updates.

### Out of Scope
- Token streaming (progress notifications), MCP resources/subscriptions, `get_config`/`get_skill` tools, config-mutation tools, HTTP auth — deferred to Stage 2.
- Client-side `ohm mcp {list|add|remove|status|connect}` — stays placeholder.

## Capabilities

### New Capabilities
- `mcp-server`: FastMCP core, tool surface, transports, `mcp serve` / `serve --protocol mcp` wiring, `mcp_server:` config.

### Modified Capabilities
- None — existing requirements unchanged; tools compose `provider-abstraction`, `skills-registry`, `observability` logic.

## Approach

Approach C (from exploration): one FastMCP core module, two thin CLI dispatchers. `build_mcp_server(agent_factory=...)` — tools call the injected factory (existing monkeypatch pattern) so tests need no API keys. `run_prompt`/`run_goal` catch unconfigured-provider errors and return a clean error result, never crash the session. Stateless per-call agents; CLI args override config.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/ohm/core/mcp_server.py` | New | FastMCP builder + tools + transports |
| `src/ohm/commands/mcp.py` | Modified | `serve` sub-subcommand |
| `src/ohm/commands/serve.py` | Modified | `--protocol mcp` alias |
| `src/ohm/core/config.py` | Modified | `mcp_server:` section |
| `tests/test_mcp_server.py` | New | TDD: tools + transports |
| `docs/cli-help-outputs.md`, `docs/configuration.md` | Modified | Help text / server config docs |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Tools require live API keys (CRITICAL) | High | Injectable agent factory; fake agent in tests; clean error on unconfigured provider |
| README:251 contract violated | Med | `--protocol mcp` alias ships in same change |
| CLI parity test breaks | Med | Sub-subcommand of `mcp`; no new top-level command |
| Config semantics collision (`mcp:` vs `mcp_server:`) | Med | Distinct `mcp_server:` key; docs updated |
| Port mismatch (8000 vs 3000) | Med | `--port` passed explicitly through dispatcher |
| PR budget (400 lines) | Med | Minimal surface; slice if needed: (1) core+tests, (2) CLI+docs |

## Rollback Plan

Additive change — revert feature-branch commits; no schema/data migration. If `mcp_server:` config key misbehaves, drop the key (CLI args still function). `serve` without `--protocol mcp` keeps today's placeholder behavior, so the default path is unchanged.

## Dependencies

- `mcp[cli]>=1.28.1` (already declared; HTTP extras installed). No new packages.

## Success Criteria

- [ ] `uv run pytest` green (new + existing suite)
- [ ] MCP client lists tools; `call_tool("run_prompt", ...)` returns AgentResponse fields via fake agent
- [ ] Unconfigured provider → clean error result, session survives
- [ ] `ohm mcp serve` (stdio) starts; `ohm serve --protocol mcp --port 3000` works as documented
- [ ] CLI parity test untouched; help outputs and config docs updated

## Proposal Question Round

Assumptions for user review (delegated — could not ask interactively):
1. Streaming, resources/subscriptions, HTTP auth deferred to Stage 2 — OK?
2. `get_config`/`get_skill` tools excluded from Stage 1 — OK?
3. `mcp_server:` config key included now (vs CLI-args-only) — OK?
4. Stateless tools (no session continuation) in Stage 1 — OK?
