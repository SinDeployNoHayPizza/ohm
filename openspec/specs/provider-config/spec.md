# Provider Configuration Specification

> **Status**: IMPLEMENTED & STABLE — synced from change `provider-abstraction-layer` (archived 2026-07-31). Verify verdict: PASS WITH WARNINGS; post-archive follow-ups tracked in Engram `sdd/provider-abstraction-layer/archive-report`.

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
