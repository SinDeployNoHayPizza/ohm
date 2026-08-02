# Delta for Provider Configuration

## ADDED Requirements

### Requirement: Observability Configuration Keys (PC-1)

OHMConfig MUST accept `log_format` (`text` default | `json`) and `metrics_enabled` (boolean, default `true`) keys, MUST apply the existing `log_level` at bootstrap, and MUST keep the `OHM_LOG_LEVEL` environment variable authoritative over the configured value.

#### Scenario: Unset keys preserve behavior

- GIVEN config without `log_format` or `metrics_enabled`
- WHEN OHMConfig is loaded
- THEN `log_format == "text"`, `metrics_enabled is True`, and prior logging behavior is unchanged

#### Scenario: Env and json applied

- GIVEN `OHM_LOG_LEVEL=DEBUG` and config `log_format: json`
- WHEN OHMConfig is loaded and the CLI/TUI starts
- THEN `log_level == "DEBUG"`, `log_format == "json"`, and the root logger applies both

#### Scenario: Invalid log_format

- GIVEN config `log_format: yaml`
- WHEN OHMConfig is loaded
- THEN `log_format` falls back to `"text"` and a warning is emitted
