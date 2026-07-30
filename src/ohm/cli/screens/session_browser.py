"""Session Browser — Modal screen for browsing and selecting saved sessions."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Static, Label, Button, ListView, ListItem


def _load_session_list(session_dir: Path | None = None) -> list[dict]:
    """Build a sorted list of session summaries."""
    from ohm.commands.session import _list_session_files, _load_session, _format_time

    files = _list_session_files(session_dir)
    sessions: list[dict] = []
    for f in files:
        data = _load_session(f)
        sessions.append({
            "file": f,
            "session_id": f.stem,
            "started_at": _format_time(data.get("started_at")),
            "messages": len(data.get("messages", [])),
            "theme": data.get("theme", "-"),
            "data": data,
        })
    return sessions


class SessionItem(ListItem):
    """A single session entry in the browser list."""

    def __init__(self, session: dict) -> None:
        self.session = session
        label = (
            f"[bold]{session['session_id']}[/]  "
            f"[dim]{session['started_at']}[/]  "
            f"[bold]{session['messages']}[/] msgs  "
            f"[dim]{session['theme']}[/]"
        )
        super().__init__(Label(label))


class SessionBrowser(ModalScreen[dict | None]):
    """Modal screen listing saved sessions for selection.

    ↑↓ navigate, Enter select, Esc dismiss.
    Returns the selected session data dict or None if dismissed.
    """

    CSS = """
    SessionBrowser {
        align: center middle;
    }
    #session-browser-dialog {
        width: 80;
        height: 24;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    #session-browser-title {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
        text-style: bold;
    }
    #session-list {
        height: 1fr;
        margin-bottom: 1;
        border: solid $panel;
    }
    .browser-hint {
        text-align: center;
        width: 100%;
        color: $text-muted;
    }
    #empty-notice {
        text-align: center;
        width: 100%;
        color: $warning;
        margin-top: 3;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("enter", "select", "Select", show=False),
    ]

    def __init__(self, session_dir: Path | None = None) -> None:
        super().__init__()
        self._session_dir = session_dir
        self._sessions: list[dict] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="session-browser-dialog"):
            yield Static("Saved Sessions", id="session-browser-title")
            self._sessions = _load_session_list(self._session_dir)
            if not self._sessions:
                yield Static(
                    "No saved sessions found.\n\n"
                    "Start a conversation and quit to create a session.",
                    id="empty-notice",
                )
            else:
                items = [SessionItem(s) for s in self._sessions]
                yield ListView(*items, id="session-list")
            yield Static("↑↓ navigate · Enter select · Esc dismiss", classes="browser-hint")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle session selection."""
        item = event.item
        if isinstance(item, SessionItem):
            self.dismiss(item.session.get("data"))

    def action_cancel(self) -> None:
        """Dismiss with no selection."""
        self.dismiss(None)

    def action_select(self) -> None:
        """Select the currently highlighted session."""
        lv = self.query_one(ListView)
        if lv.index is not None and self._sessions:
            idx = lv.index
            if 0 <= idx < len(self._sessions):
                self.dismiss(self._sessions[idx].get("data"))
