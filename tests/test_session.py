"""Tests for session persistence and resume."""

import json
import re
from datetime import datetime
from pathlib import Path

import pytest

from ohm.commands.session import (
    _get_sessions_dir,
    _list_session_files,
    _load_session,
    _load_last_session,
    _save_session,
    _gen_session_id,
)

SESSION_ID_PATTERN = re.compile(r"^ses_\d{8}_\d{6}_[0-9a-f]{4}$")


# ── Session ID format ──────────────────────────────────────────


class TestSessionIdFormat:
    """Task 1: Session IDs match the spec format."""

    def test_default_length_and_pattern(self):
        """Generated ID must match ses_YYYYMMDD_HHMMSS_xxxx pattern."""
        sid = _gen_session_id()
        assert SESSION_ID_PATTERN.match(sid), (
            f"Session ID {sid!r} does not match pattern "
            f"ses_YYYYMMDD_HHMMSS_xxxx"
        )

    def test_unique_ids(self):
        """Consecutive calls produce different IDs (different hex suffix)."""
        ids = {_gen_session_id() for _ in range(10)}
        assert len(ids) == 10, "Generated session IDs must be unique"

    def test_sortable_by_timestamp(self):
        """Earlier call produces an ID that sorts before a later call (when timestamp increments)."""
        import time
        id_a = _gen_session_id()
        time.sleep(1.0)
        id_b = _gen_session_id()
        assert id_a < id_b, "Session IDs should be lexicographically sortable"

    def test_hex_suffix_is_lowercase(self):
        """The 4-hex suffix should be lowercase hex digits."""
        sid = _gen_session_id()
        suffix = sid.split("_")[-1]
        assert suffix == suffix.lower(), f"Suffix {suffix!r} must be lowercase"
        assert all(c in "0123456789abcdef" for c in suffix)


# ── Session save / load round-trip ─────────────────────────────


class TestSessionPersistence:
    """Task 2: Saving and loading session data."""

    def test_save_then_load_roundtrip(self, tmp_path):
        """Save session data, load it back unchanged."""
        session_id = _gen_session_id()
        data = {
            "session_id": session_id,
            "messages": [{"role": "user", "content": "hello"}],
            "started_at": datetime.now().isoformat(),
        }
        _save_session(data, session_dir=tmp_path)
        loaded = _load_session(tmp_path / f"{session_id}.json")
        assert loaded is not None
        assert loaded["session_id"] == session_id
        assert loaded["messages"] == data["messages"]

    def test_pointer_updated_on_save(self, tmp_path):
        """Saving a session updates last_session.json pointer."""
        sid = _gen_session_id()
        data = {"session_id": sid, "messages": []}
        _save_session(data, session_dir=tmp_path)
        pointer = tmp_path / "last_session.json"
        assert pointer.exists()
        assert json.loads(pointer.read_text()) == {"last_session_id": sid}

    def test_pointer_resolution(self, tmp_path):
        """Load last session resolves pointer to full data."""
        sid = _gen_session_id()
        data = {"session_id": sid, "messages": [{"role": "user", "content": "hi"}]}
        _save_session(data, session_dir=tmp_path)
        loaded = _load_last_session(session_dir=tmp_path)
        assert loaded is not None
        assert loaded["session_id"] == sid
        assert loaded["messages"] == data["messages"]

    def test_multiple_saves_both_exist(self, tmp_path):
        """Save two sessions; both files exist, pointer points to latest."""
        sid_a = _gen_session_id()
        sid_b = _gen_session_id()
        _save_session({"session_id": sid_a, "messages": [{"role": "user", "content": "a"}]}, session_dir=tmp_path)
        _save_session({"session_id": sid_b, "messages": [{"role": "user", "content": "b"}]}, session_dir=tmp_path)
        assert (tmp_path / f"{sid_a}.json").exists()
        assert (tmp_path / f"{sid_b}.json").exists()
        pointer = json.loads((tmp_path / "last_session.json").read_text())
        assert pointer["last_session_id"] == sid_b

    def test_plain_text_content_on_disk(self, tmp_path):
        """Content saved as plain text (no Rich renderables)."""
        sid = _gen_session_id()
        messages = [
            {"role": "user", "content": "**bold** and `code`"},
            {"role": "agent", "content": "Response with *italic*"},
        ]
        data = {"session_id": sid, "messages": messages}
        _save_session(data, session_dir=tmp_path)
        raw = (tmp_path / f"{sid}.json").read_text(encoding="utf-8")
        disk = json.loads(raw)
        assert disk["messages"][0]["content"] == "**bold** and `code`"
        assert disk["messages"][1]["content"] == "Response with *italic*"


# ── Edge cases / fallback ──────────────────────────────────────


class TestSessionFallback:
    """Task 2 & 3: Missing, corrupt, or empty scenarios."""

    def test_no_session_returns_none(self, tmp_path):
        """No session files -> load_last_session returns None."""
        assert _load_last_session(session_dir=tmp_path) is None

    def test_corrupt_pointer_returns_none(self, tmp_path):
        """Corrupt last_session.json -> returns None."""
        (tmp_path / "last_session.json").write_text("not json")
        assert _load_last_session(session_dir=tmp_path) is None

    def test_pointer_to_missing_file(self, tmp_path):
        """Pointer references a file that doesn't exist -> returns None."""
        (tmp_path / "last_session.json").write_text(
            json.dumps({"last_session_id": "ses_20260729_000000_dead"})
        )
        assert _load_last_session(session_dir=tmp_path) is None

    def test_empty_pointer_returns_none(self, tmp_path):
        """Pointer with no session_id -> returns None."""
        (tmp_path / "last_session.json").write_text(json.dumps({}))
        assert _load_last_session(session_dir=tmp_path) is None

    def test_corrupt_session_file_returns_empty(self, tmp_path):
        """Corrupt session.json -> load_session returns {}."""
        f = tmp_path / "ses_20260729_000000_beef.json"
        f.write_text("garbage")
        result = _load_session(f)
        assert result == {}

    def test_list_filters_last_session_pointer(self, tmp_path):
        """_list_session_files() does NOT include last_session.json."""
        (tmp_path / "ses_a.json").write_text("{}")
        (tmp_path / "ses_b.json").write_text("{}")
        (tmp_path / "last_session.json").write_text("{}")
        files = _list_session_files(session_dir=tmp_path)
        names = [f.name for f in files]
        assert "last_session.json" not in names
        assert len(names) == 2
