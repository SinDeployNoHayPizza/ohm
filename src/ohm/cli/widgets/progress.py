"""OHM Progress Widget - Context usage visualization."""

from textual.widget import Widget
from textual.reactive import reactive
from textual.app import RenderResult


class ContextProgress(Widget):
    """Visual progress bar for context usage."""

    DEFAULT_CSS = """
    ContextProgress {
        height: 3;
        width: 100%;
        padding: 0 2;
    }
    """

    tokens_used: reactive[int] = reactive(0)
    context_window: reactive[int] = reactive(200_000)

    def update(self, tokens_used: int, context_window: int) -> None:
        """Update the progress bar with real token usage data."""
        self.tokens_used = tokens_used
        self.context_window = context_window

    def render(self) -> RenderResult:
        """Render the progress bar."""
        width = 30
        pct = (self.tokens_used / self.context_window * 100) if self.context_window > 0 else 0.0
        filled = int(width * pct / 100)
        empty = width - filled

        # Color based on usage
        if pct > 80:
            color = "bold red"
            status = "HIGH"
        elif pct > 60:
            color = "bold yellow"
            status = "MODERATE"
        else:
            color = "bold green"
            status = "OK"

        bar = f"[{color}]{'█' * filled}[/][dim]{'░' * empty}[/]"

        return f"""[bold]Context[/] {bar} [bold]{pct:.1f}%[/]
[dim]{self.tokens_used:,} / {self.context_window:,} tokens │ {status}[/]"""
