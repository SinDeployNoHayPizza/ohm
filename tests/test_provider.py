"""Tests for OHM provider abstraction layer."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from ohm.core.provider import (
    FallbackProvider,
    Provider,
    ProviderConfig,
    ProviderModel,
    ProviderStatus,
    retry,
)


class TestProviderABC:
    """Task 1.1: Provider ABC contract."""

    def test_cannot_instantiate_directly(self):
        """Provider ABC MUST NOT be instantiable directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            Provider(ProviderConfig(name="test", display_name="Test"))  # type: ignore[abstract]


# ── Test helpers for retry ─────────────────────────────────────


class _RetryHarness:
    """Minimal callable to test the retry decorator."""

    def __init__(self, status_codes: list[int]) -> None:
        self.status_codes = status_codes
        self.call_count = 0

    def __call__(self) -> int:
        idx = self.call_count
        self.call_count += 1
        status = self.status_codes[idx] if idx < len(self.status_codes) else 200
        if status >= 400:
            exc = RuntimeError(f"HTTP {status}")
            setattr(exc, "status_code", status)
            raise exc
        return status


class TestRetryDecorator:
    """Task 1.1: Retry decorator behavior."""

    def test_429_retries_then_succeeds(self):
        """A 429 response triggers retry with exponential backoff and eventually succeeds."""
        harness = _RetryHarness([429, 429, 200])

        @retry(max_retries=3)
        def call() -> int:
            return harness()

        result = call()
        assert result == 200
        assert harness.call_count == 3

    def test_503_retries_then_succeeds(self):
        """A 503 response triggers retry."""
        harness = _RetryHarness([503, 503, 200])

        @retry(max_retries=3)
        def call() -> int:
            return harness()

        result = call()
        assert result == 200
        assert harness.call_count == 3

    def test_500_retries_then_succeeds(self):
        """A 5xx response triggers retry."""
        harness = _RetryHarness([500, 200])

        @retry(max_retries=3)
        def call() -> int:
            return harness()

        result = call()
        assert result == 200
        assert harness.call_count == 2

    def test_400_fails_immediately(self):
        """A 4xx other than 429 MUST fail immediately without retry."""
        harness = _RetryHarness([400])

        @retry(max_retries=3)
        def call() -> int:
            return harness()

        with pytest.raises(RuntimeError, match="HTTP 400"):
            call()
        assert harness.call_count == 1

    def test_all_retries_exhausted_raises(self):
        """When all retries are exhausted, the last exception is propagated."""
        harness = _RetryHarness([429, 429, 429, 429])

        @retry(max_retries=3)
        def call() -> int:
            return harness()

        with pytest.raises(RuntimeError, match="HTTP 429"):
            call()
        assert harness.call_count == 3  # initial + 2 retries

    def test_exponential_backoff_at_least_base(self):
        """Each retry waits at least `base` seconds (base=0.05 for tests)."""
        harness = _RetryHarness([429, 200])

        @retry(max_retries=2, base=0.05)
        def call() -> int:
            return harness()

        t0 = time.monotonic()
        result = call()
        elapsed = time.monotonic() - t0

        assert result == 200
        # With base=0.05 and 1 retry, total should be >= 0.025
        # (base * 2^0 * 0.75 min jitter)
        assert elapsed >= 0.01

    def test_max_30s_cap(self):
        """Backoff MUST NOT exceed 30 seconds per wait."""
        from ohm.core.provider import _RETRY_MAX_BACKOFF

        assert _RETRY_MAX_BACKOFF == 30.0

    def test_429_without_status_code_attribute(self):
        """An exception without status_code that contains '429' in message is NOT retried."""

        @retry(max_retries=3)
        def call() -> int:
            raise RuntimeError("Server says 429")

        with pytest.raises(RuntimeError, match="Server says 429"):
            call()


class TestFallbackProvider:
    """Task 1.1: FallbackProvider failover."""

    def test_primary_fails_fallback_succeeds(self):
        """When primary exhausts retries, secondary is invoked."""
        primary_calls = 0
        secondary_calls = 0

        class FailingProvider(Provider):
            def create_model(self):
                return None

            def get_models(self):
                return []

            def check_health(self):
                return ProviderStatus.UNHEALTHY

            def get_status(self):
                return {"name": "fail"}

            def complete(self, model: str, messages: list, **kwargs):
                nonlocal primary_calls
                primary_calls += 1
                raise RuntimeError("HTTP 429")

        class WorkingProvider(Provider):
            def create_model(self):
                return None

            def get_models(self):
                return []

            def check_health(self):
                return ProviderStatus.HEALTHY

            def get_status(self):
                return {"name": "work"}

            def complete(self, model: str, messages: list, **kwargs):
                nonlocal secondary_calls
                secondary_calls += 1
                return {"content": "from secondary", "model": model}

        primary = FailingProvider(ProviderConfig(name="primary", display_name="Primary"))
        secondary = WorkingProvider(ProviderConfig(name="secondary", display_name="Secondary"))
        fallback = FallbackProvider(primary, secondary)

        result = fallback.complete("test-model", [])

        assert result["content"] == "from secondary"
        assert primary_calls >= 1
        assert secondary_calls == 1

    def test_primary_succeeds_secondary_not_used(self):
        """When primary succeeds, secondary is NOT invoked."""
        class WorkingProvider(Provider):
            def create_model(self):
                return None

            def get_models(self):
                return []

            def check_health(self):
                return ProviderStatus.HEALTHY

            def get_status(self):
                return {"name": "work"}

            def complete(self, model: str, messages: list, **kwargs):
                return {"content": "from primary", "model": model}

        primary = WorkingProvider(ProviderConfig(name="primary", display_name="Primary"))
        secondary = WorkingProvider(ProviderConfig(name="secondary", display_name="Secondary"))
        fallback = FallbackProvider(primary, secondary)

        result = fallback.complete("test-model", [])

        assert result["content"] == "from primary"

    def test_fallback_get_models_delegates_to_primary(self):
        """FallbackProvider.get_models() returns primary's models."""
        models = [ProviderModel(id="m1", name="Model 1", context_window=100, cost_input=0, cost_output=0)]

        class ModelsProvider(Provider):
            def __init__(self, config, models_list):
                super().__init__(config)
                self._models = models_list

            def create_model(self):
                return None

            def get_models(self):
                return self._models

            def check_health(self):
                return ProviderStatus.HEALTHY

            def get_status(self):
                return {"name": "test"}

        primary = ModelsProvider(ProviderConfig(name="p", display_name="P"), models)
        secondary = ModelsProvider(ProviderConfig(name="s", display_name="S"), [])
        fallback = FallbackProvider(primary, secondary)

        assert fallback.get_models() == models

    def test_fallback_check_health_checks_primary(self):
        """FallbackProvider.check_health() reflects primary health."""
        class HealthyProvider(Provider):
            def create_model(self):
                return None

            def get_models(self):
                return []

            def check_health(self):
                return ProviderStatus.HEALTHY

            def get_status(self):
                return {"name": "healthy"}

        class UnhealthyProvider(Provider):
            def create_model(self):
                return None

            def get_models(self):
                return []

            def check_health(self):
                return ProviderStatus.UNHEALTHY

            def get_status(self):
                return {"name": "unhealthy"}

        primary = UnhealthyProvider(ProviderConfig(name="p", display_name="P"))
        secondary = HealthyProvider(ProviderConfig(name="s", display_name="S"))
        fallback = FallbackProvider(primary, secondary)

        assert fallback.check_health() == ProviderStatus.UNHEALTHY


# ── Provider subclass helpers ──────────────────────────────────

_A_ENV = {"ANTHROPIC_API_KEY": "sk-ant-test"}
_O_ENV = {"OPENAI_API_KEY": "sk-openai-test"}
_G_ENV = {"GEMINI_API_KEY": "sk-gemini-test"}
_N_ENV = {"NVAPI_KEY": "nvapi-test"}
_M_ENV = {"MIMO_API_KEY": "mimo-test"}
_AWS_ENV = {"AWS_ACCESS_KEY_ID": "AKIATEST", "AWS_SECRET_ACCESS_KEY": "s3cret"}


class TestProviderSubclasses:
    """Task 1.3/1.4/1.5: All 7 provider subclass behaviors."""

    # ── Helper ─────────────────────────────────────────────

    @pytest.fixture
    def config_anthropic(self) -> ProviderConfig:
        return ProviderConfig(
            name="anthropic",
            display_name="Anthropic",
            models=[ProviderModel("claude-sonnet-4-6", "Claude Sonnet 4.6", 200_000, 3.0, 15.0)],
        )

    @pytest.fixture
    def config_openai(self) -> ProviderConfig:
        return ProviderConfig(
            name="openai",
            display_name="OpenAI",
            models=[ProviderModel("gpt-4o", "GPT-4o", 128_000, 2.5, 10.0)],
        )

    @pytest.fixture
    def config_gemini(self) -> ProviderConfig:
        return ProviderConfig(
            name="gemini",
            display_name="Gemini",
            models=[ProviderModel("gemini-2.5-flash", "Gemini 2.5 Flash", 1_000_000, 0.15, 0.60)],
        )

    @pytest.fixture
    def config_ollama(self) -> ProviderConfig:
        return ProviderConfig(
            name="ollama",
            display_name="Ollama",
            models=[ProviderModel("llama3.2", "Llama 3.2", 128_000, 0.0, 0.0)],
        )

    @pytest.fixture
    def config_bedrock(self) -> ProviderConfig:
        return ProviderConfig(
            name="bedrock",
            display_name="Bedrock",
            models=[ProviderModel(
                "global.anthropic.claude-sonnet-4-6",
                "Claude Sonnet 4.6 (Bedrock)",
                200_000,
                3.0,
                15.0,
            )],
        )

    @pytest.fixture
    def config_nvidia(self) -> ProviderConfig:
        return ProviderConfig(
            name="nvidia-nim",
            display_name="NVIDIA NIM",
            base_url="https://nim.example.com",
            models=[ProviderModel("nemotron-70b", "Nemotron 70B", 128_000, 0.80, 3.20)],
        )

    @pytest.fixture
    def config_mimo(self) -> ProviderConfig:
        return ProviderConfig(
            name="xiaomi-mimo",
            display_name="Xiaomi MiMo",
            base_url="https://mimo.example.com",
            models=[ProviderModel("mimo-v2", "MiMo V2", 128_000, 0.50, 2.00)],
        )

    # ── Tests ──────────────────────────────────────────────

    def test_anthropic_instantiation(self, config_anthropic):
        from ohm.core.provider import AnthropicProvider
        prov = AnthropicProvider(config_anthropic)
        assert prov.config.name == "anthropic"

    @patch.dict("os.environ", _A_ENV, clear=False)
    def test_anthropic_create_model(self, config_anthropic):
        from ohm.core.provider import AnthropicProvider
        prov = AnthropicProvider(config_anthropic)
        model = prov.create_model()
        from strands.models.anthropic import AnthropicModel
        assert isinstance(model, AnthropicModel)

    def test_openai_instantiation(self, config_openai):
        from ohm.core.provider import OpenAIClientProvider
        prov = OpenAIClientProvider(config_openai)
        assert prov.config.name == "openai"

    @patch.dict("os.environ", _O_ENV, clear=False)
    def test_openai_create_model(self, config_openai):
        from ohm.core.provider import OpenAIClientProvider
        prov = OpenAIClientProvider(config_openai)
        model = prov.create_model()
        from strands.models.openai import OpenAIModel
        assert isinstance(model, OpenAIModel)

    def test_gemini_instantiation(self, config_gemini):
        from ohm.core.provider import GeminiProvider
        prov = GeminiProvider(config_gemini)
        assert prov.config.name == "gemini"

    @patch.dict("os.environ", _G_ENV, clear=False)
    def test_gemini_create_model(self, config_gemini):
        from ohm.core.provider import GeminiProvider
        prov = GeminiProvider(config_gemini)
        model = prov.create_model()
        from strands.models.gemini import GeminiModel
        assert isinstance(model, GeminiModel)

    @patch.dict("os.environ", {}, clear=True)
    def test_gemini_create_model_without_api_key_no_client_args(self, config_gemini):
        """R3-001 v2: without GEMINI_API_KEY, client_args must be omitted entirely.

        Exercises the api_key-absent branch — client_args must never be
        synthesized (no api_key, and no base_url: google-genai has no such param).
        """
        from ohm.core.provider import GeminiProvider
        prov = GeminiProvider(config_gemini)
        model = prov.create_model()
        from strands.models.gemini import GeminiModel
        assert isinstance(model, GeminiModel)
        assert model.client_args == {}

    def test_ollama_instantiation(self, config_ollama):
        from ohm.core.provider import OllamaProvider
        prov = OllamaProvider(config_ollama)
        assert prov.config.name == "ollama"

    @patch.dict("os.environ", {}, clear=True)
    def test_ollama_create_model(self, config_ollama):
        """Ollama requires no API key."""
        from ohm.core.provider import OllamaProvider
        prov = OllamaProvider(config_ollama)
        model = prov.create_model()
        from strands.models.ollama import OllamaModel
        assert isinstance(model, OllamaModel)

    def test_bedrock_instantiation(self, config_bedrock):
        from ohm.core.provider import BedrockProvider
        prov = BedrockProvider(config_bedrock)
        assert prov.config.name == "bedrock"

    @patch.dict("os.environ", _AWS_ENV, clear=False)
    def test_bedrock_create_model(self, config_bedrock):
        from ohm.core.provider import BedrockProvider
        prov = BedrockProvider(config_bedrock)
        model = prov.create_model()
        from strands.models.bedrock import BedrockModel
        assert isinstance(model, BedrockModel)

    def test_nvidia_nim_instantiation(self, config_nvidia):
        from ohm.core.provider import OpenAICompatibleProvider
        prov = OpenAICompatibleProvider(config_nvidia)
        assert prov.config.name == "nvidia-nim"
        assert prov.config.base_url == "https://nim.example.com"

    @patch.dict("os.environ", _N_ENV, clear=False)
    def test_nvidia_nim_create_model(self, config_nvidia):
        from ohm.core.provider import OpenAICompatibleProvider
        prov = OpenAICompatibleProvider(config_nvidia)
        model = prov.create_model()
        from strands.models.openai import OpenAIModel
        assert isinstance(model, OpenAIModel)

    def test_xiaomi_mimo_instantiation(self, config_mimo):
        from ohm.core.provider import OpenAICompatibleProvider
        prov = OpenAICompatibleProvider(config_mimo)
        assert prov.config.name == "xiaomi-mimo"
        assert prov.config.base_url == "https://mimo.example.com"

    @patch.dict("os.environ", _M_ENV, clear=False)
    def test_xiaomi_mimo_create_model(self, config_mimo):
        from ohm.core.provider import OpenAICompatibleProvider
        prov = OpenAICompatibleProvider(config_mimo)
        model = prov.create_model()
        from strands.models.openai import OpenAIModel
        assert isinstance(model, OpenAIModel)

    # ── check_health tests ─────────────────────────────────

    @patch.dict("os.environ", _A_ENV, clear=False)
    def test_anthropic_check_health_healthy(self, config_anthropic):
        from ohm.core.provider import AnthropicProvider
        prov = AnthropicProvider(config_anthropic)
        assert prov.check_health() == ProviderStatus.HEALTHY

    @patch.dict("os.environ", {}, clear=True)
    def test_anthropic_check_health_unhealthy(self, config_anthropic):
        from ohm.core.provider import AnthropicProvider
        prov = AnthropicProvider(config_anthropic)
        assert prov.check_health() == ProviderStatus.UNHEALTHY

    @patch.dict("os.environ", _O_ENV, clear=False)
    def test_openai_check_health_healthy(self, config_openai):
        from ohm.core.provider import OpenAIClientProvider
        prov = OpenAIClientProvider(config_openai)
        assert prov.check_health() == ProviderStatus.HEALTHY

    @patch.dict("os.environ", {}, clear=True)
    def test_openai_check_health_unhealthy(self, config_openai):
        from ohm.core.provider import OpenAIClientProvider
        prov = OpenAIClientProvider(config_openai)
        assert prov.check_health() == ProviderStatus.UNHEALTHY

    @patch.dict("os.environ", _G_ENV, clear=False)
    def test_gemini_check_health_healthy(self, config_gemini):
        from ohm.core.provider import GeminiProvider
        prov = GeminiProvider(config_gemini)
        assert prov.check_health() == ProviderStatus.HEALTHY

    @patch.dict("os.environ", {}, clear=True)
    def test_gemini_check_health_unhealthy(self, config_gemini):
        from ohm.core.provider import GeminiProvider
        prov = GeminiProvider(config_gemini)
        assert prov.check_health() == ProviderStatus.UNHEALTHY

    def test_ollama_check_health_always_healthy(self, config_ollama):
        """Ollama doesn't require API keys, so it's always healthy."""
        from ohm.core.provider import OllamaProvider
        prov = OllamaProvider(config_ollama)
        assert prov.check_health() == ProviderStatus.HEALTHY

    @patch.dict("os.environ", _AWS_ENV, clear=False)
    def test_bedrock_check_health_healthy(self, config_bedrock):
        from ohm.core.provider import BedrockProvider
        prov = BedrockProvider(config_bedrock)
        assert prov.check_health() == ProviderStatus.HEALTHY

    @patch.dict("os.environ", {}, clear=True)
    def test_bedrock_check_health_unhealthy(self, config_bedrock):
        from ohm.core.provider import BedrockProvider
        prov = BedrockProvider(config_bedrock)
        assert prov.check_health() == ProviderStatus.UNHEALTHY

    @patch.dict("os.environ", _N_ENV, clear=False)
    def test_nvidia_check_health_healthy(self, config_nvidia):
        from ohm.core.provider import OpenAICompatibleProvider
        prov = OpenAICompatibleProvider(config_nvidia)
        assert prov.check_health() == ProviderStatus.HEALTHY

    @patch.dict("os.environ", _M_ENV, clear=False)
    def test_mimo_check_health_healthy(self, config_mimo):
        from ohm.core.provider import OpenAICompatibleProvider
        prov = OpenAICompatibleProvider(config_mimo)
        assert prov.check_health() == ProviderStatus.HEALTHY

    @patch.dict("os.environ", {}, clear=True)
    def test_nvidia_check_health_unhealthy(self, config_nvidia):
        from ohm.core.provider import OpenAICompatibleProvider
        prov = OpenAICompatibleProvider(config_nvidia)
        assert prov.check_health() == ProviderStatus.UNHEALTHY

    # ── get_models tests ───────────────────────────────────

    def test_all_providers_return_models_list(self, config_anthropic, config_openai, config_gemini, config_ollama, config_bedrock, config_nvidia, config_mimo):
        from ohm.core.provider import (
            AnthropicProvider,
            BedrockProvider,
            GeminiProvider,
            OllamaProvider,
            OpenAIClientProvider,
            OpenAICompatibleProvider,
        )
        providers = [
            AnthropicProvider(config_anthropic),
            OpenAIClientProvider(config_openai),
            GeminiProvider(config_gemini),
            OllamaProvider(config_ollama),
            BedrockProvider(config_bedrock),
            OpenAICompatibleProvider(config_nvidia),
            OpenAICompatibleProvider(config_mimo),
        ]
        for prov in providers:
            models = prov.get_models()
            assert isinstance(models, list), f"{prov.config.name}.get_models() should return list"
            # Unconditional: fixtures MUST carry models so these assertions always execute.
            assert len(models) >= 1, (
                f"{prov.config.name}.get_models() returned an empty list — "
                "test fixture must carry at least one model"
            )
            assert all(isinstance(pm, ProviderModel) for pm in models), (
                f"{prov.config.name}.get_models() must return ProviderModel instances"
            )
            assert all(pm.id for pm in models), (
                f"{prov.config.name}.get_models() must return models with non-empty ids"
            )

    # ── get_status tests ───────────────────────────────────

    def test_get_status_returns_dict(self, config_anthropic):
        from ohm.core.provider import AnthropicProvider
        prov = AnthropicProvider(config_anthropic)
        status = prov.get_status()
        assert isinstance(status, dict)
        assert "name" in status
        assert "status" in status
