# Proposal: Provider Abstraction Layer

## Intent

OHM's 7 supported LLM providers are configured ad-hoc — `agent.py` hardcodes per-provider model imports and kwargs, TUI uses misaligned `FAKE_PROVIDERS`, and `doctor.py` probes env vars directly. A unified Provider abstraction eliminates duplication, enables health checking, retry/failover, and consistent provider lifecycle across the stack.

## Scope

### In Scope
- Provider base class: `create_model()`, `get_models()`, `check_health()`, `get_status()`
- 7 per-provider subclasses: anthropic, openai, gemini, ollama, bedrock, nvidia-nim, xiaomi-mimo
- Config factory `resolve_provider(name)` integrated with OHMConfig
- Agent migration: use `Provider.create_model()` instead of `_resolve_model()`
- AgentConfig merged into OHMConfig
- Retry decorator for transient errors (429, 503, 5xx)
- Basic failover — fallback to next available provider
- TUI migration: model_selector, sidebar, settings use real Provider instances
- Doctor command uses `Provider.check_health()`
- Remove `FAKE_PROVIDERS` from `fake_data.py`
- Tests: `test_provider.py` (TDD, ≥80% coverage)

### Out of Scope
- LiteLLM backend (deferred)
- Streaming health checks
- Multi-key rotation per provider
- Usage quotas and billing aggregation
- Provider auto-discovery

## Capabilities

### New Capabilities
- **provider-abstraction**: Core Provider base class, per-provider subclasses, factory resolution, health checks, model listing
- **provider-config**: Configuration integration — provider config from OHMConfig, env var mapping, custom `base_url` support for OpenAI-compatible providers

### Modified Capabilities
None — first time spec-ing these.

## Approach

Factory/Wrapper pattern: Base `Provider` with abstract `create_model()`. Each provider subclass encapsulates its strands model construction. Config provides `resolve_provider(name) -> Provider`. Agent calls `provider.create_model()` instead of dynamic imports. Retry is a composable decorator/wrapper around `complete()`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/ohm/core/provider.py` | Rewrite | Provider base + 7 subclasses + retry |
| `src/ohm/core/agent.py` | Modify | Replace `_resolve_model()` with `Provider.create_model()` |
| `src/ohm/core/config.py` | Modify | Add `resolve_provider()`, merge AgentConfig |
| `src/ohm/core/models.py` | TBD | `ProviderInfo` may merge/deprecate |
| `src/ohm/utils/fake_data.py` | Modify | Remove `FAKE_PROVIDERS` |
| `src/ohm/cli/app.py` | Modify | Use real providers for context window |
| `src/ohm/cli/widgets/model_selector.py` | Modify | Use real providers |
| `src/ohm/cli/widgets/sidebar.py` | Modify | Remove `_PROVIDER_DISPLAY`, use real status |
| `src/ohm/cli/screens/settings.py` | Modify | Use real provider list |
| `src/ohm/commands/doctor.py` | Modify | Use `Provider.check_health()` |
| `tests/test_provider.py` | New | TDD tests, ≥80% coverage |
| `tests/test_agent.py` | Modify | Update if `_resolve_model()` changes |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Provider names still misaligned after migration | Low | Use exploration's name audit as spec input |
| Retry logic masks real failures | Low | Configure max retries + exponential backoff + logging |
| strands API changes break model construction | Low | Pin strands version, CI catches upgrades |

## Rollback Plan

Revert `agent.py` to `_resolve_model()` and restore `fake_data.py` `FAKE_PROVIDERS`. New `provider.py` stays unused — same as pre-change state.

## Dependencies

None.

## Success Criteria

- [ ] All 7 providers instantiable with correct strands model binding
- [ ] Agent uses `Provider.create_model()` — `_resolve_model()` removed
- [ ] TUI shows real provider status, not `FAKE_PROVIDERS`
- [ ] `doctor` command reports real provider connectivity
- [ ] Retry mechanism tested with mocked failures
- [ ] All existing tests pass
- [ ] ≥80% test coverage on new provider code
