"""OHM Command Palette - ModalScreen-based command palette with filtering."""

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Input, Static

from ohm.core.commands import PaletteEntry


class CommandPalette(ModalScreen[PaletteEntry | None]):
    """Modal command palette with filtering (R7/DD-03).

    Renders the shared catalog produced by ``palette_entries`` (R2).  A live
    filter ``Input`` narrows the visible list by name/description and resets
    the selection to the first entry (R5/DD-10).

    Presentation (R7): inherits ``ModalScreen.DEFAULT_CSS`` so the app behind
    is dimmed; the subclass CSS centers the dialog.  Selecting an entry
    dismisses the screen with it via the ``dismiss(entry)`` contract — the
    ``push_screen`` callback in the app dispatches the chosen entry (DD-12).
    """

    CSS = """
    CommandPalette {
        align: center middle;
    }
    #palette-dialog {
        width: 60;
        height: 20;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    CommandPalette Input {
        margin-bottom: 1;
    }
    CommandPalette Static {
        height: 1fr;
        overflow-y: auto;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("up", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("enter", "select", "Select", show=False),
    ]

    selected_index: reactive[int] = reactive(0)
    filter_query: reactive[str] = reactive("")

    def __init__(self, entries: list[PaletteEntry] | None = None, **kwargs):
        super().__init__(**kwargs)
        self._entries: list[PaletteEntry] = list(entries or [])
        self.filtered_commands: list[PaletteEntry] = list(self._entries)
        self._viewport_offset: int = 0

    def compose(self) -> ComposeResult:
        with Vertical(id="palette-dialog"):
            yield Input(placeholder="Filter commands...", id="palette-filter")
            yield Static(id="command-list")

    def on_mount(self) -> None:
        """Focus the filter input once the palette screen is laid out."""
        self.call_after_refresh(self._focus_filter)

    def _focus_filter(self) -> None:
        """Focus the filter Input (runs after the palette becomes visible)."""
        try:
            self.query_one("#palette-filter", expect_type=Input).focus()
        except Exception:
            self.focus()

    @property
    def _viewport_height(self) -> int:
        """Dynamic viewport based on the visible list widget's height."""
        try:
            static = self.query_one("#command-list", expect_type=Static)
            h = static.size.height
        except Exception:
            h = 20  # not mounted yet (unit tests exercise state directly)
        return max(4, h - 6)

    def _render_list(self) -> None:
        """Render the current filtered list into the Static list widget."""
        lines = []
        lines.append("[bold]OHM Commands[/]")
        lines.append("[dim]---[/]")

        for i, cmd in enumerate(self.filtered_commands):
            selected = "[bold cyan]>[/]" if i == self.selected_index else " "
            hotkey = f" [dim]({cmd.hotkey})[/]" if cmd.hotkey else ""
            lines.append(
                f"{selected} [bold cyan]{cmd.name}[/] {cmd.description}{hotkey}"
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

        text = "\n".join(output)
        try:
            self.query_one("#command-list", expect_type=Static).update(text)
        except Exception:
            pass  # not mounted yet (unit tests exercise state directly)

    def _apply_filter(self, query: str) -> None:
        """Narrow the visible list by name/description; reset selection (R5).

        Replaces the old dead ``filter_commands`` — it is wired to the
        live ``Input#palette-filter`` via ``Input.Changed`` (DD-10).
        """
        self.filter_query = query
        q = query.lower()
        if not q:
            self.filtered_commands = list(self._entries)
        else:
            self.filtered_commands = [
                cmd for cmd in self._entries
                if q in cmd.name.lower() or q in cmd.description.lower()
            ]
        self.selected_index = 0
        self._viewport_offset = 0
        self._render_list()

    @on(Input.Changed, "#palette-filter")
    def _on_filter_changed(self, event: Input.Changed) -> None:
        self._apply_filter(event.value)

    @on(Input.Submitted, "#palette-filter")
    def _on_filter_submitted(self, event: Input.Submitted) -> None:
        self.action_select()

    def move_selection(self, delta: int) -> None:
        """Move selection up or down."""
        if self.filtered_commands:
            self.selected_index = (self.selected_index + delta) % len(self.filtered_commands)
        self._render_list()

    def get_selected(self) -> PaletteEntry | None:
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
        """Cancel: dismiss the palette with no selection."""
        self.dismiss(None)

    def action_move_up(self) -> None:
        self.move_selection(-1)

    def action_move_down(self) -> None:
        self.move_selection(1)

    def action_select(self) -> None:
        """Select the current entry: dismiss with it (``dismiss(entry)``).

        The app's ``push_screen`` callback receives the entry and dispatches
        it (DD-12).  Dismissing ``None`` cancels.
        """
        self.dismiss(self.get_selected())
