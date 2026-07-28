"""OHM Agent — wraps strands-agents for real LLM execution.

Based on:
    https://strandsagents.com/docs/user-guide/quickstart/python/
    https://strandsagents.com/docs/user-guide/concepts/model-providers/anthropic/
    https://strandsagents.com/docs/user-guide/concepts/tools/community-tools-package/
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# ── Provider → strands model class mapping ────────────────────

_PROVIDER_MODEL_MAP: dict[str, tuple[str, str]] = {
    "anthropic": ("strands.models.anthropic", "AnthropicModel"),
    "openai": ("strands.models.openai", "OpenAIModel"),
    "gemini": ("strands.models.gemini", "GeminiModel"),
    "ollama": ("strands.models.ollama", "OllamaModel"),
    "bedrock": ("strands.models.bedrock", "BedrockModel"),
}

# Default model per provider
_DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o",
    "gemini": "gemini-3.5-flash",
    "ollama": "llama3.2",
    "bedrock": "global.anthropic.claude-sonnet-4-6",
}

# Default tools — platform-aware
# shell needs termios (Unix only), python_repl needs fcntl (Unix only)
# editor, file_read, file_write work on all platforms
if sys.platform == "win32":
    _DEFAULT_TOOL_NAMES: list[str] = [
        "file_read", "file_write", "editor",
        "calculator", "current_time",
        "http_request", "think",
    ]
else:
    _DEFAULT_TOOL_NAMES: list[str] = [
        "shell", "file_read", "file_write", "editor",
        "calculator", "current_time",
        "http_request", "think", "python_repl",
    ]


# ── Provider resolution ───────────────────────────────────────

def _resolve_model(provider: str, model_id: str | None) -> Any:
    """Resolve provider + model_id into a strands model instance.

    Uses the canonical strands API:
        AnthropicModel(client_args=..., max_tokens=..., model_id=..., params=...)
        OpenAIModel(client_args=..., model_id=..., params=...)
    """
    import importlib

    provider_key = provider.lower()
    if provider_key not in _PROVIDER_MODEL_MAP:
        supported = ", ".join(_PROVIDER_MODEL_MAP)
        raise ValueError(f"Unknown provider '{provider}'. Supported: {supported}")

    module_path, class_name = _PROVIDER_MODEL_MAP[provider_key]
    resolved_model = model_id or _DEFAULT_MODELS.get(provider_key, "")

    try:
        module = importlib.import_module(module_path)
        model_cls = getattr(module, class_name)
    except (ImportError, AttributeError) as exc:
        raise RuntimeError(
            f"Could not load strands model for provider '{provider}': {exc}"
        ) from exc

    # Build kwargs per provider docs
    kwargs: dict[str, Any] = {}

    if provider_key == "anthropic":
        # https://strandsagents.com/docs/user-guide/concepts/model-providers/anthropic/
        # AnthropicModel(client_args={"api_key": ...}, max_tokens=..., model_id=..., params=...)
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            kwargs["client_args"] = {"api_key": api_key}
        kwargs["max_tokens"] = 4096
        if resolved_model:
            kwargs["model_id"] = resolved_model
        kwargs["params"] = {"temperature": 0.7}

    elif provider_key == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            kwargs["client_args"] = {"api_key": api_key}
        if resolved_model:
            kwargs["model_id"] = resolved_model

    elif provider_key == "gemini":
        # https://strandsagents.com/docs/user-guide/concepts/model-providers/google/
        # GeminiModel(client_args={"api_key": ...}, model_id=..., params=...)
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if api_key:
            kwargs["client_args"] = {"api_key": api_key}
        if resolved_model:
            kwargs["model_id"] = resolved_model
        kwargs["params"] = {
            "temperature": 0.7,
            "max_output_tokens": 4096,
        }

    elif provider_key == "ollama":
        if resolved_model:
            kwargs["model_id"] = resolved_model

    elif provider_key == "bedrock":
        if resolved_model:
            kwargs["model_id"] = resolved_model

    return model_cls(**kwargs)


def _load_tools(tool_names: list[str] | None = None) -> list[Any]:
    """Load strands_tools by name with graceful fallback."""
    names = tool_names or _DEFAULT_TOOL_NAMES
    loaded: list[Any] = []
    for name in names:
        try:
            mod = __import__("strands_tools", fromlist=[name])
            tool_fn = getattr(mod, name, None)
            if tool_fn is not None:
                loaded.append(tool_fn)
            else:
                logger.warning("Tool '%s' not found in strands_tools, skipping", name)
        except ImportError as exc:
            logger.warning("strands_tools.'%s' not available (%s), skipping", name, exc)
    return loaded


# ── Data classes ──────────────────────────────────────────────

@dataclass
class AgentConfig:
    """Configuration for an OHM agent."""
    name: str = "ohm-agent"
    model: str = "claude-sonnet-4-6"
    provider: str = "anthropic"
    sandbox: bool = True
    max_tokens: int = 4096
    temperature: float = 0.7
    tools: list[str] = field(default_factory=lambda: list(_DEFAULT_TOOL_NAMES))
    system_prompt: str = (
        "You are OHM, an autonomous coding agent. "
        "You have access to file operations, shell, editor, calculator, and HTTP tools. "
        "Execute tasks precisely and report results clearly."
    )


@dataclass
class AgentResponse:
    """Response from an agent execution."""
    content: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    success: bool = True
    error: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentState:
    """Current state of the agent."""
    is_running: bool = False
    current_task: str | None = None
    progress: float = 0.0
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0


# ── Main agent class ──────────────────────────────────────────

class Agent:
    """OHM agent backed by strands-agents.

    Usage::

        agent = Agent(AgentConfig(provider="anthropic", model="claude-sonnet-4-6"))
        response = await agent.run("Fix the bug in auth.py")
    """

    def __init__(self, config: AgentConfig | None = None) -> None:
        # If no config provided, load from OHM config system
        if config is None:
            try:
                from ohm.core.config import get_config
                ohm_cfg = get_config()
                config = AgentConfig(
                    provider=ohm_cfg.provider,
                    model=ohm_cfg.model,
                    max_tokens=ohm_cfg.max_tokens,
                    temperature=ohm_cfg.temperature,
                    sandbox=ohm_cfg.sandbox,
                    tools=ohm_cfg.tools,
                    system_prompt=ohm_cfg.system_prompt or AgentConfig.system_prompt,
                )
            except Exception:
                config = AgentConfig()
        self.config = config
        self.state = AgentState()
        self._strands_agent: Any = None  # lazy init

    def _ensure_agent(self) -> Any:
        """Lazy-init the underlying strands.Agent."""
        if self._strands_agent is not None:
            return self._strands_agent

        from strands import Agent as StrandsAgent

        model = _resolve_model(self.config.provider, self.config.model)
        tools = _load_tools(self.config.tools)

        self._strands_agent = StrandsAgent(
            model=model,
            system_prompt=self.config.system_prompt,
            tools=tools,
            name=self.config.name,
            # Disable console output in CLI mode — we capture ourselves
            callback_handler=None,
        )
        logger.info(
            "Agent initialized: provider=%s model=%s tools=%d",
            self.config.provider,
            self.config.model or _DEFAULT_MODELS.get(self.config.provider),
            len(tools),
        )
        return self._strands_agent

    async def run(self, prompt: str) -> AgentResponse:
        """Execute a prompt against the LLM."""
        agent = self._ensure_agent()
        self.state.is_running = True
        self.state.current_task = prompt
        t0 = time.monotonic()

        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, lambda: agent(prompt))
            latency_ms = (time.monotonic() - t0) * 1000

            content = self._extract_text(result)
            metrics = self._extract_metrics(result)

            self.state.is_running = False
            self.state.current_task = None
            self.state.tasks_completed += 1

            return AgentResponse(
                content=content,
                tokens_used=metrics.get("total_tokens", 0),
                latency_ms=latency_ms,
                success=True,
            )

        except Exception as exc:
            latency_ms = (time.monotonic() - t0) * 1000
            self.state.is_running = False
            self.state.current_task = None
            self.state.tasks_failed += 1
            return AgentResponse(
                content="",
                latency_ms=latency_ms,
                success=False,
                error=str(exc),
            )

    async def stream(self, prompt: str):  # noqa: ANN201
        """Stream a response token-by-token via async iterator.

        Yields event dicts from strands stream_async().
        """
        agent = self._ensure_agent()
        self.state.is_running = True
        self.state.current_task = prompt

        try:
            async for event in agent.stream_async(prompt):
                yield event
        finally:
            self.state.is_running = False
            self.state.current_task = None

    @staticmethod
    def _extract_text(result: Any) -> str:
        """Extract plain text from a strands AgentResult."""
        # AgentResult has .message which is a Message with .content (list of blocks)
        message = getattr(result, "message", result)
        if hasattr(message, "content"):
            blocks = message.content
            if isinstance(blocks, list):
                parts: list[str] = []
                for block in blocks:
                    if isinstance(block, dict) and "text" in block:
                        parts.append(block["text"])
                    elif isinstance(block, str):
                        parts.append(block)
                return "\n".join(parts) if parts else str(result)
            return str(blocks)
        if isinstance(message, str):
            return message
        return str(message)

    @staticmethod
    def _extract_metrics(result: Any) -> dict[str, Any]:
        """Extract usage metrics from AgentResult."""
        try:
            summary = result.metrics.get_summary()
            usage = summary.get("accumulated_usage", {})
            return {
                "total_tokens": usage.get("totalTokens", 0),
                "input_tokens": usage.get("inputTokens", 0),
                "output_tokens": usage.get("outputTokens", 0),
                "total_cycles": summary.get("total_cycles", 0),
                "total_duration": summary.get("total_duration", 0),
                "tool_usage": summary.get("tool_usage", {}),
            }
        except Exception:
            return {}

    def get_status(self) -> dict[str, Any]:
        """Get current agent status."""
        return {
            "name": self.config.name,
            "model": self.config.model,
            "provider": self.config.provider,
            "sandbox": self.config.sandbox,
            "is_running": self.state.is_running,
            "current_task": self.state.current_task,
            "total_tokens_used": self.state.total_tokens_used,
            "total_cost_usd": self.state.total_cost_usd,
            "tasks_completed": self.state.tasks_completed,
            "tasks_failed": self.state.tasks_failed,
            "tools": self.config.tools,
        }
