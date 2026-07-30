"""Tests for CommandInput widget."""

from ohm.cli.widgets.input import CommandInput


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
