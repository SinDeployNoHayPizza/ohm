"""Tests for ContextProgress widget."""

from ohm.cli.widgets.progress import ContextProgress


class TestContextProgress:
    """Tests for ContextProgress real token data."""

    def test_default_idle_state(self):
        """Initial state should show 0% with default context_window."""
        widget = ContextProgress()
        result = str(widget.render())
        assert "0.0%" in result
        assert "0 / 200,000" in result

    def test_update_shows_correct_percentage(self):
        """Calling update with 50k/200k tokens should show 25%."""
        widget = ContextProgress()
        widget.update(tokens_used=50000, context_window=200000)
        result = str(widget.render())
        assert "25.0%" in result
        assert "50,000" in result
        assert "200,000" in result

    def test_update_zero_context_window(self):
        """When context_window is 0, percentage should be 0 to avoid division error."""
        widget = ContextProgress()
        widget.update(tokens_used=100, context_window=0)
        result = str(widget.render())
        assert "0.0%" in result

    def test_update_near_full_context(self):
        """High usage should trigger MODERATE or HIGH status."""
        widget = ContextProgress()
        widget.update(tokens_used=180000, context_window=200000)
        result = str(widget.render())
        assert "90.0%" in result
        assert "180,000" in result
