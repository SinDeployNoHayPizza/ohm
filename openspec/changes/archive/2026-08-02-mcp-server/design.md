# Design: MCP Server — Stage 1

## Technical Approach

One FastMCP core module with an injectable agent factory, exposed two ways: `ohm mcp serve` (stdio default, `--transport`/`--host`/`--port`) and `ohm serve --protocol mcp` alias (honors README:251). Tools are stateless, per-call agents resolved via the factory (existing `test_commands.py` monkeypatch pattern), so tests need no API keys. Every tool returns a clean result dict and never raises — error isolation lives in the tool layer. `mcp_server:` config section is distinct from client-side `mcp:`. Verified against mcp 1.28.1: `FastMCP(name, host, port)` constructor attrs feed `run_streamable_http_async()`; `call_tool()`/`list_tools()`/`list_resources()`/`list_prompts()` enable in-process strict-TDD tests.

## Architecture Decisions

| # | Decision | Option | Tradeoff | Decision |
|---|----------|--------|----------|----------|
| D1 | Builder shape | Class `OhmMcpServer` vs `build_mcp_server()` function | Class = more ceremony; function matches `build_*` CLI pattern, closure over factory/config | Function `build_mcp_server(agent_factory=None, *, host="127.0.0.1", port=8000) -> FastMCP`; tools defined as closures inside (MCP-1) |
| D2 | Agent factory type | `Callable[[AgentConfig], Agent]` | Existing `test_commands.py` pattern is `factory(config)`; duck-typed (fake needs `async run`) | `AgentFactory = Callable[[AgentConfig], Any]`; default factory wraps `Agent(config)`. Stateless per-call agents (MCP-1) |
| D3 | Error isolation | Pre-check keys vs wrap-all | Pre-check misses model-construction failures | Every agent tool wraps factory call + `await agent.run(...)` in `try/except Exception` → `AgentResponse(success=False, error=...)`. `Agent.run` catches post-`_ensure_agent()` errors itself, but `_ensure_agent()` runs before its `try` and can raise (unknown provider `ValueError`, `ImportError`) (MCP-3/4/12) |
| D4 | Transports | `mcp.run()` per transport | `run_streamable_http_async()` reads `settings.host/port` (no args) | `run_stdio(agent_factory=None) -> None` → `mcp.run("stdio")`; `run_http(host, port, agent_factory=None) -> None` → build with `host=`/`port=` then `mcp.run("streamable-http")`. Port always explicit — FastMCP default 8000 ≠ README 3000 (MCP-8/9) |
| D5 | CLI surface | New top-level vs sub-subcommand | New top-level breaks `test_cli.py` parity + `CLI_TUI_MAPPING` | `serve` sub-subcommand inside `commands/mcp.py`'s existing subparsers (no registry change). `serve.py` gains `--protocol {http,mcp}` default `http` (placeholder preserved). NO new module in `src/ohm/commands/` — auto-discovery would register a top-level command (MCP-8/10) |
| D6 | Port/transport resolution | CLI-only vs config-only | Spec MCP-11: CLI overrides config | Pure helper `_resolve_server_args(args, cfg)`: explicit CLI flag > `cfg.mcp_server.*` > defaults (stdio, 127.0.0.1, 3000). `serve --port` default becomes `None`; http branch resolves 8080 (today's value), mcp branch resolves config/3000 (MCP-9/11) |
| D7 | Config shape | Extend `mcp:` vs new `mcp_server:` | `mcp:` is documented client-side (docs/configuration.md:219) | `OHMConfig.mcp_server: dict` field mirroring `mcp:` pattern (DEFAULTS + field + `to_dict()` + `load_config` merge); defaults `{transport: stdio, host: 127.0.0.1, port: 3000}` (MCP-11) |
| D8 | Payload reuse | Duplicate vs import existing logic | Duplication diverges; existing cross-module private imports already established (app.py imports `_load_last_session`) | `run_goal` reuses `GOAL_SYSTEM_PROMPT` (commands/goal.py); sessions via `commands.session._list_session_files/_load_session/_get_sessions_dir`; skills via `SkillLoader.discover_skills(DEFAULT_SKILL_SEARCH_PATHS())` (DD-08); models via `PROVIDER_CATALOG`; status mirrors status.py's `_API_KEY_ENV` scan. Lazy imports inside tool bodies (agent.py pattern) to avoid cycles (MCP-4/5/6/7) |

## Data Flow

```
MCP client (Claude Desktop, opencode)
   │  stdio / streamable HTTP
   ▼
FastMCP (core/mcp_server.py)  ──7 @mcp.tool() closures──┐
   │ call_tool(name, args)                              │
   ▼                                                    │
tool fn → safe_agent_call(): try agent_factory(AgentConfig(...))  │
              → await agent.run(prompt|goal)            │
              → dict {content, tokens_used, latency_ms, success, error}
   │  config: cfg.mcp_server.* / CLI args               ▼
   └─ get_status/list_* → config.py, session.py, skills/, provider.py
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/ohm/core/mcp_server.py` | Create | `build_mcp_server`, 7 tools, `run_stdio`, `run_http`, `_default_agent_factory`, `_safe_agent_call`, `_resolve_server_args` |
| `src/ohm/core/config.py` | Modify | `mcp_server` field, `DEFAULTS["mcp_server"]`, `to_dict`, `load_config` merge (mirror `mcp:`) |
| `src/ohm/commands/mcp.py` | Modify | `serve` sub-parser (`--transport`/`--host`/`--port`); `execute` branch; usage line gains `serve` |
| `src/ohm/commands/serve.py` | Modify | `--protocol {http,mcp}` default `http`; `--port` default `None`; mcp branch dispatches to `core.mcp_server.run_http` |
| `tests/test_mcp_server.py` | Create | Tool registration, `call_tool` behavior with fake agent, error isolation, transports |
| `tests/test_cli.py` | Modify | New test classes: `mcp serve` / `serve --protocol mcp` arg parsing + dispatch (parity class untouched) |
| `docs/configuration.md` | Modify | `mcp_server:` section docs |

`docs/cli-help-outputs.md`: **no change** — top-level help lists only top-level subcommands with unchanged `help_text`; verified.

## Interfaces / Contracts

```python
AgentFactory = Callable[[AgentConfig], Any]          # duck: async run(prompt) -> AgentResponse
def build_mcp_server(agent_factory: AgentFactory | None = None, *,
                     name: str = "ohm-mcp", host: str = "127.0.0.1", port: int = 8000,
                     config: OHMConfig | None = None) -> FastMCP
def run_stdio(agent_factory: AgentFactory | None = None) -> None
def run_http(host: str, port: int, agent_factory: AgentFactory | None = None) -> None
# mcp_server config: {"transport": "stdio"|"http", "host": str, "port": int}
# tool result envelope (MCP-3): {"content": str, "tokens_used": int,
#   "latency_ms": float, "success": bool, "error": str | None}
# CLI: ohm mcp serve [--transport stdio|http] [--host H] [--port P]
#      ohm serve [--protocol http|mcp] [--host H] [--port P]
```

## Testing Strategy

Strict TDD (`uv run pytest`); FastMCP in-process `call_tool()`/`list_tools()` — no transports, no API keys.

| Slice | Files | Tests |
|-------|-------|-------|
| S1 core | `mcp_server.py` + `test_mcp_server.py` | FakeAgentFactory: exactly 7 tools (MCP-2), empty resources/prompts (MCP-2), run_prompt/run_goal success + unconfigured-provider clean error (MCP-3/4), get_status fields (MCP-5), sessions list/get + missing (MCP-6), skills via tmp dirs + models filter (MCP-7), error isolation: failing tool then `get_status` on same instance (MCP-12), default factory via `monkeypatch.setattr("ohm.core.agent.Agent", factory)` (MCP-1) |
| S2 config | `config.py` + `test_config.py` | `mcp_server` defaults, YAML load from tmp files, `to_dict` round-trip, distinct from `mcp:` (MCP-11) |
| S3 CLI | `mcp.py`, `serve.py` + `test_cli.py` | `Registry.parse(["mcp","serve","--transport","http","--port","3000"])` namespace; `serve --protocol mcp` parse; dispatch via monkeypatched `run_http`/`run_stdio` (no binding); `_resolve_server_args` precedence CLI>config>default (MCP-8/9/10/11); parity class unchanged |
| S4 docs | `configuration.md` | Docs accuracy; full suite green |

## Threat Matrix

`N/A` — no routing, shell-command, subprocess, VCS/PR-automation, executable-file-classification, or process-integration boundary. FastMCP transports are third-party listeners; tools execute no shell/subprocess. (Network-listener hardening — auth, DNS-rebinding — is Stage 2 scope per proposal.)

## Migration / Rollout

No migration. Additive: `mcp_server:` key optional (CLI args function without it); `serve` default protocol unchanged; revert = drop feature-branch commits.

## Open Questions

- None blocking. Deviation from proposal noted: `docs/cli-help-outputs.md` needs no edit (top-level help unchanged); `test_cli.py` parity class untouched.
