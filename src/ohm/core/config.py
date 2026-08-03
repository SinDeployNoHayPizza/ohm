"""OHM Configuration — loads and merges config from multiple sources.

Priority (highest wins):
    1. Environment variables (OHM_* prefix)
    2. Project config (.ohm/config.yaml in cwd)
    3. Global config (~/.ohm/config.yaml)
    4. Built-in defaults

Usage::

    from ohm.core.config import get_config
    cfg = get_config()
    print(cfg.provider)       # "anthropic"
    print(cfg.model)          # "claude-sonnet-4-6"
    print(cfg.api_key_for("anthropic"))  # "sk-..." or None
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────

GLOBAL_DIR = Path.home() / ".ohm"
GLOBAL_CONFIG = GLOBAL_DIR / "config.yaml"
SESSIONS_DIR = GLOBAL_DIR / "sessions"

PROJECT_DIR = Path(".ohm")
PROJECT_CONFIG = PROJECT_DIR / "config.yaml"

# ── Defaults ──────────────────────────────────────────────────

DEFAULTS: dict[str, Any] = {
    "provider": "anthropic",
    "model": "claude-sonnet-4-6",
    "max_tokens": 4096,
    "temperature": 0.7,
    "sandbox": True,
    "theme": "default",
    "system_prompt": None,
    "tools": [
        "file_read", "file_write", "editor",
        "calculator", "current_time",
        "http_request", "think",
    ],
    "mcp": {},
    "mcp_server": {"transport": "stdio", "host": "127.0.0.1", "port": 3000},
    "log_format": "text",
    "metrics_enabled": True,
}

# Environment variable → config key mapping
_ENV_MAP: dict[str, str] = {
    "OHM_PROVIDER": "provider",
    "OHM_MODEL": "model",
    "OHM_MAX_TOKENS": "max_tokens",
    "OHM_TEMPERATURE": "temperature",
    "OHM_SANDBOX": "sandbox",
    "OHM_LOG_LEVEL": "log_level",
    "OHM_LOG_FORMAT": "log_format",
    "OHM_METRICS_ENABLED": "metrics_enabled",
}

# API key env vars per provider
_API_KEY_ENV: dict[str, list[str]] = {
    "anthropic": ["ANTHROPIC_API_KEY"],
    "openai": ["OPENAI_API_KEY"],
    "gemini": ["GEMINI_API_KEY"],
    "bedrock": ["AWS_ACCESS_KEY_ID"],
    "ollama": [],  # no key needed
    "nvidia-nim": ["NVAPI_KEY"],
    "xiaomi-mimo": ["MIMO_API_KEY"],
}

# ── YAML loading ──────────────────────────────────────────────

def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file, return dict. Returns {} on any error."""
    if not path.is_file():
        return {}
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict):
            return data
        logger.warning("Config file %s is not a dict, ignoring", path)
        return {}
    except Exception as exc:
        logger.warning("Failed to load config %s: %s", path, exc)
        return {}


def _save_yaml(path: Path, data: dict[str, Any]) -> None:
    """Save a dict to YAML file. Creates parent dirs."""
    import yaml
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def _load_dotenv(path: Path) -> dict[str, str]:
    """Minimal .env loader — parses KEY=VALUE lines."""
    if not path.is_file():
        return {}
    env: dict[str, str] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                # Remove surrounding quotes
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]
                env[key] = value
    except Exception as exc:
        logger.warning("Failed to load .env %s: %s", path, exc)
    return env


# ── Config dataclass ──────────────────────────────────────────

@dataclass
class OHMConfig:
    """Resolved OHM configuration."""
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 4096
    temperature: float = 0.7
    sandbox: bool = True
    theme: str = "default"
    system_prompt: str | None = None
    tools: list[str] = field(default_factory=lambda: [
        "file_read", "file_write", "editor",
        "calculator", "current_time",
        "http_request", "think",
    ])
    mcp: dict[str, Any] = field(default_factory=dict)
    mcp_server: dict[str, Any] = field(
        default_factory=lambda: dict(DEFAULTS["mcp_server"])
    )
    log_level: str = "INFO"
    log_format: str = "text"
    metrics_enabled: bool = True
    base_url: str | None = None

    # Source tracking (which files were loaded)
    global_config_path: Path | None = None
    project_config_path: Path | None = None
    dotenv_path: Path | None = None

    def api_key_for(self, provider: str) -> str | None:
        """Get API key for a provider from environment."""
        for env_var in _API_KEY_ENV.get(provider, []):
            value = os.environ.get(env_var)
            if value:
                return value
        return None

    @property
    def available_providers(self) -> list[str]:
        """List providers that have API keys configured."""
        from ohm.core.provider import KNOWN_PROVIDERS

        available: list[str] = []
        for name in KNOWN_PROVIDERS:
            if name == "ollama" or self.api_key_for(name) is not None:
                available.append(name)
        return available

    def resolve_provider(self, name: str | None = None) -> Any:
        """Return a configured Provider instance for the given name."""
        from ohm.core.provider import create_provider

        provider_name = name or self.provider
        return create_provider(
            provider_name,
            api_key=self.api_key_for(provider_name),
            base_url=self.base_url,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize config to dict (for YAML/JSON output)."""
        return {
            "provider": self.provider,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "sandbox": self.sandbox,
            "theme": self.theme,
            "system_prompt": self.system_prompt,
            "tools": self.tools,
            "mcp": self.mcp,
            "mcp_server": self.mcp_server,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "metrics_enabled": self.metrics_enabled,
            "base_url": self.base_url,
        }


# ── Loader ────────────────────────────────────────────────────

def load_config(
    global_path: Path | None = None,
    project_path: Path | None = None,
    dotenv_path: Path | None = None,
) -> OHMConfig:
    """Load and merge configuration from all sources.

    Priority: env vars > project > global > defaults.
    """
    gpath = global_path or GLOBAL_CONFIG
    ppath = project_path or PROJECT_CONFIG
    dpath = dotenv_path or Path(".env")

    # 1. Start with defaults
    merged: dict[str, Any] = dict(DEFAULTS)

    # 2. Load .env file into os.environ (does not overwrite existing)
    dotenv_data = _load_dotenv(dpath)
    for key, value in dotenv_data.items():
        if key not in os.environ:
            os.environ[key] = value

    # 3. Merge global config
    global_data = _load_yaml(gpath)
    merged.update({k: v for k, v in global_data.items() if v is not None})

    # 4. Merge project config (overrides global)
    project_data = _load_yaml(ppath)
    merged.update({k: v for k, v in project_data.items() if v is not None})

    # 5. Merge env vars (highest priority)
    for env_var, config_key in _ENV_MAP.items():
        env_value = os.environ.get(env_var)
        if env_value is not None:
            # Type coercion
            if config_key in ("max_tokens",):
                try:
                    merged[config_key] = int(env_value)
                except ValueError:
                    pass
            elif config_key in ("temperature",):
                try:
                    merged[config_key] = float(env_value)
                except ValueError:
                    pass
            elif config_key in ("sandbox", "metrics_enabled"):
                merged[config_key] = env_value.lower() in ("true", "1", "yes")
            else:
                merged[config_key] = env_value

    # Validate log_format (PC-1/D3): invalid values fall back to "text"
    log_format = merged.get("log_format", "text")
    if log_format not in ("text", "json"):
        logger.warning("Invalid log_format %r; falling back to 'text'", log_format)
        log_format = "text"
    merged["log_format"] = log_format

    # Merge mcp_server over the FULL defaults (CF1): a partial config like
    # `mcp_server: {port: 3000}` keeps the default transport/host.
    mcp_server = dict(DEFAULTS["mcp_server"])
    configured_mcp_server = merged.get("mcp_server") or {}
    if isinstance(configured_mcp_server, dict):
        mcp_server.update(
            {k: v for k, v in configured_mcp_server.items() if v is not None}
        )

    return OHMConfig(
        provider=merged["provider"],
        model=merged["model"],
        max_tokens=merged["max_tokens"],
        temperature=merged["temperature"],
        sandbox=merged["sandbox"],
        theme=merged.get("theme", "default"),
        system_prompt=merged.get("system_prompt"),
        tools=merged["tools"],
        mcp=merged.get("mcp", {}),
        mcp_server=mcp_server,
        log_level=merged.get("log_level", "INFO"),
        log_format=log_format,
        metrics_enabled=merged.get("metrics_enabled", True),
        base_url=merged.get("base_url"),
        global_config_path=gpath if gpath.exists() else None,
        project_config_path=ppath if ppath.exists() else None,
        dotenv_path=dpath if dpath.exists() else None,
    )


# ── Singleton ─────────────────────────────────────────────────

_config: OHMConfig | None = None


def get_config(reload: bool = False) -> OHMConfig:
    """Get or reload the global config singleton."""
    global _config
    if _config is None or reload:
        _config = load_config()
    return _config


def save_global_config(config: OHMConfig) -> None:
    """Save config to global config file."""
    _save_yaml(GLOBAL_CONFIG, config.to_dict())


def save_project_config(config: OHMConfig) -> None:
    """Save config to project config file."""
    _save_yaml(PROJECT_CONFIG, config.to_dict())
