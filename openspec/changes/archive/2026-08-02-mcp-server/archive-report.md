# Archive Report: MCP Server — Stage 1

- **Change**: `mcp-server`
- **Branch**: `feature/mcp-server` (HEAD `5ff5ab1`)
- **Archived**: 2026-08-02 → `openspec/changes/archive/2026-08-02-mcp-server/`
- **Artifact store mode**: openspec (file-based) + Engram (`sdd/mcp-server/archive-report`)
- **SDD pipeline**: explore → propose → spec → design → tasks → apply → verify → **archive** (cycle complete)

## Classification

**COMPLETED — Verify PASS, no blockers, no CRITICAL, no WARNING findings.**

- Verify verdict: `pass` (`openspec/changes/archive/2026-08-02-mcp-server/verify-report.md`)
- Blockers: 0 | Critical findings: 0 | Warnings: 0 | Suggestions: 5 (3 doc-accuracy in apply-progress — fixed during archive; 2 logged as follow-ups FU-019/FU-020)
- Requirements: 12/12 compliant (MCP-1..MCP-12 = 21/21 scenarios)
- Tests: 275 passed / 0 failed / 0 skipped (`uv run pytest`, exit 0); 39 new unit tests (22 mcp_server + 7 config + 10 CLI); ruff: 0 new errors (7 pre-existing F541 in serve.py baseline — see FU-019)
- TDD: 22/22 tasks complete (all `[x]` in archived `tasks.md`), strict TDD 7/7 checks passed
- Build/CF3: `FastMCP` + `StreamableHTTPServerTransport` import OK, `compileall` exit 0
- Runtime smoke (help-level only, no transports started): `ohm mcp serve --help`, `ohm serve --help`, `ohm --help`, `ohm mcp` (no args) all behave as documented

### Gates

| Gate | Result | Evidence |
|------|--------|----------|
| Task completion | ✅ PASS | `tasks.md` 22/22 `[x]` (1.1–4.3); no stale unchecked tasks |
| Verify verdict | ✅ PASS | 0 blockers, 0 CRITICAL; verdict `pass` |
| Native review receipt | N/A | Change predates the native review system (no `review/{transaction,ledger,receipt,gate-context}` artifacts; apply-progress `reviewGate.result: allow`); verify-report is the gate evidence |
| Action context | ✅ PASS | Mode repo-local/openspec; operations confined to repo root (`D:\2026\python\ohm`) |
| Merge destructiveness | ✅ PASS | Spec sync is a verified no-op — canonical already matches the delta; no requirements removed/renamed |

## Summary of the Change

Delivered OHM's MCP server surface (Stage 1) as a new capability:

- **Core module** (`src/ohm/core/mcp_server.py`): `build_mcp_server(agent_factory=...)` with injectable agent factory (default builds production agents from `OHMConfig`, no live API keys required), exactly 7 stateless tools (`run_prompt`, `run_goal`, `get_status`, `list_sessions`, `get_session`, `list_skills`, `list_models`), no resources/prompts/subscriptions/config-mutation tools, `_safe_agent_call` wrapping factory + run for error isolation (MCP-1..7, MCP-12).
- **Transports**: `run_stdio()` and `run_http(host, port)` (explicit port — never the FastMCP default 8000) (MCP-8, MCP-9).
- **Config**: server-side `mcp_server:` section (transport, host, port) distinct from client-side `mcp:`, full `DEFAULTS` dict, `to_dict`/`load_config` merge; `_resolve_server_args` precedence CLI > config > defaults (MCP-11).
- **CLI wiring**: `ohm mcp serve` (`--transport stdio|http`, `--host`, `--port`) and `ohm serve --protocol mcp` alias routing to the same core server; default `ohm serve` behavior unchanged (MCP-10).
- **Docs**: `docs/configuration.md` `mcp_server:` section; README/README.es.md/CHANGELOG v0.1.11 (committed in S4).
- Deferred to Stage 2 (per proposal): streaming, resources, subscriptions, HTTP auth, config-mutation tools, real cost data.

## Spec Merge Actions

| Domain | Action | Details |
|--------|--------|---------|
| mcp-server | Verified (no-op) | Canonical `openspec/specs/mcp-server/spec.md` is byte-identical to the change's full-format spec (`specs/mcp-server/spec.md`, SHA256 `0639385B4C28F1E42ABF737A2EC73AE1B7D59AE7AA8B4DB66B8034F8F145CCE7`) and contains all 12 delta requirements MCP-1..MCP-12 (21 scenarios) verbatim. The canonical spec was written during apply; no merge needed. |

## Artifact Traceability (archived)

| Artifact | Path (archived) | Notes |
|----------|-----------------|-------|
| Exploration | `exploration.md` | Requirement clarification |
| Proposal | `proposal.md` | Intent, scope, approach |
| Change-level spec (delta) | `spec.md` | `# Delta for mcp-server`, MCP-1..MCP-12 |
| Delta spec (full format) | `specs/mcp-server/spec.md` | Mirror of the canonical spec |
| Design | `design.md` | D1–D8 decisions, interfaces, contracts |
| Tasks | `tasks.md` | 22/22 `[x]`, work-unit forecast S1–S4 |
| Apply progress | `apply-progress.md` | TDD cycle evidence, work-unit evidence, commits — 3 doc inaccuracies corrected at archive (below) |
| Verify report | `verify-report.md` | PASS, 12/12 requirements, 21/21 scenarios, 275 tests |

Engram mirror: `sdd/mcp-server/archive-report` (this report).

## Apply-Progress Corrections (made at archive, before freezing)

The `apply-progress.md` is a working document and is archived as-is after the following truthfulness fixes (each verified against git state):

1. **Commits table omitted `5ff5ab1`** — added row `5ff5ab1 test(mcp): add S1 RED tests for MCP server core (22 tests)` (S1 RED test file, HEAD). Commit order confirmed via `git log`: `c61ea11` → `979e7e6` → `d02d82f` → `2ddb4d5` → `5ff5ab1` (HEAD).
2. **Rollback section claimed `tests/test_mcp_server.py` remains untracked until archive** — inaccurate: it IS committed at `5ff5ab1` (verified via `git status` + `git log`). Rewritten: rollback boundary is `git reset --hard b6e7155` dropping all five feature commits; only `openspec/` change artifacts and the canonical spec remain untracked until archive.
3. **S2 focused-test count `-k mcp_server` → 7 passed** — the filter matches 6 tests; the 7th (`test_resolve_server_args_falls_back_to_defaults`) lacks "mcp_server" in its name and passes in the full-file run (33/33). Work-unit table and TDD row 2.1 corrected (6/6 on filter; 7th passes in full file).

These were verify-report SUGGESTIONs 1–3; fixing them at archive keeps the frozen audit trail truthful. No source, test, or doc files outside `openspec/` were modified.

## Follow-ups Logged

Logged to `docs/follow-ups.md` (Open):

- **FU-019** (SUGGESTION): 7 pre-existing ruff F541 errors in `src/ohm/commands/serve.py` placeholder block (lines 76, 78–83) — verified identical on pristine `b6e7155`; 0 introduced by this change. Verify suggestion 4. Proposed fix: dedicated cleanup task (drop f-string placeholders or use plain strings).
- **FU-020** (SUGGESTION): `ohm mcp serve --help` shows only one-level mcp help — the new `serve` subcommand's options are not listed (pre-existing Registry `_print_subcommand_help` design; `ohm mcp` no-args usage includes `serve`). Verify suggestion 5. Proposed fix: recurse Registry help into subcommands or surface `serve` options at mcp level.

## Verify Suggestions (non-blocking, recorded here)

1. apply-progress commits table omitted `5ff5ab1` — **fixed in archived apply-progress.md** (see corrections above).
2. apply-progress rollback claim about `tests/test_mcp_server.py` untracked — **fixed** (committed at 5ff5ab1).
3. apply-progress S2 `-k mcp_server` count 7 → actual 6 matching — **fixed** (7th test passes in full-file 33/33).
4. 7 pre-existing ruff F541 in serve.py placeholder block — **logged as FU-019** (baseline lint debt, not introduced by this change; ruff not a configured gate).
5. `ohm mcp serve --help` one-level Registry help — **logged as FU-020** (pre-existing `_print_subcommand_help` design).

## Verification of Archive

- [x] Main spec verified: `openspec/specs/mcp-server/spec.md` contains MCP-1..MCP-12; byte-identical to archived `specs/mcp-server/spec.md`
- [x] Change folder moved: `openspec/changes/archive/2026-08-02-mcp-server/`
- [x] Archive contains all artifacts (exploration, proposal, spec, specs/, design, tasks, apply-progress, verify-report, archive-report)
- [x] Archived `tasks.md` has no unchecked implementation tasks (22/22 `[x]`)
- [x] Active changes directory no longer contains this change
- [x] Docs follow-ups updated (FU-019, FU-020 added)
- [x] apply-progress.md corrected (commit 5ff5ab1, rollback statement, S2 filter count) before freezing

## SDD Cycle Complete

The change has been fully planned, implemented, verified, and archived. Ready for the next change.
