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
        assert cfg.base_url is None
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

    def test_custom_base_url(self):
        """R3-001: AgentConfig must carry a custom base_url for gateway/proxy providers."""
        cfg = AgentConfig(
            provider="nvidia-nim",
            model="nemotron-70b",
            base_url="https://nim.custom.example.com",
        )
        assert cfg.base_url == "https://nim.custom.example.com"


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


class TestAgentLastMetrics:
    """Tests for Agent.last_metrics property."""

    def test_last_metrics_default_empty(self):
        """Before any execution, last_metrics should be empty dict."""
        agent = Agent(AgentConfig())
        assert agent.last_metrics == {}

    async def test_last_metrics_after_run(self):
        """After run() completes, last_metrics should contain usage data."""
        agent = Agent(AgentConfig())

        class FakeMetrics:
            def get_summary(self):
                return {
                    "accumulated_usage": {
                        "totalTokens": 150,
                        "inputTokens": 100,
                        "outputTokens": 50,
                    },
                    "total_cycles": 1,
                    "total_duration": 1.5,
                    "tool_usage": {},
                }

        class FakeMsg:
            content = [{"text": "Hello world"}]

        class FakeResult:
            message = FakeMsg()
            metrics = FakeMetrics()

        agent._ensure_agent = lambda: (lambda prompt: FakeResult())

        resp = await agent.run("test prompt")
        assert agent.last_metrics["total_tokens"] == 150
        assert agent.last_metrics["input_tokens"] == 100
        assert agent.last_metrics["output_tokens"] == 50

    async def test_last_metrics_after_stream(self):
        """After stream() iteration completes, last_metrics should contain usage data."""
        agent = Agent(AgentConfig())

        class FakeMetrics:
            def get_summary(self):
                return {
                    "accumulated_usage": {
                        "totalTokens": 200,
                        "inputTokens": 120,
                        "outputTokens": 80,
                    },
                    "total_cycles": 1,
                    "total_duration": 2.0,
                    "tool_usage": {},
                }

        class FakeMsg:
            content = [{"text": "Hello"}]

        class FakeResult:
            message = FakeMsg()
            metrics = FakeMetrics()

        class FakeStrandsAgent:
            async def stream_async(self, prompt):
                yield {"type": "text", "data": "Hello"}

            _last_result = FakeResult()

        agent._ensure_agent = lambda: FakeStrandsAgent()

        events = []
        async for event in agent.stream("test prompt"):
            events.append(event)

        assert agent.last_metrics["total_tokens"] == 200
        assert agent.last_metrics["input_tokens"] == 120

    async def test_last_metrics_after_run_with_different_data(self):
        """Test triangulation: different metrics shape after run()."""
        agent = Agent(AgentConfig())

        class FakeMetrics:
            def get_summary(self):
                return {
                    "accumulated_usage": {
                        "totalTokens": 9999,
                        "inputTokens": 5000,
                        "outputTokens": 4999,
                    },
                    "total_cycles": 3,
                    "total_duration": 5.0,
                    "tool_usage": {"file_read": 2},
                }

        class FakeMsg:
            content = [{"text": "Different result"}]

        class FakeResult:
            message = FakeMsg()
            metrics = FakeMetrics()

        agent._ensure_agent = lambda: (lambda prompt: FakeResult())

        resp = await agent.run("another prompt")
        assert agent.last_metrics["total_tokens"] == 9999
        assert agent.last_metrics["input_tokens"] == 5000
        assert agent.last_metrics["output_tokens"] == 4999
        assert agent.last_metrics["total_cycles"] == 3

    async def test_last_metrics_empty_when_no_result(self):
        """When strands agent has no _last_result, last_metrics should be empty."""
        agent = Agent(AgentConfig())

        class FakeStrandsAgent:
            async def stream_async(self, prompt):
                yield {"type": "text", "data": "Hello"}

        agent._ensure_agent = lambda: FakeStrandsAgent()

        events = []
        async for event in agent.stream("test"):
            events.append(event)

        assert agent.last_metrics == {}


class TestAgentProviderIntegration:
    def test_ensure_agent_uses_provider_create_model(self, monkeypatch):
        """Agent._ensure_agent() MUST use Provider.create_model(), not _resolve_model."""
        create_calls: list[str] = []

        class FakeModel:
            pass

        class FakeProvider:
            def create_model(self, model_id=None):
                create_calls.append(model_id or "")
                return FakeModel()

        cfg = AgentConfig(provider="anthropic", model="claude-sonnet-4-6")
        agent = Agent(cfg)

        monkeypatch.setattr(
            "ohm.core.config.OHMConfig.resolve_provider",
            lambda self, name=None: FakeProvider(),
        )
        monkeypatch.setattr(
            "ohm.core.agent._load_tools",
            lambda names: [],
        )

        class FakeStrandsAgent:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        monkeypatch.setattr("strands.Agent", FakeStrandsAgent)

        agent._ensure_agent()
        assert create_calls == ["claude-sonnet-4-6"]
        assert agent._strands_agent is not None

    @pytest.mark.parametrize(
        "provider, model_id, base_url",
        [
            ("nvidia-nim", "nemotron-70b", "https://nim.custom.example.com"),
            ("xiaomi-mimo", "mimo-v2", "https://mimo.custom.example.com"),
            ("anthropic", "claude-sonnet-4-6", "https://anthropic.custom.example.com"),
        ],
    )
    def test_ensure_agent_propagates_base_url_to_provider(self, monkeypatch, provider, model_id, base_url):
        """R3-001: AgentConfig.base_url must reach the OHMConfig used to build the provider.

        The OHMConfig rebuilt inside _ensure_agent() MUST carry base_url; otherwise
        resolve_provider() falls back to catalog defaults and gateway traffic
        silently goes to the public host.
        """
        captured: list[str | None] = []

        class FakeModel:
            pass

        class FakeProvider:
            def create_model(self, model_id=None):
                return FakeModel()

        def fake_resolve(self, name=None):
            captured.append(self.base_url)
            return FakeProvider()

        monkeypatch.setattr(
            "ohm.core.config.OHMConfig.resolve_provider",
            fake_resolve,
        )
        monkeypatch.setattr(
            "ohm.core.agent._load_tools",
            lambda names: [],
        )

        class FakeStrandsAgent:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        monkeypatch.setattr("strands.Agent", FakeStrandsAgent)

        cfg = AgentConfig(provider=provider, model=model_id, base_url=base_url)
        agent = Agent(cfg)
        agent._ensure_agent()
        assert captured == [base_url]

    def test_default_config_path_carries_base_url(self, monkeypatch):
        """R3-001: Agent() without config must copy ohm_cfg.base_url into AgentConfig."""
        from ohm.core.config import OHMConfig

        fake_cfg = OHMConfig(
            provider="nvidia-nim",
            model="nemotron-70b",
            base_url="https://nim.custom.example.com",
        )
        monkeypatch.setattr("ohm.core.config.get_config", lambda: fake_cfg)

        agent = Agent()
        assert agent.config.base_url == "https://nim.custom.example.com"


class TestProviderMap:
    def test_all_providers_have_defaults(self):
        for provider in _PROVIDER_MODEL_MAP:
            assert provider in _DEFAULT_MODELS

    def test_default_tools_nonempty(self):
        assert len(_DEFAULT_TOOL_NAMES) > 0
        assert "file_read" in _DEFAULT_TOOL_NAMES
        assert "file_write" in _DEFAULT_TOOL_NAMES
