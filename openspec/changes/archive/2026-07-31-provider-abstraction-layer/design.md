# Design: Provider Abstraction Layer

## Technical Approach

Factory/Wrapper pattern: abstract `Provider` base class with `create_model()` contract, 7 per-provider subclasses encapsulating strands model construction. `OHMConfig.resolve_provider(name)` returns a configured Provider. Agent calls `provider.create_model()` instead of dynamic imports. Retry is a composable decorator; failover wraps two providers.

## Architecture Decisions

### Decision: Class Hierarchy

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `abc.ABC` + subclasses | Explicit contract; shared retry/status in base | **Adopted** |
| `typing.Protocol` | Duck-typing more Pythonic but no shared behavior | Rejected — retry and health are base-class concerns |

Base `Provider` owns `create_model()`, `get_models()`, `check_health()`, `get_status()`. Current `ProviderStatus`, `ProviderModel`, `ProviderConfig` dataclasses from skeleton are kept and extended.

### Decision: Provider Subclass Mapping

| Provider | Subclass | Strands Model | Env Vars |
|----------|----------|---------------|----------|
| `anthropic` | `AnthropicProvider` | `AnthropicModel` | `ANTHROPIC_API_KEY` |
| `openai` | `OpenAIClientProvider` | `OpenAIModel` | `OPENAI_API_KEY` |
| `nvidia-nim` | `OpenAICompatibleProvider` | `OpenAIModel` + `base_url` | `NVAPI_KEY` |
| `xiaomi-mimo` | `OpenAICompatibleProvider` | `OpenAIModel` + `base_url` | `MIMO_API_KEY` |
| `gemini` | `GeminiProvider` | `GeminiModel` | `GEMINI_API_KEY` |
| `ollama` | `OllamaProvider` | `OllamaModel` | None |
| `bedrock` | `BedrockProvider` | `BedrockModel` | `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` |

`OpenAICompatibleProvider` reuses `OpenAIModel` with a custom `base_url` — single subclass handles all OpenAI-compatible backends.

Name alignment: `google` → `gemini`, `ollama-cloud` → `ollama`, `nvidia` → `nvidia-nim`, `local` → `ollama` (all now match agent.py `_PROVIDER_MODEL_MAP` keys).

### Decision: Factory Location

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `OHMConfig.resolve_provider()` | Single import, spec requirement | **Adopted** |
| Separate `registry.py` | Cleaner but more modules | Rejected — not worth the indirection for 7 statically-known providers |

`OHMConfig.resolve_provider(name)` is a static method mapping provider name → subclass, constructing with `ProviderConfig` from config data + env vars.

### Decision: Retry as Decorator

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Decorator on `complete()` | Composable, testable in isolation | **Adopted** |
| Mixin on Provider subclass | Pollutes inheritance chain | Rejected |
| Wrapper class | Works but more ceremony | Rejected |

Exponential backoff (base 2s, max 30s), configurable `max_retries` (default 3). Retries only on 429/503/5xx.

### Decision: Failover

`FallbackProvider(primary, secondary)` implements `Provider` by delegating to primary, catching retry exhaustion, then delegating to secondary. Logs each failover event.

### Decision: TUI Migration — Static Model Data

`FAKE_PROVIDERS` removed entirely. TUI gets model data from `OHMConfig.available_providers` + `Provider.get_models()`. Provider models are defined as static `ProviderConfig` constants (no live API) — same data FAKE_PROVIDERS held, but now in the type system.

### Decision: AgentConfig Merge

`AgentConfig` fields merge into `OHMConfig` (provider, model, max_tokens, temperature, sandbox, tools, system_prompt). `Agent.__init__` accepts either `OHMConfig` directly or compatible kwargs. `AgentConfig` dataclass is deprecated but kept as a thin wrapper for backward compat during migration.

## Data Flow

```
OHMConfig.resolve_provider("anthropic")
  → AnthropicProvider(ProviderConfig(api_key=...))
    → create_model() → AnthropicModel → strands.Agent

Agent._ensure_agent()
  → self._provider.create_model(model_id, **config)
  → strands model → strands.Agent(model=model)

TUI model_selector
  → OHMConfig.available_providers → Provider.get_models() → display

doctor.py
  → OHMConfig.available_providers → Provider.check_health() → report
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/ohm/core/provider.py` | Rewrite | Provider ABC + 7 subclasses + retry decorator + FallbackProvider |
| `src/ohm/core/agent.py` | Modify | Remove `_resolve_model()`, use `Provider.create_model()`; merge AgentConfig into OHMConfig |
| `src/ohm/core/config.py` | Modify | Add `resolve_provider()` static method; merge AgentConfig fields |
| `src/ohm/core/models.py` | Modify | Deprecate `ProviderInfo` (replaced by `Provider.get_status()`) |
| `src/ohm/utils/fake_data.py` | Modify | Remove `FAKE_PROVIDERS`, `FAKE_TOKEN_USAGE`, `FAKE_STATUS` exports |
| `src/ohm/cli/app.py` | Modify | Use `Provider.get_models()` for context window resolution |
| `src/ohm/cli/widgets/model_selector.py` | Modify | Use `Provider.get_models()` + real status |
| `src/ohm/cli/widgets/sidebar.py` | Modify | Remove `_PROVIDER_DISPLAY`, use `Provider.display_name` |
| `src/ohm/cli/screens/settings.py` | Modify | Use real available_providers from config |
| `src/ohm/commands/doctor.py` | Modify | Use `Provider.check_health()` |
| `tests/test_provider.py` | New | TDD tests (unit + integration + mocked retry/failover) |

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Each subclass instantiation, `create_model()`, `get_models()`, `check_health()` | Parametrized per provider; mock env vars |
| Integration | `Provider.create_model()` produces correct strands types | Real import test (strands installed in CI) |
| Mocked | Retry decorator (429 → retry, 400 → fail), FallbackProvider failover | Mock strands model/API call to inject failures |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollback

- Phase 1: Rewrite `provider.py` with all subclasses + retry + failover. No consumers changed. (Safe — provider.py is currently unused.)
- Phase 2: Wire `OHMConfig.resolve_provider()` — add method, no consumers yet.
- Phase 3: Migrate `Agent._ensure_agent()` — critical flip. Rollback: keep `_resolve_model()` alongside for one release.
- Phase 4: Migrate TUI and doctor — each file independently.
- Phase 5: Remove `FAKE_PROVIDERS` and `ProviderInfo`.

Rollback: revert agent.py to `_resolve_model()`, restore `fake_data.py` exports. New `provider.py` stays unused — same as pre-change.

## Open Questions

None.
