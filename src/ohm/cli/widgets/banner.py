"""OHM Banner Widget - ASCII art logo with version."""

from textual.widget import Widget
from textual.reactive import reactive
from textual.app import RenderResult

from ohm.utils.fake_data import OHM_LOGO_SMALL
from ohm import __version__


class Banner(Widget):
    """ASCII art banner with version info."""

    DEFAULT_CSS = """
    Banner {
        height: 9;
        width: 100%;
        content-align: center middle;
        background: $surface;
        border-bottom: solid $panel;
    }
    """

    def render(self) -> RenderResult:
        """Render the banner with logo and version."""
        version = __version__
        return f"""[bold cyan]{OHM_LOGO_SMALL}[/]
[dim]v{version} | Orchestrator & Harness for Models[/]"""
