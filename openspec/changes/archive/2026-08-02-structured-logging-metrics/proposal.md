# Proposal: Structured Logging and Metrics

## Intent

OHM's observability surface is dead: `OHM_LOG_LEVEL` is parsed but never applied, `logger.info()` is silently dropped, logs are unformatted or trapped in Textual devtools, and README promises (`ohm.metrics.*`, correlation IDs) are unimplemented. Deliver a zero-new-dependency observability layer — logging bootstrap + in-process metrics registry + agent/provider instrumentation — surfaced via `--json`, without breaking the `ohm run` stdout contract.

## Scope

### In Scope
- `ohm/core/observability.py`: `setup_logging(config)` (applies `log_level`; optional JSON formatter) + `Metrics` registry (counters/histograms, README `ohm.metrics.*` names)
- Instrument `agent.run`/`stream` (success, latency, tokens, cycles, tool_usage) and `provider.retry`/`FallbackProvider` (attempts, statuses, failovers)
- Config: consume `log_level`; add `log_format`, `metrics_enabled`
- Metrics snapshot in `doctor --json` / `status --json`; logs/metrics to stderr/file only
- Strict-TDD tests: bootstrap, formatter, registry, instrumentation, stdout purity

### Out of Scope
- Stage 2 (`ohm observe --export`), correlation IDs (README claim re-scoped), real cost computation (emit `cost.usd` slot as 0.0), `self.log()` re-wiring, prompt/API-key logging

## Capabilities

### New Capabilities
- `observability`: logging bootstrap, JSON formatter, metrics registry, agent/provider instrumentation, doctor/status surface, config keys

### Modified Capabilities
- `provider-config`: OHMConfig gains `log_format`/`metrics_enabled`; `log_level` becomes applied, not dead

## Approach

Stage 1 only. `ohm/core/observability.py` exposes `setup_logging(config)` (root level from `OHM_LOG_LEVEL`; optional `JSONFormatter` → one object per record) and a `Metrics` registry emitting README-named records. Wire at CLI/TUI entry (`cli/main.py`, `cli/app.py`); instrument agent/provider with non-blocking calls. `logfire` stays transitive-only. Logs/metrics go to stderr or file — never stdout.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `core/observability.py` | New | Bootstrap + registry |
| `core/config.py` | Modified | Apply log_level; new keys |
| `core/agent.py` | Modified | Metric emission |
| `core/provider.py` | Modified | Retry/failover metrics |
| `cli/main.py`, `cli/app.py` | Modified | Entry bootstrap |
| `commands/doctor.py`, `status.py` | Modified | Metrics snapshot |
| `tests/` | New | Unit tests |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| CRITICAL: logs pollute `ohm run` stdout, breaking the response contract | Med | stderr/file only; stdout-purity test |
| Cost metrics emit 0.0 (no data source) | High | Documented slot; pricing as follow-up |
| Sensitive prompt/API-key data in logs | Med | Metadata/lengths only |
| Budget: ~8 files | Med | Work-unit slicing; 800-line budget |

## Rollback Plan

Revert the branch. All changes additive: removing bootstrap restores prior logging; no schema/migration; new keys default to current behavior.

## Dependencies

None new (stdlib only). Requires `OHMConfig` keys in `core/config.py`.

## Success Criteria

- [ ] `OHM_LOG_LEVEL=DEBUG` surfaces agent-init logs; `log_format=json` emits valid JSONL to stderr
- [ ] `ohm run` stdout contract unchanged (regression test)
- [ ] `doctor --json` / `status --json` include a populated metrics snapshot
- [ ] `uv run pytest` green with new tests

## Open Questions (assumptions for user review)

- Deferrals per recommendation: Stage 2, correlation IDs, real cost computation — confirm
- Metrics snapshot shape (flat vs nested) — resolve in spec phase
