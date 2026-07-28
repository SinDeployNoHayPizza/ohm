"""OHM Provider - Provider abstraction layer."""

from dataclasses import dataclass, field
from typing import Any
from enum import Enum


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


class Provider:
    """Provider abstraction for OHM.

    This is a placeholder that returns fake data for demo purposes.
    The real implementation will handle actual API calls to providers.
    """

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self.status = ProviderStatus.HEALTHY
        self._latency_ms: float = 0.0

    async def complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send a completion request (placeholder).

        In the real implementation, this will:
        1. Validate the request
        2. Handle authentication
        3. Make the API call
        4. Handle retries and errors
        5. Return structured response
        """
        import asyncio
        import random

        # Simulate API call
        await asyncio.sleep(random.uniform(0.5, 2.0))

        tokens_input = random.randint(100, 500)
        tokens_output = random.randint(50, 200)

        return {
            "content": f"[DEMO] Response from {self.config.display_name}/{model}",
            "tokens": {
                "input": tokens_input,
                "output": tokens_output,
                "total": tokens_input + tokens_output,
            },
            "latency_ms": self._latency_ms,
            "model": model,
            "provider": self.config.name,
        }

    def get_models(self) -> list[ProviderModel]:
        """Get available models."""
        return self.config.models

    def get_status(self) -> dict[str, Any]:
        """Get provider status."""
        return {
            "name": self.config.name,
            "display_name": self.config.display_name,
            "status": self.status.value,
            "models_count": len(self.config.models),
            "latency_ms": self._latency_ms,
        }


# ──────────────────────────────────────────────────────────────
# Pre-configured providers (for demo)
# ──────────────────────────────────────────────────────────────

ANTHROPIC_PROVIDER = ProviderConfig(
    name="anthropic",
    display_name="Anthropic",
    models=[
        ProviderModel(
            id="claude-sonnet-4-20250514",
            name="Claude Sonnet 4",
            context_window=200000,
            cost_input=3.0,
            cost_output=15.0,
            supports_vision=True,
        ),
        ProviderModel(
            id="claude-3-opus-20240229",
            name="Claude 3 Opus",
            context_window=200000,
            cost_input=15.0,
            cost_output=75.0,
            supports_vision=True,
        ),
    ],
)

OPENAI_PROVIDER = ProviderConfig(
    name="openai",
    display_name="OpenAI",
    models=[
        ProviderModel(
            id="gpt-4-turbo",
            name="GPT-4 Turbo",
            context_window=128000,
            cost_input=10.0,
            cost_output=30.0,
            supports_vision=True,
        ),
        ProviderModel(
            id="gpt-4",
            name="GPT-4",
            context_window=8192,
            cost_input=30.0,
            cost_output=60.0,
        ),
    ],
)

LOCAL_PROVIDER = ProviderConfig(
    name="local",
    display_name="Local (Ollama)",
    models=[
        ProviderModel(
            id="llama-3-8b",
            name="Llama 3 8B",
            context_window=8192,
            cost_input=0.0,
            cost_output=0.0,
        ),
        ProviderModel(
            id="mistral-7b",
            name="Mistral 7B",
            context_window=8192,
            cost_input=0.0,
            cost_output=0.0,
        ),
    ],
)
