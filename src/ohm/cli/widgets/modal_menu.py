"""OHM Modal Menu Widget - Command palette with filtering."""

from textual.widget import Widget
from textual.reactive import reactive
from textual.app import RenderResult
from textual.binding import Binding

from ohm.utils.fake_data import FAKE_COMMANDS


class ModalMenu(Widget):
    """Modal command palette with filtering, keyboard navigation, and scroll."""

    DEFAULT_CSS = """
    ModalMenu {
        width: 60;
        height: 25;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
        display: none;
    }
    ModalMenu.-visible {
        display: block;
    }
    ModalMenu:focus {
        border: thick $accent;
    }
    """

    can_focus = True

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("up", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("enter", "select", "Select", show=False),
    ]

    selected_index: reactive[int] = reactive(0)
    filter_query: reactive[str] = reactive("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filtered_commands = FAKE_COMMANDS.copy()
        self._viewport_offset: int = 0

    @property
    def _viewport_height(self) -> int:
        """Dynamic viewport: content_height - header(2) - footer(2) - scroll_indicators(2).

        self.size.height is the content area (excludes border + padding).
        """
        h = self.size.height if self.size.height > 0 else 21
        return max(4, h - 6)

    def render(self) -> RenderResult:
        """Render the command list with scroll."""
        lines = []
        lines.append("[bold]OHM Commands[/]")
        lines.append("[dim]---[/]")

        for i, cmd in enumerate(self.filtered_commands):
            selected = "[bold cyan]>[/]" if i == self.selected_index else " "
            hotkey = f" [dim]({cmd['hotkey']})[/]" if cmd.get("hotkey") else ""
            lines.append(
                f"{selected} [bold cyan]{cmd['name']}[/] {cmd['description']}{hotkey}"
            )

        total = len(lines)
        vp = self._viewport_height

        # Adjust viewport
        sel_line = self.selected_index + 2  # +2 for header lines
        if sel_line < self._viewport_offset:
            self._viewport_offset = sel_line
        elif sel_line >= self._viewport_offset + vp:
            self._viewport_offset = sel_line - vp + 1

        max_offset = max(0, total - vp)
        self._viewport_offset = max(0, min(self._viewport_offset, max_offset))

        vis_start = self._viewport_offset
        vis_end = vis_start + vp
        visible = lines[vis_start:vis_end]

        output = []
        if vis_start > 0:
            output.append("[dim]  \u25b2 scroll up[/]")
        else:
            output.append("")

        output.extend(visible)

        if vis_end < total:
            output.append("[dim]  \u25bc scroll down[/]")
        else:
            output.append("")

        output.append("[dim]Up/Down Navigate | Enter Select | Esc Close[/]")

        return "\n".join(output)

    def show(self) -> None:
        """Show the modal menu."""
        self.add_class("-visible")
        self.selected_index = 0
        self._viewport_offset = 0
        self.filtered_commands = FAKE_COMMANDS.copy()
        self.focus()

    def hide(self) -> None:
        """Hide the modal menu."""
        self.remove_class("-visible")

    @property
    def is_shown(self) -> bool:
        return "-visible" in self.classes

    def filter_commands(self, query: str) -> None:
        """Filter commands based on query."""
        self.filter_query = query
        if not query:
            self.filtered_commands = FAKE_COMMANDS.copy()
        else:
            self.filtered_commands = [
                cmd for cmd in FAKE_COMMANDS
                if query.lower() in cmd["name"].lower()
                or query.lower() in cmd["description"].lower()
            ]
        self.selected_index = 0
        self._viewport_offset = 0

    def move_selection(self, delta: int) -> None:
        """Move selection up or down."""
        if self.filtered_commands:
            self.selected_index = (self.selected_index + delta) % len(self.filtered_commands)

    def get_selected(self) -> dict | None:
        """Get the currently selected command."""
        if self.filtered_commands:
            return self.filtered_commands[self.selected_index]
        return None

    # ── Mouse scroll ─────────────────────────────────────────

    def on_mouse_scroll_up(self, event) -> None:
        self.move_selection(-1)

    def on_mouse_scroll_down(self, event) -> None:
        self.move_selection(1)

    # ── Actions ──────────────────────────────────────────────

    def action_close(self) -> None:
        self.hide()
        try:
            self.app.query_one("#command-input").focus()
        except Exception as exc:
            self.app.notify(f"Focus return failed: {exc}", severity="warning")

    def action_move_up(self) -> None:
        self.move_selection(-1)

    def action_move_down(self) -> None:
        self.move_selection(1)

    def action_select(self) -> None:
        cmd = self.get_selected()
        self.hide()
        try:
            self.app.query_one("#command-input").focus()
        except Exception as exc:
            self.app.notify(f"Focus return failed: {exc}", severity="warning")
        if cmd:
            key = cmd.get("key")
            if key:
                # Dispatch to a named action on the app
                action_name = f"action_{key}"
                action = getattr(self.app, action_name, None)
                if action:
                    action()
                    return
            self.app.notify(f"Command: {cmd['name']}", severity="info")
