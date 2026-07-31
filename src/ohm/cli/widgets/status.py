"""OHM Status Bar Widget - Hotkeys, session ID, and status info."""

import uuid
from textual.widget import Widget
from textual.app import RenderResult

from ohm import __version__


class StatusBar(Widget):
    """Bottom status bar with hotkeys, session ID, model, and system info."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        width: 100%;
        dock: bottom;
        background: $panel;
        color: $text;
        padding: 0 2;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._session_id = uuid.uuid4().hex[:8]

    def render(self) -> RenderResult:
        """Render the status bar."""
        # Current model from app state
        app = self.app
        model_name = getattr(app, "current_model_name", "Claude Sonnet 4")

        key_hints = [
            "[bold]Ctrl+K[/] Cmds",
            "[bold]F2[/] Model",
            "[bold]Ctrl+D[/] Theme",
            "[bold]Ctrl+S[/] Sidebar",
            "[bold]Ctrl+Q[/] Quit",
        ]

        session_info = f"[bold cyan]Session:[/] [dim]{self._session_id}[/]"
        model_info = f"[bold cyan]Model:[/] [dim]{model_name}[/]"
        system_info = f"[dim]v{__version__}[/]"

        return f" {' | '.join(key_hints)}  {session_info}  {model_info}  {system_info}"
