"""OHM Provider — Provider abstraction layer.

Defines the Provider ABC, retry decorator, FallbackProvider,
and per-provider subclasses backed by strands-agents model classes.
"""

from __future__ import annotations

import functools
import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# ── Retry constants ────────────────────────────────────────────

_RETRY_MAX_BACKOFF: float = 30.0


# ── Data types ─────────────────────────────────────────────────


class ProviderStatus(Enum):
    """Provider health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ProviderModel:
    """Model information for a provider."""
    id: str
    name: str
    context_window: int
    cost_input: float  # per 1M tokens
    cost_output: float  # per 1M tokens
    max_output: int | None = None
    supports_tools: bool = True
    supports_vision: bool = False


@dataclass
class ProviderConfig:
    """Provider configuration."""
    name: str
    display_name: str
    api_key: str | None = None
    base_url: str | None = None
    models: list[ProviderModel] = field(default_factory=list)
    timeout: float = 30.0
    max_retries: int = 3


# ── Static provider catalog ────────────────────────────────────

KNOWN_PROVIDERS: list[str] = [
    "anthropic",
    "openai",
    "gemini",
    "ollama",
    "bedrock",
    "nvidia-nim",
    "xiaomi-mimo",
]

DEFAULT_BASE_URLS: dict[str, str] = {
    "nvidia-nim": "https://integrate.api.nvidia.com/v1",
    "xiaomi-mimo": "https://api.xiaomimimo.com/v1",
}

PROVIDER_CATALOG: dict[str, ProviderConfig] = {
    "anthropic": ProviderConfig(
        name="anthropic",
        display_name="Anthropic",
        models=[
            ProviderModel("claude-sonnet-4-6", "Claude Sonnet 4.6", 200_000, 3.0, 15.0),
            ProviderModel("claude-3-opus-20240229", "Claude 3 Opus", 200_000, 15.0, 75.0),
            ProviderModel("claude-3-haiku-20240307", "Claude 3 Haiku", 200_000, 0.25, 1.25),
        ],
    ),
    "openai": ProviderConfig(
        name="openai",
        display_name="OpenAI",
        models=[
            ProviderModel("gpt-4o", "GPT-4o", 128_000, 2.5, 10.0),
            ProviderModel("gpt-4-turbo", "GPT-4 Turbo", 128_000, 10.0, 30.0),
            ProviderModel("gpt-3.5-turbo", "GPT-3.5 Turbo", 16_385, 0.5, 1.5),
        ],
    ),
    "gemini": ProviderConfig(
        name="gemini",
        display_name="Google Gemini",
        models=[
            ProviderModel("gemini-3.5-flash", "Gemini 3.5 Flash", 1_000_000, 0.15, 0.60),
            ProviderModel("gemini-2.5-pro", "Gemini 2.5 Pro", 1_000_000, 1.25, 5.0),
            ProviderModel("gemini-2.0-flash", "Gemini 2.0 Flash", 1_000_000, 0.10, 0.40),
        ],
    ),
    "ollama": ProviderConfig(
        name="ollama",
        display_name="Ollama (Local)",
        models=[
            ProviderModel("llama3.2", "Llama 3.2", 128_000, 0.0, 0.0),
            ProviderModel("llama-3-8b", "Llama 3 8B", 8_192, 0.0, 0.0),
            ProviderModel("mistral-7b", "Mistral 7B", 8_192, 0.0, 0.0),
        ],
    ),
    "bedrock": ProviderConfig(
        name="bedrock",
        display_name="AWS Bedrock",
        models=[
            ProviderModel(
                "global.anthropic.claude-sonnet-4-6",
                "Claude Sonnet 4.6 (Bedrock)",
                200_000,
                3.0,
                15.0,
            ),
        ],
    ),
    "nvidia-nim": ProviderConfig(
        name="nvidia-nim",
        display_name="NVIDIA NIM",
        base_url=DEFAULT_BASE_URLS["nvidia-nim"],
        models=[
            ProviderModel("nemotron-70b", "Nemotron 70B", 128_000, 0.80, 3.20),
            ProviderModel("mistral-large", "Mistral Large", 128_000, 1.00, 3.00),
            ProviderModel("deepseek-r1", "DeepSeek R1", 128_000, 0.55, 2.19),
        ],
    ),
    "xiaomi-mimo": ProviderConfig(
        name="xiaomi-mimo",
        display_name="Xiaomi MiMo",
        base_url=DEFAULT_BASE_URLS["xiaomi-mimo"],
        models=[
            ProviderModel("mimo-v2", "MiMo V2", 128_000, 0.50, 2.00),
        ],
    ),
}


# ── Retry decorator ────────────────────────────────────────────


def retry(
    max_retries: int = 3,
    base: float = 2.0,
    max_backoff: float = _RETRY_MAX_BACKOFF,
) -> Any:
    """Decorator: retry on 429 / 503 / 5xx with exponential backoff.

    Args:
        max_retries: Maximum number of attempts (including the first).
        base: Base delay in seconds (doubles each retry).
        max_backoff: Maximum delay cap in seconds.

    Returns:
        Decorated function that retries on transient failures.

    Raises:
        The last exception if all retries are exhausted.
    """
    def decorator(func: Any) -> Any:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    status = _extract_status(exc)
                    if status is not None and _is_transient(status):
                        if attempt < max_retries - 1:
                            delay = min(base * (2 ** attempt), max_backoff)
                            # Add jitter: ±25%
                            jitter = random.uniform(0.75, 1.25)
                            time.sleep(delay * jitter)
                            continue
                    # Non-transient or last retry — propagate immediately
                    raise
            # Should not reach here, but defensive
            if last_exc is not None:
                raise last_exc
            return None  # pragma: no cover
        return wrapper
    return decorator


def _extract_status(exc: Exception) -> int | None:
    """Extract HTTP status code from an exception, if present."""
    return getattr(exc, "status_code", None)


def _is_transient(status: int) -> bool:
    """Return True if the status code is transient (retriable)."""
    return status == 429 or status == 503 or (500 <= status < 600)


# ── Base Provider ABC ──────────────────────────────────────────


class Provider(ABC):
    """Abstract base for all LLM providers.

    Subclasses MUST implement:
        - create_model()
        - get_models()
        - check_health()
        - get_status()
    """

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self.status = ProviderStatus.HEALTHY
        self._latency_ms: float = 0.0

    @abstractmethod
    def create_model(self) -> Any:
        """Return a strands model instance for this provider."""
        ...

    @abstractmethod
    def check_health(self) -> ProviderStatus:
        """Check provider health by verifying required configuration.

        Returns HEALTHY when required env vars are present, UNHEALTHY otherwise.
        """
        ...

    def get_models(self) -> list[ProviderModel]:
        """Return the list of available model definitions."""
        return self.config.models

    def get_status(self) -> dict[str, Any]:
        """Return a dict with provider status information."""
        info: dict[str, Any] = {
            "name": self.config.name,
            "display_name": self.config.display_name,
            "status": self.check_health().value,
            "models_count": len(self.config.models),
        }
        info.update(self._extra_status())
        return info

    def _extra_status(self) -> dict[str, Any]:
        """Override in subclasses to add extra fields to get_status()."""
        return {}

    def complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send a completion request (overridable, delegates to create_model).

        Subclasses MAY override this to provide custom completion logic.
        The default implementation creates a model and calls it.
        """
        raise NotImplementedError

    # ── Helper methods for subclasses ────────────────────────────

    @staticmethod
    def _get_env(name: str) -> str | None:
        """Read an environment variable, returning None if not set."""
        import os
        return os.environ.get(name)

    def _require_env_vars(self, *names: str) -> bool:
        """Return True if ALL named environment variables are present."""
        return all(self._get_env(n) is not None for n in names)

    def _build_client_args(self, *api_key_names: str) -> dict[str, str] | None:
        """Build client_args dict from env var names.

        Uses the first non-None API key found. Includes base_url from config
        if set.
        """
        args: dict[str, str] = {}
        for name in api_key_names:
            value = self._get_env(name)
            if value is not None:
                args["api_key"] = value
                break
        if self.config.base_url:
            args["base_url"] = self.config.base_url
        return args if args else None

    @staticmethod
    def _build_model_params(**overrides: Any) -> dict[str, Any] | None:
        """Build a params dict from keyword overrides.

        Returns None if no overrides are provided.
        """
        return dict(overrides) if overrides else None

    def _default_model_id(self) -> str:
        """Return the first model id from config, or empty string."""
        if self.config.models:
            return self.config.models[0].id
        return ""


# ── Per-provider subclasses ────────────────────────────────────


class AnthropicProvider(Provider):
    """Provider for Anthropic (Claude) models.

    Requires ANTHROPIC_API_KEY environment variable.
    """

    def create_model(
        self,
        model_id: str | None = None,
    ) -> Any:
        import os

        from strands.models.anthropic import AnthropicModel

        kwargs: dict[str, Any] = {}
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            kwargs["client_args"] = {"api_key": api_key}
        kwargs["max_tokens"] = 4096
        kwargs["model_id"] = model_id or self._default_model_id()
        kwargs["params"] = {"temperature": 0.7}
        return AnthropicModel(**kwargs)

    def get_models(self) -> list[ProviderModel]:
        return self.config.models

    def check_health(self) -> ProviderStatus:
        return ProviderStatus.HEALTHY if self._get_env("ANTHROPIC_API_KEY") else ProviderStatus.UNHEALTHY


class OpenAIClientProvider(Provider):
    """Provider for OpenAI models.

    Requires OPENAI_API_KEY environment variable.
    """

    def create_model(
        self,
        model_id: str | None = None,
    ) -> Any:
        import os

        from strands.models.openai import OpenAIModel

        kwargs: dict[str, Any] = {}
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            kwargs["client_args"] = {"api_key": api_key}
        kwargs["model_id"] = model_id or self._default_model_id()
        return OpenAIModel(**kwargs)

    def get_models(self) -> list[ProviderModel]:
        return self.config.models

    def check_health(self) -> ProviderStatus:
        return ProviderStatus.HEALTHY if self._get_env("OPENAI_API_KEY") else ProviderStatus.UNHEALTHY


class GeminiProvider(Provider):
    """Provider for Google Gemini models.

    Requires GEMINI_API_KEY environment variable.
    """

    def create_model(
        self,
        model_id: str | None = None,
    ) -> Any:
        import os

        from strands.models.gemini import GeminiModel

        kwargs: dict[str, Any] = {}
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            kwargs["client_args"] = {"api_key": api_key}
        kwargs["model_id"] = model_id or self._default_model_id()
        kwargs["params"] = {"temperature": 0.7, "max_output_tokens": 4096}
        return GeminiModel(**kwargs)

    def get_models(self) -> list[ProviderModel]:
        return self.config.models

    def check_health(self) -> ProviderStatus:
        return ProviderStatus.HEALTHY if self._get_env("GEMINI_API_KEY") else ProviderStatus.UNHEALTHY


class OllamaProvider(Provider):
    """Provider for locally-run Ollama models.

    No API key required.
    """

    def create_model(
        self,
        model_id: str | None = None,
    ) -> Any:
        from strands.models.ollama import OllamaModel

        kwargs: dict[str, Any] = {}
        resolved = model_id or self._default_model_id()
        if resolved:
            kwargs["model_id"] = resolved
        return OllamaModel(host=None, **kwargs)

    def get_models(self) -> list[ProviderModel]:
        return self.config.models

    def check_health(self) -> ProviderStatus:
        """Ollama is always considered healthy (no credentials needed)."""
        return ProviderStatus.HEALTHY


class BedrockProvider(Provider):
    """Provider for AWS Bedrock models.

    Requires AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.
    """

    def create_model(
        self,
        model_id: str | None = None,
    ) -> Any:
        from strands.models.bedrock import BedrockModel

        kwargs: dict[str, Any] = {}
        resolved = model_id or self._default_model_id()
        if resolved:
            kwargs["model_id"] = resolved
        return BedrockModel(**kwargs)

    def get_models(self) -> list[ProviderModel]:
        return self.config.models

    def check_health(self) -> ProviderStatus:
        return (
            ProviderStatus.HEALTHY
            if self._require_env_vars("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY")
            else ProviderStatus.UNHEALTHY
        )


class OpenAICompatibleProvider(Provider):
    """Provider for OpenAI-compatible backends (NVIDIA NIM, Xiaomi MiMo, etc.).

    Uses OpenAIModel with a custom base_url.
    Requires NVAPI_KEY (nvidia-nim) or MIMO_API_KEY (xiaomi-mimo) depending on config.
    """

    def create_model(
        self,
        model_id: str | None = None,
    ) -> Any:
        from strands.models.openai import OpenAIModel

        kwargs: dict[str, Any] = {}
        client_args: dict[str, str] = {}

        api_key = self._get_env("NVAPI_KEY") or self._get_env("MIMO_API_KEY")
        if api_key:
            client_args["api_key"] = api_key
        if self.config.base_url:
            client_args["base_url"] = self.config.base_url
        if client_args:
            kwargs["client_args"] = client_args
        kwargs["model_id"] = model_id or self._default_model_id()
        return OpenAIModel(**kwargs)

    def get_models(self) -> list[ProviderModel]:
        return self.config.models

    def check_health(self) -> ProviderStatus:
        """Check for NVAPI_KEY or MIMO_API_KEY depending on provider name."""
        if self.config.name == "nvidia-nim":
            return ProviderStatus.HEALTHY if self._get_env("NVAPI_KEY") else ProviderStatus.UNHEALTHY
        if self.config.name == "xiaomi-mimo":
            return ProviderStatus.HEALTHY if self._get_env("MIMO_API_KEY") else ProviderStatus.UNHEALTHY
        # Fallback: check either
        return ProviderStatus.HEALTHY if (self._get_env("NVAPI_KEY") or self._get_env("MIMO_API_KEY")) else ProviderStatus.UNHEALTHY

    def _extra_status(self) -> dict[str, Any]:
        if self.config.base_url:
            return {"base_url": self.config.base_url}
        return {}


# ── Fallback provider ──────────────────────────────────────────


class FallbackProvider(Provider):
    """A Provider that delegates to a primary, failing over to a secondary.

    When the primary's ``complete()`` exhausts all retries, the
    secondary provider is invoked.  All other methods (get_models,
    check_health, get_status) delegate to the primary.
    """

    def __init__(
        self,
        primary: Provider,
        secondary: Provider,
        config: ProviderConfig | None = None,
    ) -> None:
        if config is None:
            config = ProviderConfig(
                name=f"{primary.config.name}+{secondary.config.name}",
                display_name=f"{primary.config.display_name} + {secondary.config.display_name}",
            )
        super().__init__(config)
        self._primary = primary
        self._secondary = secondary

    def create_model(self) -> Any:
        return self._primary.create_model()

    def get_models(self) -> list[ProviderModel]:
        return self._primary.get_models()

    def check_health(self) -> ProviderStatus:
        return self._primary.check_health()

    def get_status(self) -> dict[str, Any]:
        return self._primary.get_status()

    @retry(max_retries=3)
    def complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        try:
            return self._primary.complete(model, messages, **kwargs)
        except Exception:
            logger.warning(
                "Primary provider '%s' failed all retries; failing over to '%s'",
                self._primary.config.name,
                self._secondary.config.name,
            )
            return self._secondary.complete(model, messages, **kwargs)


# ── Provider factory ───────────────────────────────────────────

_PROVIDER_CLASSES: dict[str, type[Provider]] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIClientProvider,
    "gemini": GeminiProvider,
    "ollama": OllamaProvider,
    "bedrock": BedrockProvider,
    "nvidia-nim": OpenAICompatibleProvider,
    "xiaomi-mimo": OpenAICompatibleProvider,
}


def create_provider(
    name: str,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
) -> Provider:
    """Instantiate a configured Provider by name."""
    key = name.lower()
    if key not in PROVIDER_CATALOG:
        supported = ", ".join(KNOWN_PROVIDERS)
        raise ValueError(f"Unknown provider '{name}'. Supported: {supported}")

    catalog = PROVIDER_CATALOG[key]
    resolved_base = base_url or catalog.base_url
    config = ProviderConfig(
        name=catalog.name,
        display_name=catalog.display_name,
        api_key=api_key,
        base_url=resolved_base,
        models=list(catalog.models),
        timeout=catalog.timeout,
        max_retries=catalog.max_retries,
    )
    return _PROVIDER_CLASSES[key](config)


def provider_to_ui_dict(provider: Provider) -> dict[str, Any]:
    """Serialize a Provider for TUI widgets (model selector, sidebar)."""
    return {
        "name": provider.config.name,
        "display_name": provider.config.display_name,
        "models": [
            {
                "id": m.id,
                "name": m.name,
                "context_window": m.context_window,
                "cost_input": m.cost_input,
                "cost_output": m.cost_output,
            }
            for m in provider.get_models()
        ],
        "status": provider.check_health().value,
    }


def get_providers_ui_data(
    *,
    api_key_for: Any | None = None,
    base_url: str | None = None,
) -> list[dict[str, Any]]:
    """Return all known providers as UI-ready dicts."""
    result: list[dict[str, Any]] = []
    for name in KNOWN_PROVIDERS:
        key = api_key_for(name) if api_key_for else None
        prov = create_provider(name, api_key=key, base_url=base_url)
        result.append(provider_to_ui_dict(prov))
    return result


def resolve_context_window(provider_name: str, model_id: str) -> int:
    """Look up context_window for a provider/model from the catalog."""
    key = provider_name.lower()
    catalog = PROVIDER_CATALOG.get(key)
    if catalog is None:
        return 200_000
    for model in catalog.models:
        if model.id == model_id:
            return model.context_window
    if catalog.models:
        return catalog.models[0].context_window
    return 200_000
