"""ohm session - Manage chat sessions (save, load, list, delete)."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
from datetime import datetime
from pathlib import Path


def register_args(parser: argparse._ActionsContainer) -> None:
    """Add arguments for the ``session`` subcommand."""
    sub = parser.add_subparsers(dest="action", help="Session action")

    # list
    list_p = sub.add_parser("list", help="List saved sessions")
    list_p.add_argument(
        "--limit", "-n", type=int, default=10, help="Max sessions to show"
    )

    # show
    show_p = sub.add_parser("show", help="Show session details")
    show_p.add_argument("session_id", help="Session ID to show")

    # delete
    del_p = sub.add_parser("delete", help="Delete a session")
    del_p.add_argument("session_id", help="Session ID to delete")
    del_p.add_argument(
        "--yes", "-y", action="store_true", default=False,
        help="Skip confirmation"
    )

    # clear
    clear_p = sub.add_parser("clear", help="Delete all sessions")
    clear_p.add_argument(
        "--yes", "-y", action="store_true", default=False,
        help="Skip confirmation"
    )

    # continue
    cont_p = sub.add_parser("continue", help="Resume the last session")
    cont_p.add_argument(
        "--fresh", "-f", action="store_true", default=False,
        help="Start fresh even if a saved session exists"
    )


def register(registry) -> None:
    """Register the ``session`` subcommand with the CLI registry."""
    registry.register_subcommand(
        name="session",
        help_text="Manage chat sessions (list, show, delete, clear)",
        handler=handler,
        args_setup=register_args,
    )


def _get_sessions_dir(session_dir: Path | None = None) -> Path:
    """Get the sessions directory path."""
    if session_dir is not None:
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir
    from ohm.core.config import SESSIONS_DIR
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    return SESSIONS_DIR


def _list_session_files(session_dir: Path | None = None) -> list[Path]:
    """List all session JSON files, sorted by modification time (newest first)."""
    sessions_dir = _get_sessions_dir(session_dir)
    files = list(sessions_dir.glob("*.json"))
    # Filter out the special last_session.json
    files = [f for f in files if f.name != "last_session.json"]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def _load_session(path: Path) -> dict:
    """Load a session JSON file."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return {}


def _format_time(iso_str: str | None) -> str:
    """Format ISO timestamp to readable string."""
    if not iso_str:
        return "-"
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return iso_str


# ── Helpers for session persistence (used by app.py, registry.py) ──


def _gen_session_id() -> str:
    """Generate a sortable, unique session ID.

    Format: ``ses_{ISO8601-no-punct}_{4-hex}``
    Example: ``ses_20260729_221530_a1b2``
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = secrets.token_hex(2)
    return f"ses_{ts}_{suffix}"


def _save_session(
    data: dict,
    session_dir: Path | None = None,
) -> None:
    """Save session data to ``{session_id}.json`` and update pointer.

    Args:
        data: Session data dict with at least ``session_id`` key.
        session_dir: Directory to write into (defaults to SESSIONS_DIR).
    """
    if session_dir is None:
        from ohm.core.config import SESSIONS_DIR
        session_dir = SESSIONS_DIR
    session_dir.mkdir(parents=True, exist_ok=True)

    session_id = data.get("session_id") or _gen_session_id()
    data["session_id"] = session_id

    session_file = session_dir / f"{session_id}.json"
    session_file.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    pointer_file = session_dir / "last_session.json"
    pointer_file.write_text(
        json.dumps({"last_session_id": session_id}, indent=2),
        encoding="utf-8",
    )


def _load_last_session(session_dir: Path | None = None) -> dict | None:
    """Load the last saved session via pointer resolution.

    Reads ``last_session.json`` → resolves ``{session_id}.json`` →
    returns its content.  Returns ``None`` when no session exists or
    data is corrupt.
    """
    if session_dir is None:
        from ohm.core.config import SESSIONS_DIR
        session_dir = SESSIONS_DIR

    pointer_file = session_dir / "last_session.json"
    if not pointer_file.exists():
        return None

    try:
        pointer = json.loads(pointer_file.read_text(encoding="utf-8"))
        session_id = pointer.get("last_session_id")
        if not session_id:
            return None
        session_file = session_dir / f"{session_id}.json"
        if not session_file.exists():
            return None
        return json.loads(session_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def handle_continue(args: argparse.Namespace) -> int:
    """Resume the last session via TUI.

    Exit code 1 when no session exists.
    """
    session_data = _load_last_session()
    if not session_data:
        print("[session] No previous session to continue.")
        return 1

    from ohm.cli.app import OhmApp
    app = OhmApp(continue_session=session_data)
    app.run()
    return 0


def handler(args: argparse.Namespace) -> int:
    """Execute the ``session`` command."""
    action = getattr(args, "action", None) or "list"

    if action == "list":
        return _handle_list(args)
    elif action == "show":
        return _handle_show(args)
    elif action == "delete":
        return _handle_delete(args)
    elif action == "clear":
        return _handle_clear(args)
    elif action == "continue":
        return handle_continue(args)
    else:
        return _handle_list(args)


def _handle_list(args: argparse.Namespace) -> int:
    """List saved sessions."""
    files = _list_session_files()
    limit = args.limit

    if not files:
        print("[session] No saved sessions found.")
        print(f"[session] Sessions directory: {_get_sessions_dir()}")
        return 0

    # Table header
    print(f"{'ID':<20} {'Started':<20} {'Theme':<12} {'Messages':<10} {'Size'}")
    print("-" * 80)

    for f in files[:limit]:
        data = _load_session(f)
        session_id = f.stem
        started = _format_time(data.get("started_at"))
        theme = data.get("theme", "-")
        messages = len(data.get("messages", []))
        size_kb = f.stat().st_size / 1024

        print(f"{session_id:<20} {started:<20} {theme:<12} {messages:<10} {size_kb:.1f}KB")

    if len(files) > limit:
        print(f"\n... and {len(files) - limit} more sessions")

    print(f"\nTotal: {len(files)} session(s)")
    return 0


def _handle_show(args: argparse.Namespace) -> int:
    """Show details of a specific session."""
    sessions_dir = _get_sessions_dir()
    session_file = sessions_dir / f"{args.session_id}.json"

    if not session_file.exists():
        # Try to find by partial match
        files = _list_session_files()
        matches = [f for f in files if args.session_id in f.stem]
        if len(matches) == 1:
            session_file = matches[0]
        elif len(matches) > 1:
            print(f"[session] Multiple matches for '{args.session_id}':")
            for f in matches:
                print(f"  - {f.stem}")
            return 2
        else:
            print(f"[session] Session not found: {args.session_id}")
            return 2

    data = _load_session(session_file)

    print(f"Session: {session_file.stem}")
    print(f"Started: {_format_time(data.get('started_at'))}")
    print(f"Ended:   {_format_time(data.get('ended_at'))}")
    print(f"Theme:   {data.get('theme', '-')}")
    print(f"File:    {session_file}")

    messages = data.get("messages", [])
    print(f"Messages: {len(messages)}")

    if messages:
        print("\nMessages:")
        for msg in messages:
            role = msg.get("role", "?")
            content = msg.get("content", "")
            # Truncate long messages
            if len(content) > 80:
                content = content[:77] + "..."
            print(f"  [{role}] {content}")

    return 0


def _handle_delete(args: argparse.Namespace) -> int:
    """Delete a specific session."""
    sessions_dir = _get_sessions_dir()
    session_file = sessions_dir / f"{args.session_id}.json"

    if not session_file.exists():
        print(f"[session] Session not found: {args.session_id}")
        return 2

    if not args.yes:
        data = _load_session(session_file)
        started = _format_time(data.get("started_at"))
        print(f"Delete session '{args.session_id}' (started: {started})?")
        confirm = input("Type 'yes' to confirm: ").strip().lower()
        if confirm != "yes":
            print("[session] Cancelled.")
            return 0

    session_file.unlink()
    print(f"[session] Deleted: {args.session_id}")
    return 0


def _handle_clear(args: argparse.Namespace) -> int:
    """Delete all sessions."""
    files = _list_session_files()

    if not files:
        print("[session] No sessions to delete.")
        return 0

    if not args.yes:
        print(f"Delete ALL {len(files)} session(s)?")
        confirm = input("Type 'yes' to confirm: ").strip().lower()
        if confirm != "yes":
            print("[session] Cancelled.")
            return 0

    for f in files:
        f.unlink()
    print(f"[session] Deleted {len(files)} session(s)")
    return 0
