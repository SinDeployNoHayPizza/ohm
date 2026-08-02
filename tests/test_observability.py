"""Tests for OHM observability layer — logging bootstrap, JSON formatter,
metrics registry, agent/provider instrumentation, and CLI surfaces.

Written strictly TDD against the structured-logging-metrics change spec
(OBS-1..OBS-9): each test class is added before the production code it
describes exists.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path

import pytest

from ohm.core.agent import Agent, AgentConfig
from ohm.core.config import OHMConfig, _save_yaml, load_config
from ohm.core.observability import JSONFormatter, get_metrics, setup_logging
from ohm.core.provider import FallbackProvider, Provider, ProviderConfig, ProviderStatus, retry
from ohm.commands import doctor as doctor_cmd
from ohm.commands import status as status_cmd
from ohm.commands.run import _handle_run


@pytest.fixture(autouse=True)
def _clean_registry() -> None:
    """Isolate the metrics registry and root logger between tests."""
    setup_logging(OHMConfig())
    get_metrics().reset()
    yield
    get_metrics().reset()
    setup_logging(OHMConfig())


def _no_files(tmp_path) -> tuple[Path, Path, Path]:
    """Return nonexistent config paths so load_config touches nothing real."""
    return (
        tmp_path / "nope-global.yaml",
        tmp_path / "nope-project.yaml",
        tmp_path / "nope.env",
    )


class TestLoggingBootstrap:
    """S1: OBS-1 (level wiring), OBS-2 (json/text format), D3 (validation)."""

    def test_env_debug_surfaces_info_on_stderr(self, tmp_path, capsys):
        """OBS-1: OHM_LOG_LEVEL=DEBUG raises the root level; INFO reaches stderr."""
        os.environ["OHM_LOG_LEVEL"] = "DEBUG"
        cfg = load_config(*_no_files(tmp_path))
        assert cfg.log_level == "DEBUG"
        setup_logging(cfg)
        logging.getLogger("ohm.core.agent").info("agent-init record")
        err = capsys.readouterr().err
        assert "agent-init record" in err

    def test_default_suppresses_info(self, capsys):
        """OBS-1: WARNING level suppresses INFO records."""
        setup_logging(OHMConfig(log_level="WARNING"))
        logging.getLogger("ohm.core.agent").info("must be suppressed")
        err = capsys.readouterr().err
        assert "must be suppressed" not in err
        logging.getLogger("ohm.core.agent").warning("visible warning")
        err2 = capsys.readouterr().err
        assert "visible warning" in err2

    def test_json_line_parses_with_required_fields(self, capsys):
        """OBS-2: json format emits one parseable object with the four fields."""
        setup_logging(OHMConfig(log_level="INFO", log_format="json"))
        logging.getLogger("ohm.core.agent").info("agent initialized")
        err = capsys.readouterr().err
        data = json.loads(err.strip().splitlines()[0])
        assert data["level"] == "INFO"
        assert data["logger"] == "ohm.core.agent"
        assert data["message"] == "agent initialized"
        assert data["timestamp"]

    def test_text_format_is_readable_default(self, capsys):
        """OBS-2: default output is human-readable plain text."""
        setup_logging(OHMConfig(log_level="INFO"))
        logging.getLogger("ohm.core.agent").info("plain text record")
        err = capsys.readouterr().err
        assert "INFO" in err
        assert "plain text record" in err

    def test_env_log_format_override(self, tmp_path):
        """Task 1.6: OHM_LOG_FORMAT env var overrides config log_format."""
        os.environ["OHM_LOG_FORMAT"] = "json"
        cfg = load_config(*_no_files(tmp_path))
        assert cfg.log_format == "json"

    def test_invalid_log_level_falls_back_to_info_with_warning(self, caplog):
        """D3: invalid level is guarded in setup_logging → INFO + warning."""
        with caplog.at_level(logging.WARNING, logger="ohm.core.observability"):
            setup_logging(OHMConfig(log_level="LOL"))
        assert logging.getLogger().level == logging.INFO
        assert any("log_level" in r.message for r in caplog.records)

    def test_invalid_log_format_falls_back_to_text_with_warning(self, tmp_path, caplog):
        """D3: invalid log_format is guarded in load_config → text + warning."""
        cfg_file = tmp_path / "config.yaml"
        _save_yaml(cfg_file, {"log_format": "xml"})
        with caplog.at_level(logging.WARNING, logger="ohm.core.config"):
            cfg = load_config(
                global_path=tmp_path / "no-global.yaml",
                project_path=cfg_file,
                dotenv_path=tmp_path / "no.env",
            )
        assert cfg.log_format == "text"
        assert any("log_format" in r.message for r in caplog.records)

    def test_setup_idempotent_no_duplicate_handlers(self):
        """D3: repeated setup_logging never stacks duplicate handlers."""
        setup_logging(OHMConfig(log_level="DEBUG"))
        setup_logging(OHMConfig(log_level="DEBUG"))
        setup_logging(OHMConfig(log_level="DEBUG"))
        root = logging.getLogger()
        ohm_handlers = [
            h for h in root.handlers if getattr(h, "_ohm_bootstrap", False)
        ]
        assert len(ohm_handlers) == 1


class TestJsonFormatterAllowlist:
    """S1: F1/OBS-8 — the formatter serializes a fixed allowlist only."""

    @staticmethod
    def _record(extra_attrs: dict | None = None, exc_info=None) -> logging.LogRecord:
        record = logging.LogRecord(
            name="ohm.core.agent",
            level=logging.DEBUG,
            pathname=__file__,
            lineno=1,
            msg="run completed",
            args=(),
            exc_info=exc_info,
        )
        for key, value in (extra_attrs or {}).items():
            setattr(record, key, value)
        return record

    def test_key_like_text_never_serialized(self):
        """F1/OBS-8: prompt/key text attached to the record never reaches output."""
        secret = "sk-ant-secret-abcdef0123456789"
        fmt = JSONFormatter()
        record = self._record(
            extra_attrs={
                "prompt": f"{secret} hello world",
                "api_key": secret,
                "metadata": {"tokens": 3, "prompt_len": 11},
            },
            exc_info=(ValueError, ValueError(f"boom {secret}"), None),
        )
        out = fmt.format(record)
        data = json.loads(out)
        # Allowlist keys only — never args, exc_info, or arbitrary extras.
        assert set(data) <= {"timestamp", "level", "logger", "message", "metadata"}
        assert secret not in out
        assert "boom" not in out
        assert "exc_info" not in out
        # Only the explicit metadata dict may carry lengths/counts.
        assert data["metadata"] == {"tokens": 3, "prompt_len": 11}

    def test_metadata_omitted_when_absent(self):
        """Triangulation: no metadata attribute → no metadata key in output."""
        fmt = JSONFormatter()
        out = fmt.format(self._record())
        data = json.loads(out)
        assert set(data) == {"timestamp", "level", "logger", "message"}
        assert "prompt" not in out


class TestMetricsRegistry:
    """S2: OBS-4 (accumulate/disabled), OBS-7 (cost slot), D5 (isolation)."""

    def test_accumulate_snapshot_shape(self):
        """OBS-4/OBS-7: counters + histograms accumulate; cost.usd is 0.0."""
        m = get_metrics()
        m.increment("ohm.metrics.runs.success")
        m.increment("ohm.metrics.tokens.total", 100)
        m.record_histogram("ohm.metrics.latency.ms", 250.5)
        m.record_histogram("ohm.metrics.latency.ms", 150.25)
        snap = m.snapshot()
        assert snap["enabled"] is True
        assert snap["counters"]["ohm.metrics.runs.success"] == 1
        assert snap["counters"]["ohm.metrics.tokens.total"] == 100
        hist = snap["histograms"]["ohm.metrics.latency.ms"]
        assert hist["count"] == 2
        assert hist["sum"] == 400.75
        assert hist["min"] == 150.25
        assert hist["max"] == 250.5
        assert hist["avg"] == 200.375
        assert snap["cost"]["usd"] == 0.0

    def test_disabled_records_nothing_snapshot_empty(self):
        """OBS-4: metrics_enabled=false → records nothing, snapshot {}."""
        setup_logging(OHMConfig(metrics_enabled=False))
        m = get_metrics()
        m.increment("ohm.metrics.runs.success")
        m.record_histogram("ohm.metrics.latency.ms", 10.0)
        assert m.snapshot() == {}

    def test_metrics_enabled_env_var_coerces_bool(self, tmp_path):
        """Task 2.5/F3: OHM_METRICS_ENABLED uses sandbox-style bool coercion."""
        os.environ["OHM_METRICS_ENABLED"] = "false"
        cfg = load_config(*_no_files(tmp_path))
        assert cfg.metrics_enabled is False
        os.environ["OHM_METRICS_ENABLED"] = "1"
        cfg = load_config(*_no_files(tmp_path))
        assert cfg.metrics_enabled is True

    def test_reset_clears(self):
        """Task 2.3: reset() clears all accumulated counters and histograms."""
        m = get_metrics()
        m.increment("ohm.metrics.runs.success")
        m.record_histogram("ohm.metrics.latency.ms", 1.0)
        m.reset()
        snap = m.snapshot()
        assert snap["counters"] == {}
        assert snap["histograms"] == {}

    def test_broken_internals_never_raise(self):
        """D5: registry swallows internal errors — call sites never propagate."""

        class Unhashable:
            def __hash__(self) -> int:
                raise RuntimeError("boom")

        m = get_metrics()
        m.increment(Unhashable())  # must not raise
        m.record_histogram(Unhashable(), 1.0)  # must not raise
        snap = m.snapshot()
        assert snap["counters"] == {}
        assert snap["histograms"] == {}


class TestAgentMetrics:
    """S3: OBS-5 — agent run/stream records telemetry without altering results."""

    @staticmethod
    def _fake_result(tokens: int, cycles: int, tool_usage: dict) -> object:
        class FakeMetrics:
            def get_summary(self):
                return {
                    "accumulated_usage": {
                        "totalTokens": tokens,
                        "inputTokens": tokens - 50,
                        "outputTokens": 50,
                    },
                    "total_cycles": cycles,
                    "total_duration": 1.5,
                    "tool_usage": tool_usage,
                }

        class FakeMsg:
            content = [{"text": "ok"}]

        class FakeResult:
            message = FakeMsg()
            metrics = FakeMetrics()

        return FakeResult()

    async def test_successful_run_records_metrics(self):
        """OBS-5: success, latency, tokens, cycles, tool usage all recorded."""
        agent = Agent(AgentConfig())
        agent._ensure_agent = lambda: (
            lambda prompt: self._fake_result(150, 2, {"file_read": 1, "editor": 2})
        )
        resp = await agent.run("hello")
        assert resp.success is True
        snap = get_metrics().snapshot()
        assert snap["counters"]["ohm.metrics.runs.success"] == 1
        assert snap["counters"]["ohm.metrics.tokens.total"] == 150
        assert snap["counters"]["ohm.metrics.tokens.input"] == 100
        assert snap["counters"]["ohm.metrics.tokens.output"] == 50
        assert snap["counters"]["ohm.metrics.cycles.total"] == 2
        assert snap["counters"]["ohm.metrics.tools.calls"] == 3
        assert snap["counters"]["ohm.metrics.tools.file_read"] == 1
        assert snap["counters"]["ohm.metrics.tools.editor"] == 2
        assert snap["histograms"]["ohm.metrics.latency.ms"]["count"] == 1

    async def test_failed_run_records_failure_no_propagation(self):
        """OBS-5: failure counter increments; instrumentation never raises."""

        def boom(prompt):
            raise RuntimeError("api down")

        agent = Agent(AgentConfig())
        agent._ensure_agent = lambda: boom
        resp = await agent.run("hello")
        assert resp.success is False
        assert resp.error is not None
        snap = get_metrics().snapshot()
        assert snap["counters"]["ohm.metrics.runs.failure"] == 1
        assert "ohm.metrics.runs.success" not in snap["counters"]

    async def test_stream_records_success_metrics(self):
        """OBS-5: stream completion records success counters too."""

        class FakeStrandsAgent:
            async def stream_async(self, prompt):
                yield {"type": "text", "data": "hi"}

            _last_result = TestAgentMetrics._fake_result(200, 1, {})

        agent = Agent(AgentConfig())
        agent._ensure_agent = lambda: FakeStrandsAgent()
        events = []
        async for event in agent.stream("hello"):
            events.append(event)
        snap = get_metrics().snapshot()
        assert snap["counters"]["ohm.metrics.runs.success"] == 1
        assert snap["counters"]["ohm.metrics.tokens.total"] == 200


class TestProviderMetrics:
    """S3: OBS-6 — retry attempts, transient statuses, failover events."""

    def test_429_retry_records_attempts_and_transient(self):
        """OBS-6: a 429 that succeeds on retry records attempts + transient.429."""

        class _Harness:
            def __init__(self, codes):
                self.codes = codes
                self.call_count = 0

            def __call__(self):
                idx = self.call_count
                self.call_count += 1
                status = self.codes[idx]
                if status >= 400:
                    exc = RuntimeError(f"HTTP {status}")
                    setattr(exc, "status_code", status)
                    raise exc
                return status

        harness = _Harness([429, 200])

        @retry(max_retries=2, base=0.001)
        def call() -> int:
            return harness()

        assert call() == 200
        snap = get_metrics().snapshot()
        assert snap["counters"]["ohm.metrics.provider.retry.attempts"] == 1
        assert snap["counters"]["ohm.metrics.provider.transient.429"] == 1

    def test_failover_records_failover_counter(self):
        """OBS-6: FallbackProvider failover to secondary increments the counter."""

        class FailingProvider(Provider):
            def create_model(self):
                return None

            def get_models(self):
                return []

            def check_health(self):
                return ProviderStatus.UNHEALTHY

            def get_status(self):
                return {"name": "fail"}

            def complete(self, model: str, messages: list, **kwargs):
                raise RuntimeError("HTTP 429")

        class WorkingProvider(Provider):
            def create_model(self):
                return None

            def get_models(self):
                return []

            def check_health(self):
                return ProviderStatus.HEALTHY

            def get_status(self):
                return {"name": "work"}

            def complete(self, model: str, messages: list, **kwargs):
                return {"content": "from secondary", "model": model}

        primary = FailingProvider(ProviderConfig(name="primary", display_name="Primary"))
        secondary = WorkingProvider(ProviderConfig(name="secondary", display_name="Secondary"))
        fallback = FallbackProvider(primary, secondary)

        result = fallback.complete("test-model", [])
        assert result["content"] == "from secondary"
        snap = get_metrics().snapshot()
        assert snap["counters"]["ohm.metrics.provider.failover"] == 1


class TestCliMetricsJson:
    """S4: OBS-9 — doctor/status --json expose a nested ``metrics`` section."""

    def test_doctor_json_includes_populated_metrics(self, capsys):
        """OBS-9: doctor --json shows recorded metrics."""
        get_metrics().increment("ohm.metrics.runs.success", 2)
        get_metrics().record_histogram("ohm.metrics.latency.ms", 12.5)
        rc = doctor_cmd.execute(argparse.Namespace(json=True))
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert "metrics" in out
        assert out["metrics"]["counters"]["ohm.metrics.runs.success"] == 2
        assert out["metrics"]["histograms"]["ohm.metrics.latency.ms"]["count"] == 1
        assert out["metrics"]["cost"] == {"usd": 0.0}

    def test_doctor_json_metrics_empty_when_nothing_recorded(self, capsys):
        """OBS-9: metrics section present and empty-zero by default."""
        rc = doctor_cmd.execute(argparse.Namespace(json=True))
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert "metrics" in out
        assert out["metrics"]["counters"] == {}
        assert out["metrics"]["histograms"] == {}

    def test_status_json_includes_metrics_section(self, capsys):
        """OBS-9: status --json exposes the same nested metrics section."""
        get_metrics().increment("ohm.metrics.provider.failover", 1)
        rc = status_cmd.handler(argparse.Namespace(as_json=True))
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert "metrics" in out
        assert out["metrics"]["counters"]["ohm.metrics.provider.failover"] == 1
        assert "enabled" in out["metrics"]


class TestStdoutPurity:
    """S4: OBS-3 (CRITICAL) — run output goes to stdout, logs to stderr."""

    def test_run_stdout_contains_only_response(self, capsys):
        """OBS-3: json+DEBUG — stdout is exactly the response; logs on stderr."""
        setup_logging(OHMConfig(log_level="DEBUG", log_format="json"))

        def fake_call(prompt):
            logging.getLogger("ohm.core.agent").debug("inner-trace record")
            return TestAgentMetrics._fake_result(80, 1, {})

        agent = Agent(AgentConfig())
        agent._ensure_agent = lambda: fake_call

        rc = _handle_run(agent, "hello")
        captured = capsys.readouterr()
        assert rc == 0
        # Purity: nothing but the response content on stdout
        assert captured.out.strip() == "ok"
        # Logs went to stderr as parseable JSON lines
        json_lines = [
            json.loads(line)
            for line in captured.err.splitlines()
            if line.lstrip().startswith("{")
        ]
        messages = [line["message"] for line in json_lines]
        assert "inner-trace record" in messages
