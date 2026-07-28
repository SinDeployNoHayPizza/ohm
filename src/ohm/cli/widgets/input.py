"""OHM Input Widget - Command input with / filter and file inclusion."""

from textual.widget import Widget
from textual.reactive import reactive
from textual.app import RenderResult
from textual.containers import Horizontal
from textual.widgets import Input, Label
from rich.text import Text

from ohm.utils.fake_data import FAKE_COMMANDS


class CommandInput(Widget):
    """Command input with / filter, # file inclusion, and autocomplete."""

    DEFAULT_CSS = """
    CommandInput {
        height: 5;
        width: 100%;
        dock: bottom;
        background: $surface;
        border-top: solid $panel;
        padding: 0 2;
    }
    CommandInput Horizontal {
        height: 100%;
        width: 100%;
        align: left middle;
    }
    CommandInput Input {
        width: 1fr;
        background: $background;
        border: tall $primary;
    }
    CommandInput Label {
        width: 3;
        content-align: left middle;
    }
    """

    placeholder_text: reactive[str] = reactive("Type a command or message...")

    def compose(self):
        """Compose the input area."""
        with Horizontal():
            yield Label("[bold cyan]❯[/]")
            yield Input(
                placeholder=self.placeholder_text,
                id="command-input",
            )

    def get_filtered_commands(self, query: str) -> list[dict]:
        """Filter commands based on query."""
        if not query.startswith("/"):
            return []
        return [
            cmd for cmd in FAKE_COMMANDS
            if cmd["name"].startswith(query)
        ]

    def get_file_preview(self, path: str) -> dict | None:
        """Get file preview for # file inclusion."""
        from ohm.utils.fake_data import FAKE_FILE_CONTENT
        if path in FAKE_FILE_CONTENT:
            return {
                "path": path,
                "content": FAKE_FILE_CONTENT[path],
                "lines": FAKE_FILE_CONTENT[path].count("\n") + 1,
            }
        return None
