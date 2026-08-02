# Design: Structured Logging and Metrics

## Technical Approach

Zero-new-dependency observability in one module, `src/ohm/core/observability.py` (README "Observability Layer"). `setup_logging(cfg)` bootstraps the root logger — level from `cfg.log_level` (already env-overridden by `OHM_LOG_LEVEL` via `_ENV_MAP`), optional `JSONFormatter`, stderr-only handler — and applies `cfg.metrics_enabled`. A thread-safe `MetricsRegistry` singleton accumulates README-named `ohm.metrics.*` counters/histograms. Wired at CLI/TUI entry (`cli/main.py`), instrumented in `Agent.run/stream` and `Provider.retry`/`FallbackProvider`, surfaced as a nested `metrics` section in `doctor --json` / `status --json`. Covers OBS-1..OBS-9 + PC-1.

## Architecture Decisions

| # | Decision | Options (tradeoff) | Choice |
|---|---|---|---|
| D1 | Module home | split files (more surface) · `utils/` (data helpers, not machinery) | `core/observability.py` — proposal-named, cohesive, matches core/ convention |
| D2 | `metrics_enabled` default | `false` (feature invisible, observability-blind again) | `true` — PC-1 mandates it; in-process only, near-zero cost, opt-out for privacy; rollback intact (no new stdout surface) |
| D3 | `log_format` validation | at `setup_logging` (misses direct construction) | in `load_config` (PC-1: "when OHMConfig is loaded"): invalid → `text` + warning; `setup_logging` also guards invalid level → INFO + warning |
| D4 | Snapshot shape | flat (collides with doctor/status top-level keys) | nested `metrics` object — mirrors doctor's `checks` precedent; contract below |
| D5 | Instrumentation failure isolation | try/except per call site (noisy) · `safe_*` wrappers (extra API) | registry swallows its own errors internally; call sites never propagate (OBS-5) |
| D6 | Cost slot | compute from catalog (Stage 2) · omit | synthetic `cost.usd = 0.0` in enabled snapshots (OBS-7); disabled snapshot `{}` (OBS-4 wins — documented) |

## Data Flow

```
cli/main.py ── setup_logging(cfg) ──► root logger ──► StreamHandler(sys.stderr)
Agent.run/stream ──► get_metrics() ──► MetricsRegistry (Lock) ──┐
Provider.retry / FallbackProvider ──► get_metrics() ───────────┤
doctor/status --json ──► snapshot() ──► {..., "metrics": {...}} ─► stdout
```

## File Changes

| File | Action | Description |
|---|---|---|
| `src/ohm/core/observability.py` | Create | `setup_logging`, `JSONFormatter`, `MetricsRegistry`, `get_metrics()` |
| `src/ohm/core/config.py` | Modify | `log_format`/`metrics_enabled` fields, defaults, `to_dict`, `load_config` validation; `_ENV_MAP` += `OHM_LOG_FORMAT`, `OHM_METRICS_ENABLED` |
| `src/ohm/cli/main.py` | Modify | `setup_logging(get_config())` at `main()` entry (try/except — never blocks startup) |
| `src/ohm/core/agent.py` | Modify | Instrument `run()`/`stream()` boundaries (OBS-5) |
| `src/ohm/core/provider.py` | Modify | Instrument `retry()` transient branch + `FallbackProvider.complete` (OBS-6) |
| `src/ohm/commands/doctor.py` | Modify | `--json` gains `"metrics"` (OBS-9) |
| `src/ohm/commands/status.py` | Modify | `--json` gains `"metrics"` (OBS-9) |
| `tests/test_observability.py` | Create | Logging, registry, instrumentation, stdout-purity tests |

## Interfaces / Contracts

```python
def setup_logging(cfg: OHMConfig) -> None    # root level; stderr handler; text|json; applies metrics_enabled
class JSONFormatter(logging.Formatter): ...  # {timestamp, level, logger, message, *extra}; never exc_info
class MetricsRegistry:
    def increment(name: str, amount: int = 1) -> None
    def record_histogram(name: str, value: float) -> None
    def reset() -> None
    def snapshot() -> dict
def get_metrics() -> MetricsRegistry         # module singleton, enabled=True
```

`snapshot()` enabled: `{"enabled": true, "counters": {...}, "histograms": {name: {count, sum, min, max, avg}}, "cost": {"usd": 0.0}}`; disabled: `{}`.

Metric names: `ohm.metrics.runs.{success,failure}`, `tokens.{total,input,output}`, `cycles.total`, `tools.calls` + `tools.{name}`, `latency.ms` (histogram), `provider.retry.attempts`, `provider.transient.{429,503,5xx}`, `provider.failover`, `cost.usd`.

OBS-8: formatter serializes a fixed allowlist; new records pass counts/lengths only — no prompt bodies, keys, or `exc_info`.

## Testing Strategy

Slices = work-unit commits; single PR ≤ 800 lines; run `uv run pytest`.

| Slice | RED tests (`tests/test_observability.py`) |
|---|---|
| S1 bootstrap | `TestLoggingBootstrap`: level applied; `OHM_LOG_LEVEL=DEBUG` surfaces INFO on stderr; text vs json (line parses, has timestamp/level/logger/message); invalid level fallback; idempotent setup (no duplicate handlers); invalid `log_format` → text + warning; no `exc_info` in output |
| S2 registry | `TestMetricsRegistry`: accumulate; snapshot shape + `cost.usd == 0.0`; disabled records nothing, snapshot `{}`; reset; broken internals never raise |
| S3 instrumentation | `TestAgentMetrics`: run success/failure counters + tokens + latency + cycles + tools; failure never propagates; stream counters. `TestProviderMetrics`: 429-retry → attempts + transient.429; failover counter |
| S4 surfaces | `TestCliMetricsJson`: doctor/status `--json` include metrics (populated + empty-zero). `TestStdoutPurity` (CRITICAL, OBS-3): `_handle_run` with fake agent under json+DEBUG — stdout == response exactly, stderr holds JSON lines |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary. Log destination (stderr-only, OBS-3) is enforced by the S4 stdout-purity RED test, outside this matrix.

## Migration / Rollout

No migration. Additive keys (`log_format: text`, `metrics_enabled: true`, PC-1) preserve current behavior; rollback = revert branch. `ohm run` stdout unchanged (S4 regression).

## Open Questions

- [ ] `run.py:48` echoes `[run] prompt: {args.prompt}` to stderr — a pre-existing UI print, not a log record; OBS-8 covers log records only. Recommend follow-up redaction.
- [ ] None blocking.
