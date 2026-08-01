"""Shared pytest fixtures and isolation guards.

The ``_isolated_environ`` autouse fixture snapshots ``os.environ`` before
every test and restores it afterwards. ``load_config()`` deliberately pushes
the repo ``.env`` into ``os.environ`` (so provider/API-key lookups work), so
any test that constructs ``OhmApp()``/``get_config()`` with default paths
would otherwise leak those variables into every later test.
"""

from __future__ import annotations

import os
import copy

import pytest


@pytest.fixture(autouse=True)
def _isolated_environ() -> None:
    """Restore ``os.environ`` after each test regardless of outcome."""
    snapshot = copy.deepcopy(dict(os.environ))
    yield
    os.environ.clear()
    os.environ.update(snapshot)
