"""Tests for CommandInput widget."""

from textual.app import App
from textual.widgets import TextArea

from ohm.cli.widgets.input import CommandInput


class _InputHarness(App[None]):
    """Minimal app hosting CommandInput with a submit spy."""

    def __init__(self) -> None:
        super().__init__()
        self.submitted: list[str] = []

    def compose(self):
        yield CommandInput(id="input")

    def _handle_input_submit(self, text: str) -> None:
        self.submitted.append(text)


class TestCommandInput:
    """Tests for CommandInput auto-resize."""

    def test_compute_max_lines_formula(self):
        """_compute_max_lines should return min(10, 0.4 * viewport_height), never below 1."""
        widget = CommandInput()
        assert widget._compute_max_lines(100) == min(10, int(0.4 * 100))

    def test_compute_max_lines_tall_terminal(self):
        """For tall terminals, max lines should cap at 10."""
        widget = CommandInput()
        assert widget._compute_max_lines(50) == 10

    def test_compute_max_lines_short_terminal(self):
        """For very short terminals, max lines should be at least 1."""
        widget = CommandInput()
        assert widget._compute_max_lines(1) == 1

    def test_compute_max_lines_medium_terminal(self):
        """For medium terminals, max lines should be 0.4 * height capped at 10."""
        widget = CommandInput()
        assert widget._compute_max_lines(10) == 4

    def test_target_height_includes_border_overhead(self):
        """_target_height should add _BORDER_OVERHEAD to the clamped content line count."""
        widget = CommandInput()
        overhead = CommandInput._BORDER_OVERHEAD
        assert widget._target_height(1) == 1 + overhead
        assert widget._target_height(5) == 5 + overhead
        assert widget._target_height(99) == widget._max_lines + overhead


class TestCtrlJNewline:
    """R4: Ctrl+J inserts a newline at the cursor and never submits."""

    async def test_ctrl_j_inserts_newline_without_submit(self):
        """GIVEN 'line1' typed WHEN Ctrl+J THEN text is 'line1\\n'; no submit."""
        app = _InputHarness()
        async with app.run_test() as pilot:
            textarea = app.query_one("#command-input", expect_type=TextArea)
            textarea.focus()
            await pilot.press(*"line1")
            await pilot.press("ctrl+j")
            assert textarea.text == "line1\n"
            assert app.submitted == []


class TestCtrlMSubmit:
    """R4: Ctrl+M submits exactly like Enter (alias symmetry)."""

    async def test_ctrl_m_submits_like_enter(self):
        """GIVEN non-empty input WHEN Ctrl+M THEN input submits as Enter does."""
        app = _InputHarness()
        async with app.run_test() as pilot:
            textarea = app.query_one("#command-input", expect_type=TextArea)
            textarea.focus()
            textarea.text = "hello"
            await pilot.press("ctrl+m")
            assert app.submitted == ["hello"]

    async def test_enter_still_submits(self):
        """Control: plain Enter keeps submitting through the same path."""
        app = _InputHarness()
        async with app.run_test() as pilot:
            textarea = app.query_one("#command-input", expect_type=TextArea)
            textarea.focus()
            textarea.text = "plain enter"
            await pilot.press("enter")
            assert app.submitted == ["plain enter"]
