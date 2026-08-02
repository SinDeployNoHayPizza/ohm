# Exploration: Structured Logging and Metrics

> SDD explore artifact for change `structured-logging-metrics` (Phase 2 Core Engine roadmap item, README line 559).
> Scope: investigate current logging/observability state and propose what structured logging + metrics should look like. Exploration only — no code modified.

## Curiosity Map

- How do modules log today? (`logging`? `self.log()`? `print()`?)
- Is any observability infrastructure already present (logfire/OTel/logging config)?
- Where would metrics be captured: agent lifecycle, provider calls, session handling, CLI?
- What is the config surface users use to enable/configure logging and metrics today?
- What do CLI vs TUI vs core conventions look like today?
- Is `logfire` a direct dependency, a transitive one, or absent?
- Is the README's observability promise implemented anywhere?

## Current State

### Logging today — three disjoint mechanisms, none structured

1. **stdlib `logging`** — only 4 core modules create loggers: `src/ohm/core/config.py`, `core/provider.py`, `core/agent.py`, `core/skills/loader.py`. All use `logging.getLogger(__name__)` with lazy `%s`-style formatting (good). Calls: `logger.warning(...)` in config/loader/provider/agent, one `logger.info(...)` at `agent.py:213` ("Agent initialized…").
2. **No logging configuration anywhere.** There is no `basicConfig`, no handler, no `setLevel`, no formatter in the entire `src/` tree. The root logger stays at default `WARNING` → every `logger.info()` (e.g. agent initialization) is silently dropped; warnings are emitted as unformatted plain text to stderr. Logging is effectively **observability-blind**.
3. **TUI `self.log(...)`** — `src/ohm/cli/app.py` has 13+ `self.log(f"[stream] ...")` calls (app.py:658–821). This is **Textual's devtools console**, not Python logging: it only appears in `textual console`, is not captured by any handler, and is not structured. It is stream-debug output, not telemetry.
4. **CLI `print()`** — user-facing commands print directly: `run.py` (stdout = response, stderr = `[run]` progress), `status.py` (plain + `--json`), `doctor.py` (plain + `--json`), `session.py`, `skills.py`, `serve.py`. These are UI, not logs.

### Dead config: `OHM_LOG_LEVEL`

`OHMConfig.log_level` ("INFO") and env mapping `OHM_LOG_LEVEL` already exist (`core/config.py:62,146,263`), and `.env` ships `OHM_LOG_LEVEL=INFO` with a `# Log level: DEBUG | INFO | WARNING | ERROR` comment. **Nothing consumes `cfg.log_level`** — the value is parsed, stored, serialized, and never applied. The user-facing config surface is already declared; only the wiring is missing.

### Metrics-relevant data already exists

- `Agent._extract_metrics(result)` (`core/agent.py:304–318`) already derives `total_tokens`, `input_tokens`, `output_tokens`, `total_cycles`, `total_duration`, `tool_usage` from strands `AgentResult.metrics.get_summary()`; `Agent.last_metrics` + `AgentState.last_metrics` were added in the archived `widget-input-progress` change. The TUI accumulates `self._total_tokens_used` from it (app.py:778–789).
- `AgentResponse` carries `tokens_used`, `latency_ms`, `cost_usd`, `tool_calls`, `success`, `error`. **`cost_usd` is never computed** (always 0.0) even though `ProviderModel.cost_input`/`cost_output` (per 1M tokens) exist in `PROVIDER_CATALOG` — cost is computable from tokens + catalog.
- `Session`/`Message`/`Task`/`TokenUsage` models (`core/models.py`) have token/cost accounting fields (`total_tokens`, `total_cost_usd`, `tokens`, `cost_usd`) — cost fields never populated.
- `Provider` has `retry()` with `_extract_status` (429/503/5xx classification) and `FallbackProvider.complete` failover (`core/provider.py:537–552`) — natural retry/failover metric points, currently only one `logger.warning`.
- CLI `run.py:83–89` already measures latency via `time.monotonic()` around `agent.run()`.

### Logfire / OpenTelemetry status

- `logfire` is **NOT a direct dependency** (`pyproject.toml` has no logfire/otel entry), but **logfire 4.39.0 (with `httpx` extra) and `opentelemetry-api` 1.44.0 are already installed as transitive deps** of `pydantic-ai` (`uv.lock`: `pydantic-ai-slim` → `logfire` extra, `opentelemetry-api`). `strands-agents` uses neither.
- OHM executes LLMs through **strands-agents**, not a pydantic-ai `Agent` — so `logfire.instrument_pydantic_ai()` would NOT capture OHM's agent calls; only HTTP-level (`instrument_httpx`) or manual spans would.
- README declares the intent: "Observability | OpenTelemetry | Standardized tracing and metrics" (line 232), Prometheus-style metric names `ohm.metrics.tokens.input {...}` (lines 441–447), an `ohm observe --export otel|prometheus|json` command (lines 464–475), and "Structured logging — JSON logs with correlation IDs" (line 69). **None of this exists in code**; `ohm observe` is not a registered command (commands: config, cron, doctor, goal, init, loop, mcp, plugin, run, serve, session, skill, skills, status, test_cmd).

### Conventions to preserve

- Output contract: `ohm run` prints the **response to stdout**, diagnostics to stderr — structured logs must never pollute stdout.
- `doctor --json` / `status --json` already establish the JSON snapshot pattern.
- Command registration: one file per command in `src/ohm/commands/` with `register(registry)` (auto-discovered by `commands/__init__.py:register_all`).
- Config priority: env > project `.ohm/config.yaml` > global `~/.ohm/config.yaml` > defaults.
- Strict TDD: `uv run pytest`; tests live in `tests/` with class-based groups; no coverage/linter configured.

## Affected Areas

- `src/ohm/core/config.py` — extend `OHMConfig` with log-format/metrics keys (e.g. `log_format`, `metrics_enabled`); `OHM_LOG_LEVEL` already present.
- `src/ohm/core/` (new `observability.py` or `metrics.py`) — logging bootstrap (level + JSON formatter) and in-process metrics registry; the "Observability Layer" from README's architecture diagram.
- `src/ohm/core/agent.py` — emit structured records/metrics at run/stream boundaries (success, latency, tokens, cycles, tool_usage); optionally thread a correlation ID through `run()`/`stream()`.
- `src/ohm/core/provider.py` — record retry attempts, transient statuses, and failover events in `retry()` / `FallbackProvider.complete`.
- `src/ohm/cli/main.py` / `src/ohm/cli/registry.py` — apply logging config at entry point before dispatch; potential global flags (`--log-level`, `--log-format=json`).
- `src/ohm/cli/app.py` — decide fate of the 13 `self.log()` devtools calls (keep as debug, or mirror to structured logger); `_stream_agent_response` is the main metric emission site.
- `src/ohm/commands/run.py`, `status.py`, `doctor.py` — surface metrics (doctor/status `--json` sections; run keeps stdout clean).
- `src/ohm/commands/observe.py` (new, optional) — README's `ohm observe --export` command, only if export is in scope.
- `src/ohm/core/models.py` — cost computation hook (`cost_usd` from catalog prices) if cost metrics are included.
- `pyproject.toml` — only if logfire/OTel is promoted to a direct dependency (not required for the default path).
- `tests/` — new tests: logging bootstrap, JSON formatter, metrics registry, agent metric emission (mock strands).

## Approaches

1. **stdlib `logging` + JSON formatter, wire `OHM_LOG_LEVEL` (zero new deps)** — bootstrap a root logger config in core (`logging.basicConfig(level=cfg.log_level)` + optional `JSONFormatter` emitting one JSON object per record with timestamp/level/logger/message/fields). Emit metrics as structured log records (JSONL) with README's `ohm.metrics.*` names.
   - Pros: zero new dependencies; uses existing logger calls; `OHM_LOG_LEVEL`/`.env` surface already declared; fully TDD-testable; stdout contract untouched; small diff.
   - Cons: no trace correlation across async without extra work; no dashboards/export; JSON formatter hand-rolled; metric queries need a consumer (doctor/status JSON).
   - Effort: **Low–Medium**.

2. **Logfire** (already installed as a transitive dep via pydantic-ai) — promote to direct dependency, `logfire.configure()` at entry point, structured `logfire.info('msg {key}', key=...)` calls + `logfire.metric_counter/histogram`, optional cloud/OTLP export.
   - Pros: real observability platform; spans + metrics + logs in one; README's OTel story aligns; minimal new machinery (SDK present).
   - Cons: **must be promoted to a direct dep** (relying on transitive is fragile); OHM uses strands-agents so `instrument_pydantic_ai()` does NOT capture LLM spans — only HTTP/manual spans; SaaS/`LOGFIRE_TOKEN` for cloud export (privacy consideration for an "enterprise" tool); replacing stdlib loggers across modules is a larger diff.
   - Effort: **Medium** (console/local) to **High** (cloud export + auth UX).

3. **structlog** — standard structured logging library binding to stdlib.
   - Pros: best-in-class ergonomics, JSON out, stdlib-compatible.
   - Cons: new dependency; still needs a separate metrics story; same no-dashboard gap as approach 1.
   - Effort: **Medium**.

4. **Custom in-process metrics registry + JSONL emission** (optionally layered on approach 1) — `MetricsRegistry` with counters/histograms/gauges (session count, runs, latency, tokens, retries, failovers), exposed via `ohm doctor --json` / `ohm status` and/or written as JSONL to a metrics file.
   - Pros: no deps; matches README's metric names; surfaces through existing `--json` commands; trivially testable; export-ready (JSONL → OTLP/Prometheus later).
   - Cons: reinvents a small wheel; no dashboards until an exporter exists; needs a home for state (module-level registry vs session file).
   - Effort: **Medium**.

5. **Direct OpenTelemetry SDK** (README's stated architecture table choice) — add `opentelemetry-sdk` + exporters, meters/`Counter`/`Histogram`, OTLP/Prometheus export.
   - Pros: matches README architecture ("Observability | OpenTelemetry"); standard; future-proof for `ohm observe --export otel`.
   - Cons: `opentelemetry-api` present but **SDK/exporters not installed**; heaviest dependency and boilerplate; overkill for the current single-process CLI/TUI surface.
   - Effort: **High**.

## Recommendation

**Two-stage, zero-new-dependency default:**

- **Stage 1 (this change): stdlib logging + JSONL metrics.** Add a small `ohm/core/observability.py` (the README "Observability Layer" made real) that (a) bootstraps Python logging from `OHMConfig` — level from the already-dead `OHM_LOG_LEVEL`, optional `log_format=json` adding a JSON formatter, wired at the CLI/TUI entry point; and (b) provides a tiny `Metrics` registry (counters/histograms) emitting README's `ohm.metrics.*` records. Instrument `agent.run/stream` (success, latency, tokens, cycles) and `provider.retry`/`FallbackProvider` (attempts, transient statuses, failovers); surface a metrics snapshot through `ohm doctor --json` and `ohm status`. Keep stdout clean; logs/metrics go to stderr or a file. Optionally compute `cost_usd` from tokens + `PROVIDER_CATALOG` prices since the data is already there.
- **Stage 2 (future, same roadmap item or follow-up): optional exporter.** Add `ohm observe --export jsonl|otel|prometheus` later, wrapping approach 1's JSONL records — this is where Logfire (already installed) or a direct OTLP exporter slots in behind a config switch, without churn to the core instrumentation.

Rationale: the codebase already has the config surface (`OHM_LOG_LEVEL`), the metric data (`_extract_metrics`, latency timers, catalog prices), and the output conventions (`--json`). Approach 1 + 4 delivers the roadmap item with no dependency risk, stays inside the 400–800 line PR budget, and is fully strict-TDD testable. It also leaves the door open for Logfire/OTel export without locking the default path to a SaaS dependency.

## Risks

- **CRITICAL — log/UI interleaving**: `ohm run` stdout is the agent response; naive log-to-stdout would corrupt the output contract. Logs/metrics MUST go to stderr or a file (README's `observe --export json` suggests a file/pipe).
- **WARNING — `self.log()` is Textual devtools, not logging**: routing or "fixing" these naively breaks nothing but changes nothing either; decide explicitly whether to keep them as debug-only or mirror to the structured logger.
- **WARNING — logfire is transitive only**: any proposal that uses logfire directly must promote it to `pyproject.toml` first (dependency-pruning would otherwise silently remove it).
- **WARNING — cost metric has no data source today**: `cost_usd` is 0.0 everywhere; emitting `ohm.metrics.cost.usd` without wiring catalog prices would emit zeros. Either compute it or defer the metric.
- **WARNING — sensitive data in logs**: prompts may contain secrets/keys; structured logging must never emit prompt bodies or API keys at INFO (log length/metadata only).
- **WARNING — no correlation IDs exist**: README promises "correlation IDs across agent runs"; producing them requires threading an id through `Agent.run/stream` — a behavioral change to `AgentResponse`/events that must be scoped in proposal.
- **WARNING — PR budget**: even the modest Stage 1 touches ~8 files; must stay under the 400-line budget or be sliced (logging bootstrap + metrics registry as one work unit, agent/provider instrumentation as another).

## Ready for Proposal

Yes. Evidence is complete: current state, dead config, available metric data, and README commitments are all verified in code. The orchestrator should tell the user the recommended shape — zero-dep stdlib logging + JSONL metrics registry (Stage 1) with an optional Logfire/OTLP export path (Stage 2) — and ask whether `ohm observe --export` and cost metrics are in scope for THIS change or deferred, plus whether logfire should be promoted to a direct dependency.
