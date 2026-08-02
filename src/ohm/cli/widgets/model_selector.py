"""OHM Model Selector - ModalScreen-based provider/model picker with navigation."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Static

from ohm.core.config import get_config
from ohm.core.provider import get_providers_ui_data


class ModelSelector(ModalScreen[tuple[dict, dict] | None]):
    """Modal-style provider/model selector with keyboard navigation (R7).

    Presentation (R7/DD-03): inherits ``ModalScreen.DEFAULT_CSS`` so the app
    behind is dimmed; the subclass CSS centers the dialog.  The rendered
    provider/model list lives inside the dialog's ``Static`` (``_refresh``).

    Navigation (R8/DD-11): left collapses the selected provider's branch,
    right expands it.  Selecting a model applies it via the app's
    ``_on_model_selected`` and dismisses the screen.
    """

    CSS = """
    ModelSelector {
        align: center middle;
    }
    #model-selector-dialog {
        width: 70;
        height: 20;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    #model-list {
        height: 1fr;
        overflow-y: auto;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("up", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("enter", "select", "Select", show=False),
        Binding("pageup", "page_up", "Page Up", show=False),
        Binding("pagedown", "page_down", "Page Down", show=False),
        Binding("space", "toggle_expand", "Expand", show=False),
        Binding("left", "collapse", "Collapse Branch", show=False),
        Binding("right", "expand", "Expand Branch", show=False),
    ]

    selected_provider: reactive[int] = reactive(0)
    selected_model: reactive[int] = reactive(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        cfg = get_config()
        self.providers = get_providers_ui_data(api_key_for=cfg.api_key_for)
        self._expanded: set[int] = {0}
        self._viewport_offset: int = 0

    def compose(self) -> ComposeResult:
        with Vertical(id="model-selector-dialog"):
            yield Static(id="model-list")

    def on_mount(self) -> None:
        """Render the initial list once the dialog is mounted."""
        self._refresh()

    @property
    def _viewport_height(self) -> int:
        """Dynamic viewport based on the model list widget's height."""
        try:
            static = self.query_one("#model-list", expect_type=Static)
            h = static.size.height
        except Exception:
            h = 20  # not mounted yet (unit tests exercise state directly)
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

    def _render_text(self) -> str:
        """Build the viewport-sliced text for the model list."""
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

    def _refresh(self) -> None:
        """Rebuild the rendered list into the dialog's Static."""
        if not hasattr(self, "providers"):
            return  # not constructed yet (reactive watcher during __init__)
        try:
            self.query_one("#model-list", expect_type=Static).update(self._render_text())
        except Exception:
            pass  # not mounted yet (unit tests exercise state directly)

    def watch_selected_provider(self, old_value: int, new_value: int) -> None:
        """Re-render when the selected provider changes."""
        self._refresh()

    def watch_selected_model(self, old_value: int, new_value: int) -> None:
        """Re-render when the selected model changes."""
        self._refresh()

    # ── Mouse scroll ─────────────────────────────────────────

    def on_mouse_scroll_up(self, event) -> None:
        """Handle mouse scroll up — move selection up."""
        self.action_move_up()

    def on_mouse_scroll_down(self, event) -> None:
        """Handle mouse scroll down — move selection down."""
        self.action_move_down()

    # ── Actions ──────────────────────────────────────────────

    def action_close(self) -> None:
        """Close the selector without choosing."""
        self.dismiss(None)

    def action_move_up(self) -> None:
        """Move selection up."""
        if self.selected_model > 0:
            self.selected_model -= 1
        elif self.selected_provider > 0:
            self.selected_provider -= 1
            prev = self.providers[self.selected_provider]
            self.selected_model = len(prev["models"]) - 1
            self._expanded.add(self.selected_provider)
        self._refresh()

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
        self._refresh()

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
        self._refresh()

    def action_expand(self) -> None:
        """Expand the selected provider's model branch (R8)."""
        self._expanded.add(self.selected_provider)
        self._refresh()

    def action_collapse(self) -> None:
        """Collapse the selected provider's model branch (R8)."""
        self._expanded.discard(self.selected_provider)
        self._refresh()

    def action_select(self) -> None:
        """Select the current model, apply it, and dismiss the screen."""
        provider = self.providers[self.selected_provider]
        model = provider["models"][self.selected_model]
        self.app._on_model_selected(provider, model)
        self.dismiss(None)
