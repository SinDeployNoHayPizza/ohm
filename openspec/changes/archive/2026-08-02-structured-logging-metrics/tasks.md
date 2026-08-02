# Tasks: Structured Logging and Metrics

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~600 (range 500–700) |
| 400-line budget risk | High vs 400 default; 800-line budget granted preflight |
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
| S1 | Logging bootstrap (OBS-1/2/8) | PR 1 | `uv run pytest tests/test_observability.py -k TestLoggingBootstrap` | `OHM_LOG_LEVEL=DEBUG uv run ohm doctor`: DEBUG on stderr, stdout clean | Revert observability.py + cli/main.py |
| S2 | Metrics registry (OBS-4/7) | PR 1 | `uv run pytest tests/test_observability.py -k TestMetricsRegistry` | N/A: no CLI surface until S4 | Revert MetricsRegistry + config keys |
| S3 | Instrumentation (OBS-5/6) | PR 1 | `uv run pytest tests/test_observability.py -k "TestAgentMetrics or TestProviderMetrics"` | N/A: requires live API key; fake-agent tests cover it | Revert agent.py/provider.py |
| S4 | Surfaces + purity (OBS-9/3) | PR 1 | `uv run pytest tests/test_observability.py -k "TestCliMetricsJson or TestStdoutPurity"` | `uv run ohm doctor --json`: metrics section present | Revert doctor.py/status.py |

## Phase 1: S1 — Logging Bootstrap (OBS-1, OBS-2, OBS-8)

- [x] 1.1 RED — `TestLoggingBootstrap`: `OHM_LOG_LEVEL=DEBUG` surfaces INFO on stderr; default level suppresses INFO (OBS-1)
- [x] 1.2 RED — json line parses to timestamp/level/logger/message; text default readable (OBS-2)
- [x] 1.3 RED — invalid level → INFO+warning; invalid `log_format` → text+warning; setup idempotent, no duplicate handlers (D3)
- [x] 1.4 RED — F1/OBS-8: key-like string in prompt → output has no prompt text/key value; no `exc_info` (allowlist test)
- [x] 1.5 GREEN — create `src/ohm/core/observability.py`: `setup_logging(cfg)` (root level, stderr-only handler) + `JSONFormatter` (allowlist timestamp/level/logger/message/metadata)
- [x] 1.6 GREEN — `config.py`: `log_format: str = "text"` field + `to_dict`; `load_config` validation fallbacks; `_ENV_MAP` += `OHM_LOG_FORMAT`
- [x] 1.7 GREEN — `cli/main.py`: `setup_logging(get_config())` in try/except at `main()` entry

## Phase 2: S2 — Metrics Registry (OBS-4, OBS-7)

- [x] 2.1 RED — `TestMetricsRegistry`: accumulate; snapshot `{enabled,counters,histograms,cost}` with `cost.usd == 0.0` (OBS-7)
- [x] 2.2 RED — F2/OBS-4: `metrics_enabled: false` → records nothing, snapshot `{}` (disabled registry)
- [x] 2.3 RED — `reset()` clears; broken internals never raise (D5)
- [x] 2.4 GREEN — `observability.py`: Lock-guarded `MetricsRegistry` (increment/record_histogram/reset/snapshot, swallows internal errors) + `get_metrics()`; `setup_logging` sets module `_enabled` flag from `cfg.metrics_enabled`
- [x] 2.5 GREEN — `config.py`: `metrics_enabled: bool = True` field (D2) + `to_dict`; `_ENV_MAP` += `OHM_METRICS_ENABLED` with sandbox-style bool coercion (F3: config.py:248-249 pattern)

## Phase 3: S3 — Instrumentation (OBS-5, OBS-6)

- [x] 3.1 RED — `TestAgentMetrics`: success → runs.success, latency.ms, tokens.{total,input,output}, cycles.total, tools.calls; failure → runs.failure, no propagation; stream counters (OBS-5)
- [x] 3.2 RED — `TestProviderMetrics`: 429 succeeded on retry → retry.attempts + transient.429; failover → provider.failover (OBS-6)
- [x] 3.3 GREEN — `agent.py`: instrument `run()`/`stream()` boundaries via `get_metrics()`
- [x] 3.4 GREEN — `provider.py`: instrument `retry()` transient branch + `FallbackProvider.complete` except branch

## Phase 4: S4 — CLI Surfaces (OBS-9, OBS-3)

- [x] 4.1 RED — `TestCliMetricsJson`: doctor/status `--json` include nested `metrics`, populated + empty-zero (OBS-9, D4)
- [x] 4.2 RED — `TestStdoutPurity` (CRITICAL): `_handle_run` with fake agent, json+DEBUG → stdout == response, stderr JSON lines (OBS-3)
- [x] 4.3 GREEN — `doctor.py`: add `metrics: snapshot()` to `--json` result (line ~154-162)
- [x] 4.4 GREEN — `status.py`: add `metrics: snapshot()` to `--json` result (line ~86-105)

## Phase 5: Docs & Verification

- [x] 5.1 F4 — `README.md:446` + `README.es.md:449`: rename `ohm.metrics.success` → `ohm.metrics.runs.success`; confirm remaining names match design
- [x] 5.2 Verify — `uv run pytest` full suite green (236); `uv run ohm doctor --json` shows metrics; stdout purity regression passes
