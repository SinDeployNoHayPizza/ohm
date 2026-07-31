# Tasks: Provider Abstraction Layer

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~550–700 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1: Foundation → PR 2: Config+Agent → PR 3: TUI/Doctor → PR 4: Cleanup |
| Delivery strategy | auto-forecast |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Provider ABC + 7 subclasses + retry + failover + tests | PR 1 | `uv run pytest tests/test_provider.py -x` | N/A — no consumers yet | Revert provider.py, test_provider.py |
| 2 | Config factory + Agent migration | PR 2 | `uv run pytest tests/test_provider.py tests/test_agent.py -x` | `uv run ohm --help` (import validation) | Revert config.py, agent.py |
| 3 | TUI + doctor use real providers | PR 3 | `uv run pytest tests/ -x` | `uv run ohm doctor` | Revert all cli/ files changed |
| 4 | Remove FAKE_PROVIDERS + deprecate ProviderInfo | PR 4 | `uv run pytest tests/ -x` | `uv run ohm doctor` | Revert fake_data.py, models.py |

## Phase 1: Provider ABC + Core Infrastructure

- [x] 1.1 RED: Test Provider ABC contract + retry (429 retries, 400 fails) + FallbackProvider failover in `tests/test_provider.py`
- [x] 1.2 GREEN: Implement Provider ABC with abstract methods + retry decorator + FallbackProvider in `src/ohm/core/provider.py`
- [x] 1.3 RED: Test all 7 subclass instantiation + create_model + check_health + get_models in `tests/test_provider.py`
- [x] 1.4 GREEN: Implement AnthropicProvider, OpenAIClientProvider, OpenAICompatibleProvider in `src/ohm/core/provider.py`
- [x] 1.5 GREEN: Implement GeminiProvider, OllamaProvider, BedrockProvider in `src/ohm/core/provider.py`
- [x] 1.6 REFACTOR: Deduplicate common patterns, reuse ProviderConfig dataclasses

## Phase 2: Config Factory + Agent Migration

- [x] 2.1 RED: Test OHMConfig.resolve_provider() + available_providers + unknown provider raises ValueError
- [x] 2.2 GREEN: Add resolve_provider(), available_providers to `src/ohm/core/config.py`; merge AgentConfig fields
- [x] 2.3 RED: Test Agent uses Provider.create_model() with mocked provider
- [x] 2.4 GREEN: Replace _resolve_model() with Provider.create_model() in `src/ohm/core/agent.py`; keep old method for compat
- [x] 2.5 REFACTOR: Add deprecation warning to _resolve_model()

## Phase 3: TUI + Doctor Migration

- [x] 3.1 GREEN: Use Provider.get_models() for context window in `src/ohm/cli/app.py`
- [x] 3.2 GREEN: Use Provider.get_models() + real status in `src/ohm/cli/widgets/model_selector.py`
- [x] 3.3 GREEN: Remove _PROVIDER_DISPLAY, use Provider.display_name in `src/ohm/cli/widgets/sidebar.py`
- [x] 3.4 GREEN: Use real available_providers in `src/ohm/cli/screens/settings.py`
- [x] 3.5 GREEN: Use Provider.check_health() in `src/ohm/commands/doctor.py`

## Phase 4: Cleanup

- [x] 4.1 GREEN: Remove FAKE_PROVIDERS, FAKE_TOKEN_USAGE, FAKE_STATUS from `src/ohm/utils/fake_data.py`
- [x] 4.2 GREEN: Deprecate ProviderInfo in `src/ohm/core/models.py`; remove unused ProviderConfig constants from `src/ohm/core/provider.py` (ProviderConfig kept — actively used as PROVIDER_CATALOG, not unused)
