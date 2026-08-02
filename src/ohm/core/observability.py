"""OHM observability layer — structured logging bootstrap and in-process metrics.

Provides::

    setup_logging(cfg)  — bootstraps the root logger (level from
                          ``cfg.log_level``, stderr-only handler, optional
                          ``JSONFormatter``) and applies ``cfg.metrics_enabled``.
    JSONFormatter       — emits one JSON object per record; allowlisted fields
                          only (OBS-8: no prompt bodies, keys, or ``exc_info``).
    MetricsRegistry     — thread-safe counters/histograms registry.
    get_metrics()       — module-level registry singleton.

Wire at the CLI/TUI entry point; logs always go to stderr, never stdout
(OBS-3), and instrumentation call sites never propagate registry errors (D5).
"""

from __future__ import annotations

import json
import logging
import sys
import threading
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ohm.core.config import OHMConfig

logger = logging.getLogger(__name__)

# Flag applied by setup_logging(cfg.metrics_enabled); the registry honors it.
_metrics_enabled: bool = True

_HANDLER_MARKER = "_ohm_bootstrap"
_VALID_LOG_LEVELS = ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET")
_VALID_LOG_FORMATS = ("text", "json")


class JSONFormatter(logging.Formatter):
    """Serialize each log record as one JSON object with allowlisted fields.

    OBS-2: every record is one JSON object with ``timestamp``, ``level``,
    ``logger`` and ``message``. OBS-8: ``metadata`` is included only when the
    record explicitly carries a dict under that name — record args,
    ``exc_info``/tracebacks, and arbitrary extra attributes are NEVER
    serialized, so prompt content and API keys cannot leak into output.
    """

    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        metadata = getattr(record, "metadata", None)
        if isinstance(metadata, dict):
            data["metadata"] = metadata
        return json.dumps(data, ensure_ascii=False, default=str)


def setup_logging(cfg: OHMConfig) -> None:
    """Bootstrap the root logger from an :class:`OHMConfig`.

    Applies ``cfg.log_level`` (invalid values fall back to INFO with a
    warning), installs a single stderr-only handler (idempotent — repeated
    calls never duplicate handlers), selects text vs ``JSONFormatter`` from
    ``cfg.log_format``, and applies ``cfg.metrics_enabled`` to the registry.

    Never raises: observability must never block CLI/TUI startup.
    """
    try:
        level_name = (getattr(cfg, "log_level", "INFO") or "INFO").upper()
        if level_name not in _VALID_LOG_LEVELS:
            logger.warning("Invalid log_level %r; falling back to INFO", cfg.log_level)
            level_name = "INFO"

        log_format = getattr(cfg, "log_format", "text")
        if log_format not in _VALID_LOG_FORMATS:
            logger.warning("Invalid log_format %r; falling back to 'text'", log_format)
            log_format = "text"

        root = logging.getLogger()
        root.setLevel(getattr(logging, level_name))

        # Idempotent: remove our own previous handler, never duplicate (D3).
        for handler in list(root.handlers):
            if getattr(handler, _HANDLER_MARKER, False):
                root.removeHandler(handler)

        handler = logging.StreamHandler(sys.stderr)
        setattr(handler, _HANDLER_MARKER, True)
        if log_format == "json":
            handler.setFormatter(JSONFormatter())
        else:
            handler.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
            )
        root.addHandler(handler)

        global _metrics_enabled
        _metrics_enabled = getattr(cfg, "metrics_enabled", True)
    except Exception:  # noqa: BLE001 — never block startup
        pass


class MetricsRegistry:
    """Thread-safe in-process registry for ``ohm.metrics.*`` telemetry.

    Records counters and histogram samples; ``snapshot()`` returns a
    serializable view. When the module-level ``_metrics_enabled`` flag (set
    by :func:`setup_logging`) is False, record methods are no-ops and the
    snapshot is empty (OBS-4).

    D5: internal errors are swallowed — instrumentation call sites never
    propagate, so a broken registry can never break an agent run.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, int] = {}
        self._histograms: dict[str, list[float]] = {}

    @property
    def enabled(self) -> bool:
        """Whether recording is currently enabled (mirrors config)."""
        return _metrics_enabled

    def increment(self, name: str, amount: int = 1) -> None:
        """Add ``amount`` to the named counter (no-op when disabled)."""
        if not self.enabled:
            return
        try:
            with self._lock:
                self._counters[name] = self._counters.get(name, 0) + amount
        except Exception:  # noqa: BLE001
            pass

    def record_histogram(self, name: str, value: float) -> None:
        """Record a histogram sample (no-op when disabled)."""
        if not self.enabled:
            return
        try:
            with self._lock:
                self._histograms.setdefault(name, []).append(value)
        except Exception:  # noqa: BLE001
            pass

    def reset(self) -> None:
        """Clear all counters and histograms."""
        try:
            with self._lock:
                self._counters.clear()
                self._histograms.clear()
        except Exception:  # noqa: BLE001
            pass

    def snapshot(self) -> dict:
        """Return the current state; ``{}`` when disabled (OBS-4)."""
        try:
            with self._lock:
                if not self.enabled:
                    return {}
                return {
                    "enabled": True,
                    "counters": dict(self._counters),
                    "histograms": {
                        name: self._summarize(values)
                        for name, values in self._histograms.items()
                    },
                    "cost": {"usd": 0.0},  # OBS-7: no cost source in Stage 1
                }
        except Exception:  # noqa: BLE001
            return {}

    @staticmethod
    def _summarize(values: list[float]) -> dict:
        """Aggregate a histogram sample list into count/sum/min/max/avg."""
        if not values:
            return {"count": 0, "sum": 0.0, "min": 0.0, "max": 0.0, "avg": 0.0}
        total = float(sum(values))
        return {
            "count": len(values),
            "sum": total,
            "min": float(min(values)),
            "max": float(max(values)),
            "avg": total / len(values),
        }


_registry: MetricsRegistry | None = None


def get_metrics() -> MetricsRegistry:
    """Return the module-level metrics registry singleton."""
    global _registry
    if _registry is None:
        _registry = MetricsRegistry()
    return _registry
