"""Tests for OHM CLI command handlers (run, goal).

Covers R4-001: the run/goal handlers must only forward the config
``base_url`` to ``AgentConfig`` when the CLI-selected provider matches the
provider the ``base_url`` was configured for.  Otherwise the CLI provider's
API key would be shipped to a foreign gateway host.
"""

from __future__ import annotations

import argparse
import pytest

from ohm.core.agent import AgentConfig
from ohm.core.config import OHMConfig
from ohm.commands.goal import handler as goal_handler
from ohm.commands.run import handler as run_handler


class _FakeResponse:
    """Minimal successful agent response."""

    def __init__(self, content: str = "ok") -> None:
        self.content = content
        self.success = True
        self.error = None


class _FakeAgent:
    """Replacement for ohm.core.agent.Agent that records its AgentConfig."""

    def __init__(self, config: AgentConfig) -> None:
        self.config = config

    async def run(self, prompt: str) -> _FakeResponse:
        return _FakeResponse()


@pytest.fixture
def fake_agent(monkeypatch) -> dict[str, AgentConfig]:
    """Patch ohm.core.agent.Agent and return a dict capturing the AgentConfig."""
    captured: dict[str, AgentConfig] = {}

    def factory(config: AgentConfig) -> _FakeAgent:
        captured["config"] = config
        return _FakeAgent(config)

    monkeypatch.setattr("ohm.core.agent.Agent", factory)
    return captured


@pytest.fixture
def config_with_base_url(monkeypatch):
    """Patch get_config() to return a config with a custom base_url."""
    def _set(provider: str, base_url: str) -> None:
        fake_cfg = OHMConfig(provider=provider, base_url=base_url)
        monkeypatch.setattr("ohm.core.config.get_config", lambda: fake_cfg)
    return _set


class TestRunHandlerBaseUrlGating:
    """R4-001: run handler must gate base_url on provider match."""

    def test_run_provider_differs_does_not_propagate_base_url(
        self, fake_agent, config_with_base_url
    ):
        """CLI provider (anthropic) != config provider (gemini) → base_url must be None."""
        config_with_base_url(provider="gemini", base_url="https://gemini-proxy.corp")
        args = argparse.Namespace(
            provider="anthropic", model=None, prompt="hello", stream=False
        )

        code = run_handler(args)

        assert code == 0
        assert fake_agent["config"].provider == "anthropic"
        assert fake_agent["config"].base_url is None

    def test_run_provider_matches_propagates_base_url(
        self, fake_agent, config_with_base_url
    ):
        """CLI provider == config provider → base_url must reach AgentConfig."""
        config_with_base_url(provider="anthropic", base_url="https://claude-gateway.corp")
        args = argparse.Namespace(
            provider="anthropic", model=None, prompt="hello", stream=False
        )

        code = run_handler(args)

        assert code == 0
        assert fake_agent["config"].provider == "anthropic"
        assert fake_agent["config"].base_url == "https://claude-gateway.corp"

    def test_run_other_differs_does_not_propagate_base_url(
        self, fake_agent, config_with_base_url
    ):
        """CLI provider (nvidia-nim) != config provider (anthropic) → base_url must be None."""
        config_with_base_url(provider="anthropic", base_url="https://claude-gateway.corp")
        args = argparse.Namespace(
            provider="nvidia-nim", model=None, prompt="hello", stream=False
        )

        code = run_handler(args)

        assert code == 0
        assert fake_agent["config"].provider == "nvidia-nim"
        assert fake_agent["config"].base_url is None


class TestGoalHandlerBaseUrlGating:
    """R4-001: goal handler must gate base_url on provider match."""

    def test_goal_provider_differs_does_not_propagate_base_url(
        self, fake_agent, config_with_base_url
    ):
        """CLI provider (gemini) != config provider (anthropic) → base_url must be None."""
        config_with_base_url(provider="anthropic", base_url="https://claude-gateway.corp")
        args = argparse.Namespace(
            provider="gemini", model=None, description="fix the tests"
        )

        code = goal_handler(args)

        assert code == 0
        assert fake_agent["config"].provider == "gemini"
        assert fake_agent["config"].base_url is None

    def test_goal_provider_matches_propagates_base_url(
        self, fake_agent, config_with_base_url
    ):
        """CLI provider == config provider → base_url must reach AgentConfig."""
        config_with_base_url(provider="anthropic", base_url="https://claude-gateway.corp")
        args = argparse.Namespace(
            provider="anthropic", model=None, description="fix the tests"
        )

        code = goal_handler(args)

        assert code == 0
        assert fake_agent["config"].provider == "anthropic"
        assert fake_agent["config"].base_url == "https://claude-gateway.corp"
