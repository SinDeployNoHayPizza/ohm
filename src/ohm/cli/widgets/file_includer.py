"""OHM File Includer Widget - # file inclusion with preview."""

from textual.widget import Widget
from textual.reactive import reactive
from textual.app import RenderResult

from ohm.utils.fake_data import FAKE_FILE_TREE, FAKE_FILE_CONTENT


class FileIncluder(Widget):
    """File inclusion widget triggered by # prefix."""

    DEFAULT_CSS = """
    FileIncluder {
        width: 70;
        height: 20;
        background: $surface;
        border: thick $accent;
        padding: 1 2;
        display: none;
    }
    FileIncluder.-visible {
        display: block;
    }
    """

    selected_path: reactive[str] = reactive("")

    def render(self) -> RenderResult:
        """Render the file includer."""
        if not self.selected_path:
            return "[bold]File Includer[/]\n[dim]Type # to include a file[/]"

        content = FAKE_FILE_CONTENT.get(self.selected_path)
        if content:
            all_lines = content.split("\n")
            total = len(all_lines)

            # self.size.height is content area (excludes border + padding)
            h = self.size.height if self.size.height > 0 else 16
            vp = max(4, h - 3)  # header(2) + footer(1)

            visible_lines = all_lines[:vp]
            numbered = "\n".join(
                f"[dim]{i+1:3}[/] {line}" for i, line in enumerate(visible_lines)
            )

            footer = ""
            if total > vp:
                footer = f"\n[dim]... {total - vp} more lines ({total} total)[/]"
            else:
                footer = f"\n[dim]{total} total lines[/]"

            return f"""[bold]{self.selected_path}[/]
[dim]---[/]
{numbered}{footer}"""

        return f"""[bold]{self.selected_path}[/]
[dim]---[/]
[dim]File not found in demo data[/]"""

    def show(self, path: str) -> None:
        """Show the file includer with path."""
        self.selected_path = path
        self.add_class("-visible")

    def hide(self) -> None:
        """Hide the file includer."""
        self.remove_class("-visible")
        self.selected_path = ""

    @property
    def is_shown(self) -> bool:
        return "-visible" in self.classes

    def on_mouse_scroll_up(self, event) -> None:
        """No-op: file includer is read-only preview."""
        pass

    def on_mouse_scroll_down(self, event) -> None:
        """No-op: file includer is read-only preview."""
        pass
