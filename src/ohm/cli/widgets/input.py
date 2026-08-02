"""OHM Input Widget - Command input with / filter and file inclusion."""

from textual.widget import Widget
from textual.reactive import reactive
from textual.containers import Horizontal
from textual.widgets import TextArea, Label, Button
from textual.events import Resize, Key
from textual import on


class _SubmitTextArea(TextArea):
    """TextArea that submits on Enter/Ctrl+M and inserts on Ctrl+J.

    - ``enter``/``ctrl+m`` (aliased by ``KEY_ALIASES``) submit immediately.
    - ``ctrl+j`` (alias ``newline``) inserts a newline at the cursor and
      never submits (R4).
    """

    async def _on_key(self, event: Key) -> None:
        if event.key in ("enter", "ctrl+m") or "enter" in event.aliases:
            event.stop()
            event.prevent_default()
            # self → Horizontal → CommandInput
            if self.parent is not None:
                cmd_input = self.parent.parent
                if hasattr(cmd_input, "action_submit_input"):
                    cmd_input.action_submit_input()  # type: ignore[union-attr]
                    return
        elif event.key == "ctrl+j" or "newline" in event.aliases:
            event.stop()
            event.prevent_default()
            self.insert("\n")
            return
        await super()._on_key(event)


class CommandInput(Widget):
    """Command input with / filter, # file inclusion, and autocomplete.

    Enter submits, Send button also submits.
    """

    # Layout overhead: 1 (container border-top) + 2 (TextArea border tall)
    _BORDER_OVERHEAD = 3

    DEFAULT_CSS = """
    CommandInput {
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
    CommandInput TextArea {
        width: 1fr;
        background: $background;
        border: tall $primary;
    }
    CommandInput Label {
        width: 3;
        content-align: left middle;
    }
    CommandInput #send-btn {
        min-width: 8;
        height: 3;
        margin: 0 0 0 1;
    }
    """

    placeholder_text: reactive[str] = reactive("Type a command or message...")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._max_lines: int = 5

    def compose(self):
        """Compose the input area."""
        with Horizontal():
            yield Label("[bold cyan]❯[/]")
            yield _SubmitTextArea(
                placeholder=self.placeholder_text,
                id="command-input",
                show_line_numbers=False,
                soft_wrap=True,
            )
            yield Button("Send", id="send-btn", variant="primary")

    def _compute_max_lines(self, viewport_height: int | None = None) -> int:
        """Compute max content lines: min(10, 40% of viewport height), never below 1."""
        if viewport_height is None:
            viewport_height = self.app.size.height
        return max(1, min(10, int(0.4 * viewport_height)))

    def _target_height(self, line_count: int) -> int:
        """Total widget height for a given content line count, including borders."""
        return min(max(line_count, 1), self._max_lines) + self._BORDER_OVERHEAD

    def on_mount(self) -> None:
        """Set initial height and max_lines on mount."""
        self._max_lines = self._compute_max_lines()
        self.styles.height = self._target_height(1)

    def on_resize(self, event: Resize) -> None:
        """Recalculate max_lines and re-clamp height on terminal resize."""
        self._max_lines = self._compute_max_lines()
        textarea = self.query_one("#command-input", expect_type=TextArea)
        text = textarea.text
        line_count = len(text.splitlines()) if text else 1
        self.styles.height = self._target_height(line_count)

    @on(TextArea.Changed, "#command-input")
    def _on_textarea_changed(self, event: TextArea.Changed) -> None:
        """Handle text changes to resize widget dynamically."""
        text = event.text_area.text
        line_count = len(text.splitlines()) if text else 1
        target = self._target_height(line_count)
        if self.styles.height != target:
            self.styles.height = target

    @on(Button.Pressed, "#send-btn")
    def _on_send_clicked(self) -> None:
        """Send button clicked."""
        self.action_submit_input()

    def action_submit_input(self) -> None:
        """Submit current input text. Clears the input and fires background worker."""
        textarea = self.query_one("#command-input", expect_type=TextArea)
        text = textarea.text.strip()
        if not text:
            return
        textarea.text = ""
        self.app._handle_input_submit(text)

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
