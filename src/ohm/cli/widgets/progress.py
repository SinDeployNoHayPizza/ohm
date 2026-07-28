"""OHM Progress Widget - Context usage visualization."""

from textual.widget import Widget
from textual.reactive import reactive
from textual.app import RenderResult
from rich.text import Text

from ohm.utils.fake_data import FAKE_TOKEN_USAGE


class ContextProgress(Widget):
    """Visual progress bar for context usage."""

    DEFAULT_CSS = """
    ContextProgress {
        height: 3;
        width: 100%;
        padding: 0 2;
    }
    """

    percentage: reactive[float] = reactive(0.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        tokens = FAKE_TOKEN_USAGE
        self.percentage = (tokens["total_tokens"] / tokens["max_tokens"]) * 100

    def render(self) -> RenderResult:
        """Render the progress bar."""
        width = 30
        filled = int(width * self.percentage / 100)
        empty = width - filled

        # Color based on usage
        if self.percentage > 80:
            color = "bold red"
            status = "HIGH"
        elif self.percentage > 60:
            color = "bold yellow"
            status = "MODERATE"
        else:
            color = "bold green"
            status = "OK"

        bar = f"[{color}]{'█' * filled}[/][dim]{'░' * empty}[/]"

        tokens = FAKE_TOKEN_USAGE
        return f"""[bold]Context[/] {bar} [bold]{self.percentage:.1f}%[/]
[dim]{tokens['total_tokens']:,} / {tokens['max_tokens']:,} tokens │ {status}[/]"""
