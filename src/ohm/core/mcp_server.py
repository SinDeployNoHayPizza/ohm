"""OHM MCP Server — FastMCP core with injectable agent factory (MCP-1..MCP-12).

Exposes OHM as a Model Context Protocol server: exactly seven stateless
tools over stdio or streamable-HTTP transports. The agent factory is
injectable so tests never touch a real LLM (D2); every tool returns a
clean result dict and never raises — error isolation lives in the tool
layer (D3 / MCP-12).

Design decisions (see openspec/changes/mcp-server/design.md):

- D1  ``build_mcp_server()`` is a function returning a configured FastMCP.
- D2  ``AgentFactory = Callable[[AgentConfig], Any]``; the default factory
      constructs ``ohm.core.agent.Agent`` per call (stateless tools).
- D3  ``_safe_agent_call`` wraps the factory call AND ``await run(...)`` in
      ``try/except Exception`` so unknown-provider ``ValueError`` raised in
      ``_ensure_agent()`` surfaces as a clean error result.
- D4  ``run_stdio()`` / ``run_http(host, port)`` pass the transport to
      ``FastMCP.run()`` (blocking, anyio internally — no asyncio wrapper).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

from mcp.server.fastmcp import FastMCP

from ohm.core.agent import AgentConfig, AgentResponse
from ohm.core.config import OHMConfig

logger = logging.getLogger(__name__)

AgentFactory = Callable[[AgentConfig], Any]

_MCP_SERVER_NAME = "ohm-mcp"
_DEFAULT_HOST = "127.0.0.1"
# README documents `--port 3000`; FastMCP's own default (8000) differs.
_DEFAULT_PORT = 3000


def _sessions_dir() -> Path:
    """Resolve the sessions directory at call time.

    Uses ``Path.home()`` per call (not the import-time ``SESSIONS_DIR``
    constant) so tests that patch ``Path.home`` are honored.
    """
    return Path.home() / ".ohm" / "sessions"


def _default_agent_factory(config: AgentConfig) -> Any:
    """Construct a production agent from an ``AgentConfig`` (D2 / MCP-1).

    Imported lazily so tests can ``monkeypatch.setattr("ohm.core.agent.Agent")``.
    """
    from ohm.core.agent import Agent

    return Agent(config)


def _agent_config_from(cfg: OHMConfig) -> AgentConfig:
    """Map an ``OHMConfig`` onto an ``AgentConfig``.

    Mirrors the shape ``Agent.__init__`` builds when given no config, so
    the default factory receives the same fields the CLI would use.
    """
    return AgentConfig(
        provider=cfg.provider,
        model=cfg.model,
        max_tokens=cfg.max_tokens,
        temperature=cfg.temperature,
        sandbox=cfg.sandbox,
        tools=cfg.tools,
        system_prompt=cfg.system_prompt or AgentConfig.system_prompt,
        base_url=cfg.base_url,
    )


async def _safe_agent_call(
    agent_factory: AgentFactory,
    config: AgentConfig,
    prompt: str,
) -> AgentResponse:
    """Run one agent call, catching EVERY failure into a clean response (D3).

    ``Agent.run`` catches errors after ``_ensure_agent()``, but construction
    itself can raise (unknown provider ``ValueError``, ``ImportError``), so
    the factory call is wrapped too.
    """
    try:
        agent = agent_factory(config)
        return await agent.run(prompt)
    except Exception as exc:  # noqa: BLE001 — MCP-12 error isolation boundary
        logger.warning("MCP agent call failed: %s", exc)
        return AgentResponse(content="", success=False, error=str(exc))


def _result_dict(response: AgentResponse) -> dict[str, Any]:
    """Serialize an ``AgentResponse`` into the MCP result envelope (MCP-3)."""
    return {
        "content": response.content,
        "tokens_used": response.tokens_used,
        "latency_ms": response.latency_ms,
        "success": response.success,
        "error": response.error,
    }


def _model_dict(provider: str, model: Any) -> dict[str, Any]:
    """Serialize a ``ProviderModel`` into an MCP ``list_models`` entry."""
    return {
        "provider": provider,
        "id": model.id,
        "name": model.name,
        "context_window": model.context_window,
        "cost_input": model.cost_input,
        "cost_output": model.cost_output,
    }


def build_mcp_server(
    agent_factory: AgentFactory | None = None,
    *,
    name: str = _MCP_SERVER_NAME,
    host: str = "127.0.0.1",
    port: int = 8000,
    config: OHMConfig | None = None,
) -> FastMCP:
    """Build a configured FastMCP instance with exactly seven tools (MCP-1/2).

    Args:
        agent_factory: Callable receiving an ``AgentConfig`` and returning a
            duck-typed agent with ``async run(prompt) -> AgentResponse``.
            Defaults to a factory constructing ``ohm.core.agent.Agent``.
        name: MCP server name.
        host: Bind host (used by ``run_http`` transports).
        port: Bind port (used by ``run_http`` transports).
        config: Resolved OHM config. When omitted, deterministic defaults
            (``OHMConfig()``) are used so the server is offline-safe.
    """
    factory = agent_factory or _default_agent_factory
    cfg = config or OHMConfig()

    mcp = FastMCP(name, host=host, port=port)

    # NOTE: tool functions intentionally carry NO return-type annotations —
    # mcp 1.28.1 wraps annotated returns into a (unstructured, structured)
    # tuple; unannotated dict returns stay a plain content list.

    @mcp.tool()
    async def run_prompt(  # noqa: ANN202 — MCP-3 envelope, see note above
        prompt: str,
        provider: str | None = None,
        model: str | None = None,
        system_prompt: str | None = None,
    ):
        """Run a single prompt through the OHM agent."""
        agent_cfg = _agent_config_from(cfg)
        if provider:
            agent_cfg.provider = provider
        if model:
            agent_cfg.model = model
        if system_prompt is not None:
            agent_cfg.system_prompt = system_prompt
        response = await _safe_agent_call(factory, agent_cfg, prompt)
        return _result_dict(response)

    @mcp.tool()
    async def run_goal(  # noqa: ANN202 — MCP-4 envelope, see note above
        goal: str,
        provider: str | None = None,
        model: str | None = None,
    ):
        """Run the autonomous-goal loop (reuses the goal system prompt)."""
        from ohm.commands.goal import GOAL_SYSTEM_PROMPT

        agent_cfg = _agent_config_from(cfg)
        if provider:
            agent_cfg.provider = provider
        if model:
            agent_cfg.model = model
        agent_cfg.system_prompt = GOAL_SYSTEM_PROMPT
        response = await _safe_agent_call(factory, agent_cfg, goal)
        return _result_dict(response)

    @mcp.tool()
    async def get_status():  # noqa: ANN202 — MCP-5 envelope, see note above
        """Report version, provider, model, API-key status, session count."""
        import os

        from ohm import __version__
        from ohm.commands.session import _list_session_files
        from ohm.core.config import _API_KEY_ENV

        api_key_status: dict[str, str] = {}
        for provider_name, env_vars in _API_KEY_ENV.items():
            if provider_name == "ollama":
                api_key_status[provider_name] = "local"
            elif any(os.environ.get(var) for var in env_vars):
                api_key_status[provider_name] = "configured"
            else:
                api_key_status[provider_name] = "missing"

        return {
            "version": __version__,
            "provider": cfg.provider,
            "model": cfg.model,
            "providers": api_key_status,
            "session_count": len(_list_session_files(_sessions_dir())),
        }

    @mcp.tool()
    async def list_sessions():  # noqa: ANN202 — MCP-6 envelope, see note above
        """List persisted session identifiers (excluding the pointer file)."""
        from ohm.commands.session import _list_session_files

        session_ids = [f.stem for f in _list_session_files(_sessions_dir())]
        return {"sessions": session_ids, "count": len(session_ids)}

    @mcp.tool()
    async def get_session(session_id: str):  # noqa: ANN202 — MCP-6, note above
        """Return a persisted session, or a clean error when missing."""
        from ohm.commands.session import _load_session

        session_file = _sessions_dir() / f"{session_id}.json"
        if not session_file.is_file():
            return {"success": False, "error": f"Session '{session_id}' not found"}
        return {
            "success": True,
            "session_id": session_id,
            "session": _load_session(session_file),
        }

    @mcp.tool()
    async def list_skills():  # noqa: ANN202 — MCP-7 envelope, see note above
        """List skills from the registry (project-local + user-global)."""
        from ohm.core.skills.loader import DEFAULT_SKILL_SEARCH_PATHS, SkillLoader

        skill_names = sorted(SkillLoader.discover_skills(DEFAULT_SKILL_SEARCH_PATHS()))
        return {"skills": skill_names, "count": len(skill_names)}

    @mcp.tool()
    async def list_models(provider: str | None = None):  # noqa: ANN202 — MCP-7
        """List models from the provider catalog, optionally filtered."""
        from ohm.core.provider import PROVIDER_CATALOG

        if provider is not None:
            catalog = PROVIDER_CATALOG.get(provider)
            if catalog is None:
                return {"success": False, "error": f"Unknown provider '{provider}'"}
            models = [_model_dict(provider, m) for m in catalog.models]
            return {"provider": provider, "models": models, "count": len(models)}

        models: list[dict[str, Any]] = []
        for provider_name, catalog in PROVIDER_CATALOG.items():
            models.extend(_model_dict(provider_name, m) for m in catalog.models)
        return {"models": models, "count": len(models)}

    return mcp


def run_stdio(agent_factory: AgentFactory | None = None) -> None:
    """Serve MCP over stdio (blocking; MCP-8).

    ``FastMCP.run()`` blocks via anyio internally — no ``asyncio.run``
    wrapper (CF2).
    """
    from ohm.core.config import get_config

    server = build_mcp_server(agent_factory=agent_factory, config=get_config())
    server.run("stdio")


def run_http(
    host: str,
    port: int,
    agent_factory: AgentFactory | None = None,
) -> None:
    """Serve MCP over streamable HTTP on an explicit host/port (MCP-9).

    The port is ALWAYS passed explicitly — the FastMCP default (8000)
    differs from the documented 3000 (D4).
    """
    from ohm.core.config import get_config

    server = build_mcp_server(
        agent_factory=agent_factory,
        host=host,
        port=port,
        config=get_config(),
    )
    server.run("streamable-http")


def _resolve_server_args(args: Any, cfg: OHMConfig) -> dict[str, Any]:
    """Resolve transport/host/port: explicit CLI flag > config > defaults (D6).

    Defaults match the documented ``mcp_server`` config section
    (stdio, 127.0.0.1, 3000 — README:251).
    """
    mcp_server = getattr(cfg, "mcp_server", None) or {}
    transport = (
        getattr(args, "transport", None)
        or mcp_server.get("transport")
        or "stdio"
    )
    host = getattr(args, "host", None) or mcp_server.get("host") or _DEFAULT_HOST
    port = getattr(args, "port", None) or mcp_server.get("port") or _DEFAULT_PORT
    return {"transport": transport, "host": host, "port": int(port)}
