# Tasks: MCP Server — Stage 1

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~900 (range 850–1000) |
| 400-line budget risk | High vs 400 default; 800-line budget granted preflight — borderline |
| Chained PRs recommended | No |
| Suggested split | Single PR; 4 work-unit commits (S1→S4) |
| Delivery strategy | single-pr |
| Chain strategy | size-exception |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| S1 | Core module + tools (MCP-1..7,12) | PR 1 | `uv run pytest tests/test_mcp_server.py` | N/A: in-process call_tool; live transports need a real client | Revert mcp_server.py + test_mcp_server.py |
| S2 | mcp_server config (MCP-11) | PR 1 | `uv run pytest tests/test_config.py -k mcp_server` | N/A: no CLI surface until S3 | Revert config.py field + tests |
| S3 | CLI wiring (MCP-8/9/10) | PR 1 | `uv run pytest tests/test_cli.py -k "McpServe or ServeProtocol"` | `uv run ohm serve --help`: shows `--protocol mcp` | Revert mcp.py/serve.py branches + tests |
| S4 | Docs + full suite (CF3) | PR 1 | `uv run pytest` | `uv run ohm mcp serve --help`: usage incl. serve (no bind) | Revert configuration.md; drop feature commits |

## Phase 1: S1 — Core Module (MCP-1..MCP-7, MCP-12)

- [x] 1.1 RED — `test_mcp_server.py`: fake factory → exactly 7 tools, empty resources/prompts (MCP-2)
- [x] 1.2 RED — `run_prompt` success fields + unconfigured-provider clean error (MCP-3)
- [x] 1.3 RED — `run_goal` success + unconfigured-provider clean error (MCP-4)
- [x] 1.4 RED — `get_status` fields: version/provider/model/api-key/session count (MCP-5)
- [x] 1.5 RED — `list_sessions`/`get_session` incl. missing-session clean error (MCP-6)
- [x] 1.6 RED — `list_skills` (tmp dirs) + `list_models` provider filter (MCP-7)
- [x] 1.7 RED — D3/MCP-12: factory raises → clean error result, `get_status` next succeeds; default factory via monkeypatched `ohm.core.agent.Agent` (MCP-1)
- [x] 1.8 GREEN — create `src/ohm/core/mcp_server.py`: `build_mcp_server`, `_default_agent_factory`, `_safe_agent_call` (try/except around factory+run in EVERY tool), 7 tool closures
- [x] 1.9 GREEN — `run_stdio` (mcp.run("stdio")) + `run_http(host, port)` with explicit host/port (MCP-8/9)

## Phase 2: S2 — Config (MCP-11)

- [x] 2.1 RED — `test_config.py`: `mcp_server` defaults `{transport: stdio, host: 127.0.0.1, port: 3000}`; YAML load; to_dict round-trip; distinct from `mcp:` (MCP-11)
- [x] 2.2 RED — CF1 empty-config path: no `mcp_server:` key → defaults merged; `_resolve_server_args` falls back to defaults
- [x] 2.3 GREEN — `config.py`: `mcp_server` field + `DEFAULTS["mcp_server"]` full dict (NOT `{}` mirror of `mcp:`), to_dict + load_config merge (CF1)
- [x] 2.4 GREEN — `mcp_server.py`: `_resolve_server_args(args, cfg)` — CLI > config > defaults (D6)

## Phase 3: S3 — CLI Wiring (MCP-8/9/10)

- [x] 3.1 RED — `TestMcpServe`: `Registry.parse(["mcp","serve","--transport","http","--port","3000"])` namespace (MCP-9)
- [x] 3.2 RED — `TestServeProtocol`: `serve --protocol mcp` parse; default protocol stays http (MCP-10)
- [x] 3.3 RED — dispatch monkeypatches `run_http`/`run_stdio` — no socket bind (CF4); `_resolve_server_args` precedence CLI>config>default (MCP-11)
- [x] 3.4 GREEN — `mcp.py`: `serve` sub-parser (`--transport stdio|http`, `--host`, `--port`); execute branch http→`run_http`, stdio→`run_stdio`; usage fallback string += `serve` (CF2)
- [x] 3.5 GREEN — CF2: no `asyncio.run` wrapper inside handler — `FastMCP.run()` blocks; call `run_http`/`run_stdio` directly
- [x] 3.6 GREEN — `serve.py`: `--protocol {http,mcp}` default http, `--port` default None; mcp branch → `core.mcp_server.run_http(host, port)` (MCP-9/10)

## Phase 4: S4 — Docs & Verification (CF3)

- [x] 4.1 GREEN — `docs/configuration.md`: document `mcp_server:` section (transport/host/port, CLI overrides)
- [x] 4.2 VERIFY — full `uv run pytest` green; real streamable-http transport import check (exercises run_http path at import, not only bind) (CF3)
- [x] 4.3 VERIFY — `test_cli.py` `TestCliTuiParity` unchanged; `docs/cli-help-outputs.md` untouched
