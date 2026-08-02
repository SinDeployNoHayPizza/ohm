# Delta for Structured Logging and Metrics

> Change-level spec (Stage 1). Per-domain deltas: `observability` (full spec at `openspec/specs/observability/spec.md`), `provider-config` (delta at `specs/provider-config/spec.md`). Deferred: export, correlation IDs, real cost, `self.log()` re-wiring.

## ADDED Requirements

### Requirement: Log Level Wiring (OBS-1)

The system MUST apply the configured `log_level` at CLI/TUI startup; `OHM_LOG_LEVEL` MUST override it.

#### Scenario: Env var raises level

- GIVEN `OHM_LOG_LEVEL=DEBUG`, config `log_level: INFO`
- WHEN the CLI/TUI starts
- THEN the root logger level is DEBUG
- AND the agent-init INFO record reaches stderr

#### Scenario: Default suppresses INFO

- GIVEN no `OHM_LOG_LEVEL`, config `log_level: WARNING`
- WHEN the CLI/TUI starts
- THEN the root logger level is WARNING
- AND INFO records are suppressed

### Requirement: JSON Log Format (OBS-2)

With `log_format: json`, the system MUST emit one JSON object per log record (timestamp, level, logger, message, metadata). Default output MUST be plain text.

#### Scenario: JSON lines

- GIVEN config `log_format: json`
- WHEN a log record is emitted
- THEN each stderr line is a valid JSON object with timestamp, level, logger, message

#### Scenario: Text default

- GIVEN config without `log_format`
- WHEN a log record is emitted
- THEN output is human-readable plain text

### Requirement: Log Routing — stdout Purity (OBS-3)

Logs and metrics MUST go only to stderr or a configured log file — NEVER to `ohm run` stdout; stdout MUST contain only the agent response.

#### Scenario: Response-only stdout

- GIVEN `ohm run` with DEBUG logging
- WHEN the agent produces a response
- THEN stdout contains exactly the response
- AND logs appear on stderr or the log file

#### Scenario: No JSON pollution

- GIVEN `log_format: json` during `ohm run`
- WHEN logs are emitted mid-run
- THEN no log line appears on stdout

### Requirement: Metrics Registry (OBS-4)

The system MUST provide an in-process registry with counters and histograms under `ohm.metrics.*` names. With `metrics_enabled: false` it MUST record nothing.

#### Scenario: Records accumulate

- GIVEN an enabled registry
- WHEN a counter is incremented and a histogram records a latency
- THEN the snapshot returns those values

#### Scenario: Disabled registry

- GIVEN config `metrics_enabled: false`
- WHEN metrics are emitted
- THEN the snapshot is empty

### Requirement: Agent Instrumentation (OBS-5)

The agent MUST record, on run/stream completion without altering results: success/failure, latency (ms), total/input/output tokens, cycles, tool usage.

#### Scenario: Successful run

- GIVEN an agent run that succeeds
- WHEN the snapshot is read
- THEN success, latency, tokens, cycles, tool usage are recorded

#### Scenario: Failed run

- GIVEN an agent run that raises
- WHEN instrumentation runs
- THEN a failure counter is incremented
- AND instrumentation never propagates an exception

### Requirement: Provider Instrumentation (OBS-6)

The provider layer MUST record retry attempts, transient statuses (429/503/5xx), and failover events.

#### Scenario: Retry recorded

- GIVEN a 429 that succeeds on retry
- WHEN the snapshot is read
- THEN retry-attempt and transient-status counts reflect it

#### Scenario: Failover recorded

- GIVEN FallbackProvider failover to the secondary
- WHEN the snapshot is read
- THEN a failover counter is incremented

### Requirement: Cost Metric Slot (OBS-7)

The system MUST expose `ohm.metrics.cost.usd` as a fixed 0.0 value; no cost data source exists in Stage 1.

#### Scenario: Zero slot

- GIVEN any metrics snapshot
- WHEN `ohm.metrics.cost.usd` is read
- THEN it equals 0.0

### Requirement: Sensitive Data Protection (OBS-8)

Logs and metrics MUST NOT contain prompt content or API keys; they MAY carry only metadata, lengths, token counts, labels.

#### Scenario: Key-like text in prompt

- GIVEN a DEBUG run with an API-key-like string in the prompt
- WHEN log records are emitted
- THEN none contain the prompt text or the key value
- AND records carry lengths and metadata only

#### Scenario: Error records

- GIVEN an error logged with exception context
- WHEN the formatted record is inspected
- THEN no API key material is present

### Requirement: Metrics Snapshot Surface (OBS-9)

`ohm doctor --json` and `ohm status --json` MUST include a `metrics` section from the registry snapshot.

#### Scenario: Populated snapshot

- GIVEN a session with recorded metrics
- WHEN `ohm doctor --json` or `ohm status --json` runs
- THEN output includes a populated `metrics` section

#### Scenario: Empty snapshot present

- GIVEN no metrics recorded
- WHEN `ohm status --json` runs
- THEN the `metrics` section is present with zero values
