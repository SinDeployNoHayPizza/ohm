"""Tests for the OHM MCP server core module (MCP-1..MCP-7, MCP-12).

Strict-TDD slice S1: in-process FastMCP ``call_tool()``/``list_tools()`` —
no transports are started and no API keys are required. The agent factory is
always injected (or monkeypatched) so tests never touch a real LLM.
"""

from __future__ import annotations

import json
from pathlib import Path

from ohm import __version__
from ohm.core.agent import AgentConfig, AgentResponse
from ohm.core.config import OHMConfig

EXPECTED_TOOLS = {
    "run_prompt",
    "run_goal",
    "get_status",
    "list_sessions",
    "get_session",
    "list_skills",
    "list_models",
}

# API-key env vars cleared in status tests for deterministic output.
_PROVIDER_KEY_ENVS = (
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "AWS_ACCESS_KEY_ID",
    "NVAPI_KEY",
    "MIMO_API_KEY",
)


class _FakeAgent:
    """Duck-typed agent used in place of ``ohm.core.agent.Agent``."""

    def __init__(self, config: AgentConfig, response: AgentResponse | None = None) -> None:
        self.config = config
        self.prompt: str | None = None
        self.response = response or AgentResponse(
            content="fake answer",
            tokens_used=42,
            latency_ms=10.0,
            success=True,
        )

    async def run(self, prompt: str) -> AgentResponse:
        self.prompt = prompt
        return self.response


def _ok_factory() -> callable:  # noqa: F821
    def factory(config: AgentConfig) -> _FakeAgent:
        return _FakeAgent(config)

    return factory


def _failing_factory() -> callable:  # noqa: F821
    """Factory whose agent reports an unconfigured provider (MCP-3/4)."""

    def factory(config: AgentConfig) -> _FakeAgent:
        return _FakeAgent(
            config,
            AgentResponse(
                content="",
                success=False,
                error="No API key configured for provider 'anthropic'",
            ),
        )

    return factory


def _raising_factory() -> callable:  # noqa: F821
    """Factory that raises at construction time (D3: unknown provider)."""

    def factory(config: AgentConfig) -> _FakeAgent:
        raise ValueError(f"unknown provider '{config.provider}'")

    return factory


def _make_server(factory=None, agents=None, config=None):
    """Build a server with an explicit config; agents list captures instances."""
    from ohm.core.mcp_server import build_mcp_server

    kwargs: dict = {}
    if factory is None and agents is not None:
        def factory(cfg: AgentConfig) -> _FakeAgent:
            agent = _FakeAgent(cfg)
            agents.append(agent)
            return agent

    if factory is not None:
        kwargs["agent_factory"] = factory
    if config is not None:
        kwargs["config"] = config
    return build_mcp_server(**kwargs)


def _unpack(result) -> dict:
    """Unpack a FastMCP ``call_tool`` result (JSON TextContent) into a dict."""
    return json.loads(result[0].text)


class TestToolRegistration:
    """MCP-2: exactly seven tools; no resources, prompts, or subscriptions."""

    async def test_lists_exactly_seven_tools(self):
        server = _make_server(_ok_factory())
        tools = await server.list_tools()
        assert {tool.name for tool in tools} == EXPECTED_TOOLS
        assert len(tools) == 7

    async def test_no_resources_or_prompts(self):
        # Spec scenario MCP-2: the server must NOT register resources/prompts
        # in Stage 1 — the empty lists come from real registration logic.
        server = _make_server(_ok_factory())
        assert await server.list_resources() == []
        assert await server.list_prompts() == []


class TestRunPrompt:
    """MCP-3: success envelope fields + unconfigured-provider clean error."""

    async def test_success_returns_envelope_fields(self):
        server = _make_server(_ok_factory())
        result = _unpack(await server.call_tool("run_prompt", {"prompt": "Explain SOLID"}))
        assert result["success"] is True
        assert result["content"] == "fake answer"
        assert result["tokens_used"] == 42
        assert isinstance(result["latency_ms"], float) and result["latency_ms"] >= 0
        assert result["error"] is None

    async def test_arguments_reach_agent_config_and_prompt(self):
        agents: list[_FakeAgent] = []
        server = _make_server(agents=agents)
        await server.call_tool(
            "run_prompt",
            {"prompt": "hello", "provider": "openai", "model": "gpt-4o", "system_prompt": "Be terse"},
        )
        assert agents[0].prompt == "hello"
        assert agents[0].config.provider == "openai"
        assert agents[0].config.model == "gpt-4o"
        assert agents[0].config.system_prompt == "Be terse"

    async def test_unconfigured_provider_clean_error(self):
        server = _make_server(_failing_factory())
        result = _unpack(await server.call_tool("run_prompt", {"prompt": "hi"}))
        assert result["success"] is False
        assert "API key" in result["error"]


class TestRunGoal:
    """MCP-4: goal loop success + unconfigured-provider clean error."""

    async def test_goal_success(self):
        server = _make_server(_ok_factory())
        result = _unpack(await server.call_tool("run_goal", {"goal": "Write a test"}))
        assert result["success"] is True
        assert result["content"] == "fake answer"

    async def test_goal_uses_goal_system_prompt_and_goal_text(self):
        from ohm.commands.goal import GOAL_SYSTEM_PROMPT

        agents: list[_FakeAgent] = []
        server = _make_server(agents=agents)
        await server.call_tool("run_goal", {"goal": "Refactor this module"})
        assert agents[0].prompt == "Refactor this module"
        assert agents[0].config.system_prompt == GOAL_SYSTEM_PROMPT

    async def test_goal_unconfigured_provider_clean_error(self):
        server = _make_server(_failing_factory())
        result = _unpack(await server.call_tool("run_goal", {"goal": "x"}))
        assert result["success"] is False
        assert "API key" in result["error"]


class TestGetStatus:
    """MCP-5: version/provider/model/api-key status/session count."""

    @staticmethod
    def _clear_keys(monkeypatch) -> None:
        for var in _PROVIDER_KEY_ENVS:
            monkeypatch.delenv(var, raising=False)

    async def test_status_fields_with_missing_keys_and_sessions(
        self, tmp_path, monkeypatch
    ):
        session_dir = tmp_path / ".ohm" / "sessions"
        session_dir.mkdir(parents=True)
        (session_dir / "ses_1.json").write_text("{}", encoding="utf-8")
        (session_dir / "ses_2.json").write_text("{}", encoding="utf-8")
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        self._clear_keys(monkeypatch)

        server = _make_server(config=OHMConfig(provider="anthropic", model="claude-sonnet-4-6"))
        result = _unpack(await server.call_tool("get_status", {}))

        assert result["version"] == __version__
        assert result["provider"] == "anthropic"
        assert result["model"] == "claude-sonnet-4-6"
        assert result["providers"]["anthropic"] == "missing"
        assert result["session_count"] == 2

    async def test_status_reports_configured_and_local_providers(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        self._clear_keys(monkeypatch)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

        server = _make_server(config=OHMConfig(provider="anthropic", model="claude-sonnet-4-6"))
        result = _unpack(await server.call_tool("get_status", {}))

        assert result["providers"]["anthropic"] == "configured"
        assert result["providers"]["ollama"] == "local"
        assert result["session_count"] == 0


class TestSessionsTools:
    """MCP-6: list persisted sessions; get one or a clean error."""

    @staticmethod
    def _seed(tmp_path: Path, names: list[str]) -> None:
        session_dir = tmp_path / ".ohm" / "sessions"
        session_dir.mkdir(parents=True)
        for name in names:
            (session_dir / f"{name}.json").write_text(
                json.dumps({"session_id": name, "messages": [{"role": "user", "content": "hi"}]}),
                encoding="utf-8",
            )

    async def test_list_sessions_returns_persisted_ids(self, tmp_path, monkeypatch):
        self._seed(tmp_path, ["ses_111", "ses_222"])
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

        server = _make_server()
        result = _unpack(await server.call_tool("list_sessions", {}))

        assert set(result["sessions"]) == {"ses_111", "ses_222"}
        assert result["count"] == 2

    async def test_list_sessions_excludes_last_session_pointer(
        self, tmp_path, monkeypatch
    ):
        self._seed(tmp_path, ["ses_111"])
        (tmp_path / ".ohm" / "sessions" / "last_session.json").write_text(
            "{}", encoding="utf-8"
        )
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

        server = _make_server()
        result = _unpack(await server.call_tool("list_sessions", {}))

        assert result["sessions"] == ["ses_111"]
        assert result["count"] == 1

    async def test_get_session_returns_saved_content(self, tmp_path, monkeypatch):
        self._seed(tmp_path, ["ses_111"])
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

        server = _make_server()
        result = _unpack(await server.call_tool("get_session", {"session_id": "ses_111"}))

        assert result["success"] is True
        assert result["session_id"] == "ses_111"
        assert result["session"]["messages"][0]["content"] == "hi"

    async def test_get_session_missing_is_clean_error(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

        server = _make_server()
        result = _unpack(await server.call_tool("get_session", {"session_id": "nope"}))

        assert result["success"] is False
        assert "nope" in result["error"]


class TestSkillsModelsTools:
    """MCP-7: skills from the registry; models filtered by provider."""

    async def test_list_skills_returns_discovered_names(self, tmp_path, monkeypatch):
        for name in ("skill-a", "skill-b"):
            skill_dir = tmp_path / ".agents" / "skills" / name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: {name} desc\n---\nBody",
                encoding="utf-8",
            )
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

        server = _make_server()
        result = _unpack(await server.call_tool("list_skills", {}))

        assert set(result["skills"]) == {"skill-a", "skill-b"}
        assert result["count"] == 2

    async def test_list_skills_empty_in_clean_workspace(self, tmp_path, monkeypatch):
        # Companion empty case: no skill dirs exist in the isolated workspace.
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

        server = _make_server()
        result = _unpack(await server.call_tool("list_skills", {}))

        assert result["skills"] == []
        assert result["count"] == 0

    async def test_list_models_filters_by_provider(self):
        server = _make_server()
        result = _unpack(await server.call_tool("list_models", {"provider": "openai"}))

        assert result["provider"] == "openai"
        assert {m["id"] for m in result["models"]} == {"gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"}
        assert result["count"] == 3

    async def test_list_models_without_filter_covers_catalog(self):
        from ohm.core.provider import PROVIDER_CATALOG

        server = _make_server()
        result = _unpack(await server.call_tool("list_models", {}))

        expected = sum(len(prov.models) for prov in PROVIDER_CATALOG.values())
        assert result["count"] == expected
        assert {m["provider"] for m in result["models"]} == set(PROVIDER_CATALOG)

    async def test_list_models_unknown_provider_clean_error(self):
        server = _make_server()
        result = _unpack(await server.call_tool("list_models", {"provider": "bogus"}))

        assert result["success"] is False
        assert "bogus" in result["error"]


class TestErrorIsolation:
    """MCP-12/D3: no tool raises; the server stays responsive after a failure."""

    async def test_factory_raise_becomes_clean_error_result(self):
        server = _make_server(_raising_factory())
        result = _unpack(
            await server.call_tool("run_prompt", {"prompt": "hi", "provider": "bogus"})
        )
        assert result["success"] is False
        assert "bogus" in result["error"]

    async def test_session_survives_tool_error(self, tmp_path, monkeypatch):
        # Spec scenario MCP-12: an unconfigured provider fails cleanly and a
        # subsequent get_status call succeeds on the same server instance.
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        for var in _PROVIDER_KEY_ENVS:
            monkeypatch.delenv(var, raising=False)

        server = _make_server(_failing_factory())
        first = _unpack(await server.call_tool("run_prompt", {"prompt": "hi"}))
        assert first["success"] is False
        assert "API key" in first["error"]

        second = _unpack(await server.call_tool("get_status", {}))
        assert second["provider"] == "anthropic"
        assert second["session_count"] == 0


class TestDefaultFactory:
    """MCP-1: the default factory constructs agents from OHMConfig."""

    async def test_default_factory_constructs_agent(self, monkeypatch):
        captured: dict = {}

        def fake_agent_class(config: AgentConfig) -> _FakeAgent:
            captured["config"] = config
            return _FakeAgent(config)

        monkeypatch.setattr("ohm.core.agent.Agent", fake_agent_class)
        server = _make_server(
            config=OHMConfig(provider="anthropic", model="claude-sonnet-4-6")
        )

        result = _unpack(await server.call_tool("run_prompt", {"prompt": "hi"}))

        assert result["success"] is True
        assert captured["config"].provider == "anthropic"
        assert captured["config"].model == "claude-sonnet-4-6"
