"""Tests for OHM agent core."""

import pytest
import asyncio

from ohm.core.agent import (
    Agent,
    AgentConfig,
    AgentResponse,
    AgentState,
    _DEFAULT_MODELS,
    _PROVIDER_MODEL_MAP,
    _DEFAULT_TOOL_NAMES,
)


class TestAgentConfig:
    def test_default_values(self):
        cfg = AgentConfig()
        assert cfg.name == "ohm-agent"
        assert cfg.provider == "anthropic"
        assert cfg.model == "claude-sonnet-4-6"
        assert cfg.sandbox is True
        assert cfg.max_tokens == 4096
        assert cfg.temperature == 0.7
        assert "file_read" in cfg.tools

    def test_custom_values(self):
        cfg = AgentConfig(
            provider="openai",
            model="gpt-4o",
            max_tokens=8192,
            temperature=0.3,
            sandbox=False,
        )
        assert cfg.provider == "openai"
        assert cfg.model == "gpt-4o"
        assert cfg.max_tokens == 8192
        assert cfg.temperature == 0.3
        assert cfg.sandbox is False


class TestAgentResponse:
    def test_default_values(self):
        resp = AgentResponse(content="Hello")
        assert resp.content == "Hello"
        assert resp.tokens_used == 0
        assert resp.latency_ms == 0.0
        assert resp.cost_usd == 0.0
        assert resp.success is True
        assert resp.error is None
        assert resp.tool_calls == []

    def test_error_response(self):
        resp = AgentResponse(
            content="",
            success=False,
            error="API key missing",
        )
        assert resp.success is False
        assert resp.error == "API key missing"


class TestAgentState:
    def test_default_values(self):
        state = AgentState()
        assert state.is_running is False
        assert state.current_task is None
        assert state.progress == 0.0
        assert state.total_tokens_used == 0
        assert state.tasks_completed == 0
        assert state.tasks_failed == 0


class TestAgent:
    def test_create_with_default_config(self):
        agent = Agent(AgentConfig())
        assert agent.config.provider == "anthropic"
        assert agent.state.is_running is False

    def test_create_with_custom_config(self):
        cfg = AgentConfig(provider="openai", model="gpt-4o")
        agent = Agent(cfg)
        assert agent.config.provider == "openai"
        assert agent.config.model == "gpt-4o"

    def test_get_status(self):
        agent = Agent(AgentConfig())
        status = agent.get_status()
        assert "name" in status
        assert "provider" in status
        assert "model" in status
        assert "is_running" in status
        assert "tools" in status

    def test_extract_text_from_string(self):
        result = Agent._extract_text("Hello world")
        assert result == "Hello world"

    def test_extract_text_from_dict_blocks(self):
        class FakeResult:
            message = type("M", (), {
                "content": [
                    {"text": "Hello "},
                    {"text": "world"},
                ]
            })()
        result = Agent._extract_text(FakeResult())
        assert result == "Hello \nworld"  # _extract_text joins with \n

    def test_extract_text_from_string_blocks(self):
        class FakeResult:
            message = type("M", (), {
                "content": ["Hello", " ", "world"]
            })()
        result = Agent._extract_text(FakeResult())
        assert result == "Hello\n \nworld"  # _extract_text joins with \n

    def test_extract_metrics_exception_returns_empty(self):
        result = Agent._extract_metrics(None)
        assert result == {}


class TestProviderMap:
    def test_all_providers_have_defaults(self):
        for provider in _PROVIDER_MODEL_MAP:
            assert provider in _DEFAULT_MODELS

    def test_default_tools_nonempty(self):
        assert len(_DEFAULT_TOOL_NAMES) > 0
        assert "file_read" in _DEFAULT_TOOL_NAMES
        assert "file_write" in _DEFAULT_TOOL_NAMES
