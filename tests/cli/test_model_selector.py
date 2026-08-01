"""Tests for ModelSelector left/right branch navigation (R8/FU-016).

Left collapses the selected provider's branch (``discard`` from
``_expanded``), right expands it (``add``) — DD-11.
"""

from textual.app import App

from ohm.cli.widgets.model_selector import ModelSelector


def _providers() -> list[dict]:
    """Two realistic provider dicts (shape from ``provider_to_ui_dict``)."""
    return [
        {
            "display_name": "Anthropic",
            "status": "healthy",
            "models": [
                {
                    "name": "claude-sonnet-4-6",
                    "context_window": 200_000,
                    "cost_input": 3.0,
                    "cost_output": 15.0,
                }
            ],
        },
        {
            "display_name": "Gemini",
            "status": "healthy",
            "models": [
                {
                    "name": "gemini-2.5-flash",
                    "context_window": 1_000_000,
                    "cost_input": 0.0,
                    "cost_output": 0.0,
                }
            ],
        },
    ]


def _selector() -> ModelSelector:
    selector = ModelSelector()
    selector.providers = _providers()
    return selector


class TestBranchNavigation:
    """R8: right expands, left collapses the selected provider branch."""

    def test_right_expands_selected_provider(self):
        selector = _selector()
        selector.selected_provider = 1
        assert 1 not in selector._expanded
        selector.action_expand()
        assert 1 in selector._expanded

    def test_left_collapses_selected_provider(self):
        selector = _selector()
        selector.selected_provider = 1
        selector._expanded.add(1)
        selector.action_collapse()
        assert 1 not in selector._expanded

    def test_right_on_expanded_stays_expanded(self):
        selector = _selector()
        selector.selected_provider = 0
        selector._expanded.add(0)
        selector.action_expand()
        assert 0 in selector._expanded

    def test_left_on_collapsed_is_noop(self):
        selector = _selector()
        selector.selected_provider = 1
        selector.action_collapse()
        assert 1 not in selector._expanded

    def test_collapse_only_affects_selected_provider(self):
        selector = _selector()
        selector.selected_provider = 0
        selector._expanded.add(1)
        selector.action_collapse()
        assert 1 in selector._expanded


class _SelectorHarness(App[None]):
    """Minimal app mounting a ModelSelector for key-press tests."""

    def compose(self):
        yield ModelSelector()


class TestBranchNavigationKeys:
    """R8 headless: pressing right/left mutates the expanded set."""

    async def test_right_key_expands(self):
        app = _SelectorHarness()
        async with app.run_test() as pilot:
            selector = app.query_one(ModelSelector)
            selector.providers = _providers()
            selector.add_class("-visible")
            selector.selected_provider = 1
            selector.focus()
            await pilot.press("right")
            assert 1 in selector._expanded

    async def test_left_key_collapses(self):
        app = _SelectorHarness()
        async with app.run_test() as pilot:
            selector = app.query_one(ModelSelector)
            selector.providers = _providers()
            selector.add_class("-visible")
            selector.selected_provider = 1
            selector._expanded.add(1)
            selector.focus()
            await pilot.press("left")
            assert 1 not in selector._expanded
