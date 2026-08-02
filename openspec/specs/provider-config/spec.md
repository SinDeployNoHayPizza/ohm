# Provider Configuration Specification

> **Status**: IMPLEMENTED & STABLE — synced from change `provider-abstraction-layer` (archived 2026-07-31). Verify verdict: PASS WITH WARNINGS; post-archive follow-ups tracked in Engram `sdd/provider-abstraction-layer/archive-report`.
> Extended by change `structured-logging-metrics` (archived 2026-08-02): PC-1 Observability Configuration Keys merged (see `openspec/changes/archive/2026-08-02-structured-logging-metrics/archive-report.md`).

## Purpose

Integrate provider lifecycle with OHMConfig — enabling consistent provider resolution, environment variable mapping, and availability discovery.

## Requirements

### Requirement: Provider Resolution from Config

OHMConfig MUST provide `resolve_provider(name)` returning a configured Provider instance.

#### Scenario: Resolve known provider
- GIVEN OHMConfig with `provider: "openai"`
- WHEN `resolve_provider("openai")` is called
- THEN it returns an OpenAIClientProvider with OPENAI_API_KEY

#### Scenario: Custom base_url for OpenAI-compatible
- GIVEN OHMConfig with `provider: "nvidia-nim"` and `base_url: "https://nim.example.com"`
- WHEN `resolve_provider("nvidia-nim")` is called
- THEN it returns an OpenAICompatibleProvider with the custom base_url

#### Scenario: Unknown provider raises error
- GIVEN OHMConfig
- WHEN `resolve_provider("nonexistent")` is called
- THEN it raises ValueError

### Requirement: Environment Variable Mapping

Each provider MUST map its required credentials from standard environment variable names.

#### Scenario: Provider reads its env var
- GIVEN ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, NVAPI_KEY, MIMO_API_KEY, and AWS_ACCESS_KEY_ID are set
- WHEN a provider is resolved
- THEN it reads its corresponding env var for configuration

### Requirement: AgentConfig Merged into OHMConfig

All AgentConfig fields MUST be available directly through OHMConfig — no separate AgentConfig class.

#### Scenario: Agent properties accessible
- GIVEN an OHMConfig instance
- WHEN accessing agent configuration properties
- THEN they are available without a separate AgentConfig object

### Requirement: Provider Availability Discovery

OHMConfig MUST expose `available_providers` listing providers with configured API keys.

#### Scenario: Partial provider configuration
- GIVEN only ANTHROPIC_API_KEY and OPENAI_API_KEY are set
- WHEN `available_providers` is queried
- THEN it returns `["anthropic", "openai"]`

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
