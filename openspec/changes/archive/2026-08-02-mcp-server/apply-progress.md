# Apply Progress: mcp-server

- **Change**: `mcp-server`
- **Batch**: single apply batch covering all 22 tasks (S1→S4)
- **Mode**: Strict TDD (openspec/config.yaml `strict_tdd: true`, runner `uv run pytest`)
- **Status**: all 22 tasks complete — **ready for verify**
- **Store**: openspec (native) with hybrid persistence (tasks.md checkboxes + Engram observation `sdd/mcp-server/apply-progress`)

## SDD Status (gentle-ai.sdd-status v1)

```yaml
schemaName: gentle-ai.sdd-status
schemaVersion: 1
changeName: mcp-server
artifactStore: hybrid
planningHome:
  mode: repo-local
  path: D:\2026\python\ohm\openspec
changeRoot: D:\2026\python\ohm\openspec\changes\mcp-server
artifactPaths:
  proposal: [D:\2026\python\ohm\openspec\changes\mcp-server\proposal.md]
  specs: [D:\2026\python\ohm\openspec\changes\mcp-server\spec.md]
  design: [D:\2026\python\ohm\openspec\changes\mcp-server\design.md]
  tasks: [D:\2026\python\ohm\openspec\changes\mcp-server\tasks.md]
  applyProgress: [D:\2026\python\ohm\openspec\changes\mcp-server\apply-progress.md]
  verifyReport: []
  reviewLedger: []
  reviewReceipt: []
  reviewBundle: []
  reviewContext: []
  reviewState: []
artifacts:
  proposal: done
  specs: done
  design: done
  tasks: done
  applyProgress: done
  verifyReport: missing
  reviewLedger: missing
  reviewReceipt: missing
  reviewBundle: missing
  reviewContext: missing
  reviewState: missing
taskProgress:
  total: 22
  completed: 22
  pending: 0
  allComplete: true
dependencies:
  proposal: all_done
  specs: all_done
  design: all_done
  tasks: all_done
  apply: all_done
  verify: ready
  archive: blocked
applyState: all_done
actionContext:
  mode: repo-local
  workspaceRoot: D:\2026\python\ohm
  allowedEditRoots: [D:\2026\python\ohm]
relationships:
  dependsOn: []
  supersedes: []
  amends: []
  conflictsWith: []
  sameDomainActiveChanges: []
remediationState:
  required: false
  complete: false
  failedEvidenceRevision: ""
  lineageId: ""
  generation: 0
  fixBatch: 0
  reason: ""
reviewGate:
  result: allow
  reason: No review transaction exists; final archive gating will re-evaluate.
phaseInstructions:
  apply: []
  verify: []
  remediate: []
  archive: []
nextRecommended: verify
blockedReasons: []
```

## Work Unit Evidence (all modes)

| Work unit | Focused test command + exact result | Runtime harness command/scenario + exact result | Rollback boundary |
|-----------|-------------------------------------|------------------------------------------------|-------------------|
| S1 — Core module + tools (MCP-1..7,12) | `uv run pytest tests/test_mcp_server.py` → **22 passed** | Real stdio initialize handshake via `uv run ohm mcp serve` (probe script) → JSON-RPC `serverInfo: {name: "ohm-mcp", version: "1.28.1"}`, clean stderr, no provider calls | Revert `src/ohm/core/mcp_server.py` + `tests/test_mcp_server.py` |
| S2 — mcp_server config (MCP-11) | `uv run pytest tests/test_config.py -k mcp_server` → **6 passed** (the filter matches 6 tests; the 7th, `test_resolve_server_args_falls_back_to_defaults`, lacks "mcp_server" in its name — it passes in the full-file run); full file → **33 passed** | N/A: no CLI surface until S3 — `_resolve_server_args` exercised via unit tests (precedence CLI > config > defaults) | Revert `config.py` `mcp_server` field/merge + tests |
| S3 — CLI wiring (MCP-8/9/10) | `uv run pytest tests/test_cli.py -k "McpServe or ServeProtocol or ResolveServerArgs"` → **10 passed**; full file → **46 passed** | `uv run ohm mcp serve --help` / `uv run ohm serve --help` (parse, no bind); real stdio handshake probe (same as S1) | Revert `mcp.py`/`serve.py` branches + appended tests |
| S4 — Docs & verification (CF3) | `uv run pytest` (full suite) → **275 passed** (236 baseline + 39 new) | CF3 import check: `from mcp.server.fastmcp.server import FastMCP` + `from mcp.server.streamable_http_manager import StreamableHTTPServerTransport` → **OK** (mcp 1.28.1) | Revert `docs/configuration.md`/README/CHANGELOG edits; drop feature commits |

## TDD Cycle Evidence (Strict TDD mode)

| Task | RED (test written first) | GREEN (implementation passes) | REFACTOR |
|------|--------------------------|-------------------------------|----------|
| 1.1 RED — 7 tools, empty resources/prompts | `test_mcp_server.py` written; baseline run **22 failed** (module missing) | 22/22 pass after `mcp_server.py` created | N/A (new module) |
| 1.2 RED — run_prompt success + unconfigured-provider error | Same 22-failed baseline includes these | 22/22 pass | N/A |
| 1.3 RED — run_goal success + error | Same baseline | 22/22 pass | N/A |
| 1.4 RED — get_status fields | Same baseline | 22/22 pass | N/A |
| 1.5 RED — list_sessions/get_session + missing error | Same baseline | 22/22 pass | N/A |
| 1.6 RED — list_skills + list_models filter | Same baseline | 22/22 pass | N/A |
| 1.7 RED — factory raises → clean error; default factory | Same baseline (includes D3/MCP-12 cases) | 22/22 pass | N/A |
| 1.8 GREEN — build_mcp_server, _safe_agent_call, 7 closures | written after 1.1–1.7 tests | 22/22 pass | N/A |
| 1.9 GREEN — run_stdio/run_http + `_resolve_server_args` | written after tests | 22/22 pass; full suite 258 passed | N/A |
| 2.1 RED — mcp_server defaults/round-trip/distinct | `TestMcpServerConfig` added to `test_config.py`; run → **6 failed** (`AttributeError: 'OHMConfig' object has no attribute 'mcp_server'`) | 7/7 class tests pass — 6/6 on the `-k mcp_server` filter, 7th (`test_resolve_server_args_falls_back_to_defaults`) in the full-file 33/33 — after `DEFAULTS["mcp_server"]` + `OHMConfig.mcp_server` field + `load_config` merge | N/A |
| 2.2 RED — CF1 empty-config fallback | 1 of 2 tests **failed**; `test_resolve_server_args_falls_back_to_defaults` passed immediately (function existed from S1 — regression guard, no separate RED) | both pass | N/A |
| 2.3 GREEN — config.py field + DEFAULTS + merge | after 2.1/2.2 tests | 33/33 pass (full file) | N/A |
| 2.4 GREEN — `_resolve_server_args` precedence | function pre-existed from S1 (D6); precedence verified by tests in 2.2/3.3 | pass | N/A |
| 3.1 RED — mcp serve parse | `TestMcpServe` added; run → **8 failed** (McpServe+ServeProtocol) | 10/10 pass | N/A |
| 3.2 RED — serve --protocol parse | same 8-failed run | 10/10 pass | N/A |
| 3.3 RED — dispatch monkeypatch + precedence | 6 of 8 failed; 2 `TestResolveServerArgs` passed immediately (S1 behavior — regression guards) | 10/10 pass | N/A |
| 3.4 GREEN — mcp.py serve sub-parser + dispatch | after 3.1–3.3 tests | 10/10 pass; full CLI file 46/46 | N/A |
| 3.5 GREEN — CF2 no asyncio.run wrapper | after tests | 10/10 pass | N/A |
| 3.6 GREEN — serve.py --protocol/--port None + mcp branch | after tests | 10/10 pass | N/A |
| 4.1 GREEN — configuration.md mcp_server section | docs (no test; suite keeps 275 green) | suite 275 passed | N/A |
| 4.2 VERIFY — full suite + CF3 streamable-http import | N/A (verification gate) | `uv run pytest` → **275 passed**; CF3 import → **OK** (symbol is `StreamableHTTPServerTransport` in mcp 1.28.1) | N/A |
| 4.3 VERIFY — TestCliTuiParity unchanged; cli-help-outputs.md untouched | N/A (verification gate) | `git diff` shows only appends after `TestCliTuiParity` (hunk anchor, class body untouched); `docs/cli-help-outputs.md` absent from `b6e7155..2ddb4d5` diff | N/A |

## Commits

| Commit | Message | Scope |
|--------|---------|-------|
| `c61ea11` | `feat(mcp): add FastMCP server core with seven stateless tools` | S1 (mcp_server.py + tests) |
| `979e7e6` | `feat(config): add mcp_server section for the MCP server transport` | S2 (config.py + tests) |
| `d02d82f` | `feat(cli): wire ohm mcp serve and serve --protocol mcp` | S3 (mcp.py, serve.py + tests) |
| `2ddb4d5` | `docs(mcp): document ohm mcp serve, mcp_server config, v0.1.11` | S4 (docs) |
| `5ff5ab1` | `test(mcp): add S1 RED tests for MCP server core (22 tests)` | S1 (RED test file `tests/test_mcp_server.py`) — HEAD |

## Deviations and Notes

- **CF3 symbol (mcp 1.28.1)**: the streamable-http transport export is `StreamableHTTPServerTransport` from `mcp.server.streamable_http_manager` (the module does NOT expose `streamable_http_manager` as an attribute). Import check passes with the real symbol; no code uses it directly yet (transport selection stays in FastMCP via `mcp.run("streamable-http")` at a later stage).
- **Pre-existing ruff baseline**: the repo has 44 pre-existing ruff errors (verified against pristine files at `c61ea11`), including 7 F541 in serve.py's placeholder block that predate this change. This change adds **0 new** ruff errors (ruff on all 5 touched source files reports only those 7 pre-existing serve.py lines). Baseline left untouched — flagging rather than silently fixing out-of-scope lines.
- **Registry help depth**: `ohm mcp serve --help` shows the one-level mcp help (pre-existing Registry design — `_print_subcommand_help` only lists mcp-level options). `ohm mcp` (no args) usage line correctly includes `serve`. Not in scope to redesign the Registry.
- **TDD honesty**: 3 tests (2 in S2/S3 RED batches + 1 fallback) passed at write time because their behavior was already implemented in S1 (`_resolve_server_args`, D6) — recorded as regression guards, not claimed RED.
- **README command reality check**: `ohm serve --protocol mcp --port 3000` remains a valid alias; the primary documented path is now `ohm mcp serve` (stdio) / `ohm mcp serve --transport http --port 3000`, preserving the 3000 default port promise (`_DEFAULT_PORT = 3000`, `DEFAULTS["mcp_server"].port = 3000`).
- **Env gotcha (pre-existing, unchanged)**: repo `.env` sets real `GEMINI_API_KEY` + `OHM_PROVIDER=gemini` and `load_config()` pushes `.env` into `os.environ` without cleanup; tests rely on conftest's `_isolated_environ` autouse fixture. Status/CLI tests use `_PROVIDER_KEY_ENVS` + `monkeypatch.delenv`. No behavior changed.

## Rollback

The five commits (`c61ea11`, `979e7e6`, `d02d82f`, `2ddb4d5`, `5ff5ab1`) can be dropped as a unit: `git reset --hard b6e7155` restores the pre-change state (feature branch `feature/mcp-server`). All implementation and test files are committed across those five commits, including `tests/test_mcp_server.py` (committed at `5ff5ab1`, HEAD). Only `openspec/` change artifacts and the canonical spec (`openspec/specs/mcp-server/`) remain untracked until archive. (Corrected at archive: an earlier draft claimed `tests/test_mcp_server.py` remained untracked until archive; it is in fact committed at `5ff5ab1`.)
