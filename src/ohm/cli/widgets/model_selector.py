"""OHM Model Selector Widget - Provider/model picker with keyboard navigation."""

from textual.widget import Widget
from textual.reactive import reactive
from textual.app import RenderResult
from textual.binding import Binding

from ohm.utils.fake_data import FAKE_PROVIDERS


class ModelSelector(Widget):
    """Modal-style provider/model selector with keyboard navigation and scroll."""

    DEFAULT_CSS = """
    ModelSelector {
        width: 70;
        height: 24;
        layer: modal;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
        display: none;
    }
    ModelSelector.-visible {
        display: block;
    }
    ModelSelector:focus {
        border: thick $accent;
    }
    """

    can_focus = True

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("up", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("enter", "select", "Select", show=False),
        Binding("pageup", "page_up", "Page Up", show=False),
        Binding("pagedown", "page_down", "Page Down", show=False),
        Binding("space", "toggle_expand", "Expand", show=False),
    ]

    selected_provider: reactive[int] = reactive(0)
    selected_model: reactive[int] = reactive(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.providers = FAKE_PROVIDERS
        self._expanded: set[int] = {0}
        self._viewport_offset: int = 0

    @property
    def _viewport_height(self) -> int:
        """Dynamic viewport: content_height - header(2) - footer(2) - scroll_indicators(2).

        self.size.height is the content area (excludes border + padding).
        """
        h = self.size.height if self.size.height > 0 else 20
        return max(4, h - 6)

    def _build_lines(self) -> list[str]:
        """Build all renderable lines (header + content + footer)."""
        lines = []
        lines.append("[bold]Select Provider & Model[/]")
        lines.append("[dim]---[/]")

        for pi, provider in enumerate(self.providers):
            is_expanded = pi in self._expanded
            is_sel = pi == self.selected_provider
            arrow = "[bold cyan]>[/]" if is_sel else " "
            expand = "[cyan]+[/]" if is_expanded else "[dim]-[/]"
            status_icon = "[green]*[/]" if provider["status"] == "healthy" else "[red]![/]"

            if is_sel:
                lines.append(f"{arrow} {expand} [bold]{provider['display_name']}[/] {status_icon}")
            else:
                lines.append(f"  {expand} {provider['display_name']} {status_icon}")

            if is_expanded:
                for mi, model in enumerate(provider["models"]):
                    is_msel = pi == self.selected_provider and mi == self.selected_model
                    marker = "[bold cyan]>[/]" if is_msel else " "
                    ctx = f"[dim]{model['context_window'] // 1000}k[/]"
                    cost_in = f"${model['cost_input']:.2f}" if model['cost_input'] > 0 else "[green]free[/]"
                    cost_out = f"${model['cost_output']:.2f}" if model['cost_output'] > 0 else "[green]free[/]"

                    if is_msel:
                        lines.append(f"  {marker} [bold cyan]{model['name']}[/] {ctx} [dim]{cost_in}/{cost_out}[/]")
                    else:
                        lines.append(f"    {model['name']} {ctx} [dim]{cost_in}/{cost_out}[/]")

        return lines

    _HEADER_LINES = 2  # title + separator in _build_lines

    def _get_selected_line(self, content_lines: list[str]) -> int:
        """Find the content line index of the current selection."""
        line_idx = self._HEADER_LINES  # skip header lines
        for pi, provider in enumerate(self.providers):
            if pi == self.selected_provider and not (pi in self._expanded):
                return line_idx
            if pi == self.selected_provider and pi in self._expanded:
                if self.selected_model == 0:
                    return line_idx + 1
                return line_idx + 1 + self.selected_model
            line_idx += 1
            if pi in self._expanded:
                line_idx += len(provider["models"])
        return self._HEADER_LINES

    def render(self) -> RenderResult:
        content = self._build_lines()
        total = len(content)
        vp = self._viewport_height

        sel_line = self._get_selected_line(content)

        # Adjust viewport so selected line is visible
        if sel_line < self._viewport_offset:
            self._viewport_offset = sel_line
        elif sel_line >= self._viewport_offset + vp:
            self._viewport_offset = sel_line - vp + 1

        max_offset = max(0, total - vp)
        self._viewport_offset = max(0, min(self._viewport_offset, max_offset))

        vis_start = self._viewport_offset
        vis_end = vis_start + vp
        visible = content[vis_start:vis_end]

        lines = []
        if vis_start > 0:
            lines.append("[dim]  \u25b2 scroll up[/]")
        else:
            lines.append("")

        lines.extend(visible)

        if vis_end < total:
            lines.append("[dim]  \u25bc scroll down[/]")
        else:
            lines.append("")

        lines.append("[dim]Up/Down Navigate | Enter Select | Space Expand | Esc Close[/]")

        return "\n".join(lines)

    def show(self) -> None:
        """Show the model selector and take focus."""
        self.add_class("-visible")
        self.selected_provider = 0
        self.selected_model = 0
        self._expanded = {0}
        self._viewport_offset = 0
        self.focus()

    def hide(self) -> None:
        """Hide the model selector."""
        self.remove_class("-visible")

    @property
    def is_shown(self) -> bool:
        return "-visible" in self.classes

    # ── Mouse scroll ─────────────────────────────────────────

    def on_mouse_scroll_up(self, event) -> None:
        """Handle mouse scroll up — move selection up."""
        self.action_move_up()

    def on_mouse_scroll_down(self, event) -> None:
        """Handle mouse scroll down — move selection down."""
        self.action_move_down()

    # ── Actions ──────────────────────────────────────────────

    def action_close(self) -> None:
        """Close the selector."""
        self.hide()
        try:
            self.app.query_one("Input").focus()
        except Exception as exc:
            self.app.notify(f"Focus return failed: {exc}", severity="warning")

    def action_move_up(self) -> None:
        """Move selection up."""
        if self.selected_model > 0:
            self.selected_model -= 1
        elif self.selected_provider > 0:
            self.selected_provider -= 1
            prev = self.providers[self.selected_provider]
            self.selected_model = len(prev["models"]) - 1
            self._expanded.add(self.selected_provider)

    def action_move_down(self) -> None:
        """Move selection down."""
        provider = self.providers[self.selected_provider]
        if self.selected_provider in self._expanded:
            if self.selected_model < len(provider["models"]) - 1:
                self.selected_model += 1
            elif self.selected_provider < len(self.providers) - 1:
                self.selected_provider += 1
                self.selected_model = 0
                self._expanded.add(self.selected_provider)
        else:
            self._expanded.add(self.selected_provider)

    def action_page_up(self) -> None:
        for _ in range(3):
            self.action_move_up()

    def action_page_down(self) -> None:
        for _ in range(3):
            self.action_move_down()

    def action_toggle_expand(self) -> None:
        """Toggle expand/collapse of current provider."""
        if self.selected_provider in self._expanded:
            self._expanded.discard(self.selected_provider)
        else:
            self._expanded.add(self.selected_provider)

    def action_select(self) -> None:
        """Select the current model and close."""
        provider = self.providers[self.selected_provider]
        model = provider["models"][self.selected_model]
        self.app._on_model_selected(provider, model)
        self.hide()
        try:
            self.app.query_one("Input").focus()
        except Exception as exc:
            self.app.notify(f"Focus return failed: {exc}", severity="warning")
