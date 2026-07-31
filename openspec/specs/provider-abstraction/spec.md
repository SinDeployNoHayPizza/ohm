# Provider Abstraction Specification

> **Status**: IMPLEMENTED & STABLE — synced from change `provider-abstraction-layer` (archived 2026-07-31). Verify verdict: PASS WITH WARNINGS; post-archive follow-ups tracked in Engram `sdd/provider-abstraction-layer/archive-report`.

## Purpose

Abstract LLM provider model construction, health checking, and lifecycle behind a uniform interface — eliminating ad-hoc per-provider logic across the codebase.

## Requirements

### Requirement: Base Provider Interface

The Provider base class MUST define `create_model()`, `get_models()`, `check_health()`, and `get_status()`.

#### Scenario: Subclass satisfies contract
- GIVEN a concrete Provider subclass
- WHEN instantiated
- THEN `create_model()` returns a strands Model, `get_models()` returns `list[ProviderModel]`, `check_health()` returns ProviderStatus, and `get_status()` returns a dict

### Requirement: Per-Provider Model Resolution

Each subclass MUST construct the correct strands model using provider-specific configuration.

#### Scenario: Anthropic
- GIVEN AnthropicProvider with ANTHROPIC_API_KEY set
- WHEN `create_model()` is called
- THEN it returns a strands AnthropicModel with configured max_tokens and temperature

#### Scenario: OpenAI and OpenAI-compatible
- GIVEN an OpenAIClientProvider with OPENAI_API_KEY (or NVAPI_KEY / MIMO_API_KEY for compatible providers)
- WHEN `create_model()` is called
- THEN it returns a strands OpenAIModel; for nvidia-nim and xiaomi-mimo, the model uses a custom base_url

#### Scenario: Ollama
- GIVEN OllamaProvider with model_id only
- WHEN `create_model()` is called
- THEN it returns a strands OllamaModel (no API key required)

#### Scenario: Bedrock
- GIVEN BedrockProvider with AWS credentials in the environment
- WHEN `create_model()` is called
- THEN it returns a strands BedrockModel

### Requirement: Health Checking

`check_health()` MUST verify required environment variables exist and the model is instantiable.

#### Scenario: Healthy provider
- GIVEN a provider with all required env vars present
- WHEN `check_health()` is called
- THEN it returns ProviderStatus.HEALTHY

#### Scenario: Missing env vars
- GIVEN a provider missing a required env var
- WHEN `check_health()` is called
- THEN it returns ProviderStatus.UNHEALTHY with a descriptive message

### Requirement: Retry on Transient Errors

Retry MUST wrap `complete()` with exponential backoff on 429, 503, and 5xx responses.

#### Scenario: Transient error retried
- GIVEN a provider call returning 429
- WHEN retried
- THEN it retries with exponential backoff up to N attempts before propagating

#### Scenario: Non-transient not retried
- GIVEN a provider call returning 400
- WHEN attempted
- THEN it fails immediately without retry

### Requirement: Failover

`with_fallback(primary, secondary)` MUST delegate to the secondary provider when the primary exhausts all retries.

#### Scenario: Primary fails, fallback succeeds
- GIVEN primary and secondary providers
- WHEN the primary fails all retries
- THEN the secondary provider is invoked
