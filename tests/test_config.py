"""Tests for OHM configuration system."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from ohm.core.config import (
    OHMConfig,
    load_config,
    _load_yaml,
    _save_yaml,
    _load_dotenv,
    DEFAULTS,
)


class TestLoadYaml:
    def test_returns_empty_for_missing_file(self):
        result = _load_yaml(Path("/nonexistent/path.yaml"))
        assert result == {}

    def test_loads_valid_yaml(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("provider: openai\nmodel: gpt-4o\n")
        result = _load_yaml(config_file)
        assert result["provider"] == "openai"
        assert result["model"] == "gpt-4o"

    def test_returns_empty_for_invalid_yaml(self, tmp_path):
        config_file = tmp_path / "bad.yaml"
        config_file.write_text("{{invalid yaml}}")
        result = _load_yaml(config_file)
        assert result == {}

    def test_returns_empty_for_non_dict(self, tmp_path):
        config_file = tmp_path / "list.yaml"
        config_file.write_text("- item1\n- item2\n")
        result = _load_yaml(config_file)
        assert result == {}


class TestSaveYaml:
    def test_creates_file(self, tmp_path):
        config_file = tmp_path / "sub" / "config.yaml"
        _save_yaml(config_file, {"provider": "anthropic"})
        assert config_file.exists()
        data = yaml.safe_load(config_file.read_text())
        assert data["provider"] == "anthropic"

    def test_roundtrip(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        original = {"provider": "gemini", "model": "gemini-2.5-flash", "tools": ["calculator"]}
        _save_yaml(config_file, original)
        loaded = _load_yaml(config_file)
        assert loaded == original


class TestLoadDotenv:
    def test_returns_empty_for_missing_file(self):
        result = _load_dotenv(Path("/nonexistent/.env"))
        assert result == {}

    def test_parses_key_value_pairs(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            'ANTHROPIC_API_KEY=sk-ant-123\n'
            'OPENAI_API_KEY="sk-proj-456"\n'
            '# comment line\n'
            'GEMINI_API_KEY=AIza789\n'
        )
        result = _load_dotenv(env_file)
        assert result["ANTHROPIC_API_KEY"] == "sk-ant-123"
        assert result["OPENAI_API_KEY"] == "sk-proj-456"
        assert result["GEMINI_API_KEY"] == "AIza789"


class TestOHMConfig:
    def test_default_values(self):
        cfg = OHMConfig()
        assert cfg.provider == "anthropic"
        assert cfg.model == "claude-sonnet-4-6"
        assert cfg.max_tokens == 4096
        assert cfg.temperature == 0.7
        assert cfg.sandbox is True
        assert cfg.theme == "default"

    def test_to_dict(self):
        cfg = OHMConfig(provider="openai", model="gpt-4o", theme="ocean")
        d = cfg.to_dict()
        assert d["provider"] == "openai"
        assert d["model"] == "gpt-4o"
        assert d["theme"] == "ocean"
        assert "sandbox" in d
        assert "tools" in d

    def test_api_key_for_returns_none_when_missing(self):
        cfg = OHMConfig()
        # Make sure the env var is not set
        os.environ.pop("ANTHROPIC_API_KEY", None)
        assert cfg.api_key_for("anthropic") is None

    def test_api_key_for_returns_value_when_set(self):
        cfg = OHMConfig()
        os.environ["ANTHROPIC_API_KEY"] = "sk-test-123"
        try:
            assert cfg.api_key_for("anthropic") == "sk-test-123"
        finally:
            del os.environ["ANTHROPIC_API_KEY"]

    def test_available_providers_empty_when_no_keys(self):
        cfg = OHMConfig()
        # Clear all keys
        for var in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "AWS_ACCESS_KEY_ID"]:
            os.environ.pop(var, None)
        available = cfg.available_providers
        assert "ollama" in available  # ollama always available


class TestLoadConfig:
    def test_defaults_when_no_files(self, tmp_path):
        cfg = load_config(
            global_path=tmp_path / "nonexistent" / "global.yaml",
            project_path=tmp_path / "nonexistent" / "project.yaml",
            dotenv_path=tmp_path / "nonexistent" / ".env",
        )
        assert cfg.provider == "anthropic"
        assert cfg.model == "claude-sonnet-4-6"
        assert cfg.global_config_path is None
        assert cfg.project_config_path is None

    def test_global_config_overrides_defaults(self, tmp_path):
        import ohm.core.config as cfg_mod
        # Clear singleton cache
        cfg_mod._config = None
        global_file = tmp_path / "global.yaml"
        _save_yaml(global_file, {"provider": "openai", "model": "gpt-4o"})
        cfg = load_config(
            global_path=global_file,
            project_path=tmp_path / "nonexistent" / "project.yaml",
            dotenv_path=tmp_path / "nonexistent" / ".env",
        )
        assert cfg.provider == "openai"
        assert cfg.model == "gpt-4o"

    def test_project_overrides_global(self, tmp_path):
        global_file = tmp_path / "global.yaml"
        project_file = tmp_path / "project.yaml"
        _save_yaml(global_file, {"provider": "openai"})
        _save_yaml(project_file, {"provider": "gemini", "model": "gemini-2.5-flash"})
        cfg = load_config(global_path=global_file, project_path=project_file)
        assert cfg.provider == "gemini"
        assert cfg.model == "gemini-2.5-flash"

    def test_env_var_overrides_project(self, tmp_path):
        project_file = tmp_path / "project.yaml"
        _save_yaml(project_file, {"provider": "openai"})
        os.environ["OHM_PROVIDER"] = "anthropic"
        try:
            cfg = load_config(project_path=project_file)
            assert cfg.provider == "anthropic"
        finally:
            del os.environ["OHM_PROVIDER"]

    def test_dotenv_loaded(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("ANTHROPIC_API_KEY=sk-test-env\n")
        os.environ.pop("ANTHROPIC_API_KEY", None)
        cfg = load_config(dotenv_path=env_file)
        assert cfg.api_key_for("anthropic") == "sk-test-env"
