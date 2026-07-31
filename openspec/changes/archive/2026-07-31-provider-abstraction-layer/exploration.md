## Exploration: Provider Abstraction Layer

### Current State

**Provider skeleton exists but is completely orphaned:**
- `src/ohm/core/provider.py` defines `Provider`, `ProviderConfig`, `ProviderModel`, `ProviderStatus` — but is **never imported or used** by any production code
- The `Provider.complete()` method is a placeholder that sleeps randomly and returns fake data
- Three pre-configured `ProviderConfig` constants (`ANTHROPIC_PROVIDER`, `OPENAI_PROVIDER`, `LOCAL_PROVIDER`) exist but are never referenced

**Agent bypasses the abstraction entirely:**
- `src/ohm/core/agent.py` has `_resolve_model()` that directly imports strands model classes (`AnthropicModel`, `OpenAIModel`, `GeminiModel`, `OllamaModel`, `BedrockModel`) via dynamic import
- Each provider has hardcoded kwargs (env var names, `max_tokens`, `temperature`, `params`)
- No shared interface, no retry, no fallback, no health checking
- The `Agent` class creates its own `AgentConfig` dataclass (partially duplicating `OHMConfig` fields)

**Config has provider awareness but never produces a Provider:**
- `OHMConfig` stores `provider` string and `model` string
- `api_key_for(provider)` reads env vars from `_API_KEY_ENV` mapping
- `available_providers` lists providers with configured keys
- But these are never used to construct a `Provider` instance — they remain strings

**TUI uses fake_data.py, not the Provider class:**
- `model_selector.py`, `settings.py`, `app.py` all import `FAKE_PROVIDERS` from `fake_data.py`
- `FAKE_PROVIDERS` has 6 providers: anthropic, openai, google, nvidia, ollama-cloud, local
- **Misalignment**: agent.py supports `gemini` and `bedrock`; fake_data has `google` and `nvidia`
- sidebar.py has its own hardcoded `_PROVIDER_DISPLAY` dict for name resolution

**No test coverage for provider at all:**
- `test_provider.py` does NOT exist (only referenced in fake_data's file tree as mock content)
- No tests for Provider class, ProviderConfig, ProviderModel, ProviderStatus

**Error handling is bare:**
- `_resolve_model()` raises `ValueError` for unknown providers, `RuntimeError` for import failures
- `Agent.run()` catches `Exception` broadly and returns `success=False`
- No retry logic, no fallback between providers, no rate limiting, no health checking

### Affected Areas

- `src/ohm/core/provider.py` — The core target; complete rewrite from placeholder to real abstraction
- `src/ohm/core/agent.py` — Must use Provider instead of direct _resolve_model()
- `src/ohm/core/config.py` — May need ProviderConfig integration (bootstrap from OHMConfig)
- `src/ohm/core/models.py` — `ProviderInfo` may be deprecated or merged into Provider internals
- `src/ohm/utils/fake_data.py` — Should be replaced by real Provider instances; FAKE_PROVIDERS deprecated
- `src/ohm/cli/app.py` — `_resolve_context_window()` uses FAKE_PROVIDERS; must use Provider
- `src/ohm/cli/widgets/model_selector.py` — Uses FAKE_PROVIDERS; must use Provider.get_models()
- `src/ohm/cli/widgets/sidebar.py` — Uses hardcoded _PROVIDER_DISPLAY; could use Provider.display_name
- `src/ohm/cli/screens/settings.py` — Uses FAKE_PROVIDERS[0] hardcoded
- `src/ohm/commands/doctor.py` — `_check_providers()` reads env vars directly; should probe real providers
- `tests/test_agent.py` — Tests for _resolve_model() may need update
- `tests/test_provider.py` — MUST be created (first-class coverage)

### Approaches

1. **Provider as Factory/Wrapper** — Provider wraps the strands model creation and completion
   - Pros: Single responsibility per Provider; Agent delegates cleanly; easy to add retry/fallback at Provider level; testable in isolation
   - Cons: Each provider needs its own subclass (AnthropicProvider, OpenAIProvider, etc.); more classes
   - Effort: Medium

2. **Provider as Registry/Facade** — Centralized ProviderRegistry that manages all providers, resolves models, handles API keys
   - Pros: Single entry point for all provider operations; easy to add new providers; central configuration
   - Cons: Can become a god class; harder to test individual provider behavior; bloated interface
   - Effort: Medium

3. **Provider as Protocol/Interface only** — Define a Protocol (or ABC) for Provider, keep the model resolution in a lightweight function or per-provider module
   - Pros: Pythonic; minimal interface surface; existing _resolve_model can adapt gradually; low migration cost
   - Cons: Less structured; still need somewhere to put retry/fallback/health logic; may end up with utility soup
   - Effort: Low-Medium

### Recommendation

**Approach 1 (Provider as Factory/Wrapper)** — with a base Provider class and per-provider subclasses. The base Provider owns the interface (`complete()`, `get_models()`, `get_status()`), and each provider subclass encapsulates the strands model creation and API call logic. `Agent._ensure_agent()` uses a ProviderFactory (or the Provider subclass directly) to get the right Provider, then delegates `complete()` / streaming to it.

Rationale:
- Replaces the current _resolve_model() spaghetti with clean per-provider classes
- Each provider subclass handles its own API key lookup, model kwargs, and error mapping
- Retry/fallback logic lives in the base Provider or a decorator wrapper, not duplicated per-provider
- TUI widgets can ask the Provider for available models via `provider.get_models()` instead of FAKE_PROVIDERS
- `Config` can provide a `ProviderRegistry` or `resolve_provider(name) -> Provider` method
- Migratable: start by extracting _resolve_model per-provider logic into subclasses, then gradually wire them into Agent

### Risks

- **API key management**: Provider subclasses must know how to get API keys. Currently config.py has `_API_KEY_ENV`; Provider shouldn't duplicate that. Config should resolve keys and pass them in ProviderConfig.
- **TUI data source migration**: FAKE_PROVIDERS is deeply ingrained in 6+ files. A real Provider query (e.g., list models) requires an API call or a static config — can't just swap FAKE_PROVIDERS for Provider.get_models() without a non-network fallback.
- **AgentConfig vs OHMConfig overlap**: AgentConfig duplicates OHMConfig fields. The Provider abstraction should clarify which config is authoritative or merge them.
- **strands version coupling**: _resolve_model() hardcodes strands class names and kwargs. Provider subclasses will inherit this coupling. If strands changes APIs, Provider needs update too.
- **Backward compatibility**: Existing configs with `provider: "anthropic"` must keep working. The `provider` string → Provider subclass resolution must be stable.

### Ready for Proposal

**Yes.** The problem space is well-understood, the codebase impact is clear, and the architectural options are defined. The orchestrator should proceed with sdd-propose using Approach 1 (Provider as Factory/Wrapper) as the recommended direction, with the following caveats:
- Confirm that the provider string → subclass mapping matches `_PROVIDER_MODEL_MAP` keys (anthropic, openai, gemini, ollama, bedrock) — NOT the fake_data names (google, nvidia, ollama-cloud, local)
- Decide whether to keep `AgentConfig` standalone or merge it into `OHMConfig`
- Decide on retry/fallback strategy before implementation
