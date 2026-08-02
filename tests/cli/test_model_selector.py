"""Tests for ModelSelector: ModalScreen presentation (R7), left/right branch
navigation (R8/FU-016, DD-11), and select-dismiss flow."""

from textual.app import App
from textual.screen import ModalScreen
from textual.widgets import Static

from ohm.cli.widgets.model_selector import ModelSelector


def _providers() -> list[dict]:
    """Two realistic provider dicts (shape from ``provider_to_ui_dict``)."""
    return [
        {
            "name": "anthropic",
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
            "name": "gemini",
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
    """Minimal app pushing a ModelSelector for headless key tests."""

    def compose(self):
        yield Static(id="app-behind")

    def on_mount(self) -> None:
        self.push_screen(ModelSelector())


class TestBranchNavigationKeys:
    """R8 headless: pressing right/left mutates the expanded set."""

    async def test_right_key_expands(self):
        app = _SelectorHarness()
        async with app.run_test() as pilot:
            selector = app.screen
            selector.providers = _providers()
            selector.selected_provider = 1
            selector.focus()
            await pilot.press("right")
            assert 1 in selector._expanded

    async def test_left_key_collapses(self):
        app = _SelectorHarness()
        async with app.run_test() as pilot:
            selector = app.screen
            selector.providers = _providers()
            selector.selected_provider = 1
            selector._expanded.add(1)
            selector.focus()
            await pilot.press("left")
            assert 1 not in selector._expanded


class TestModalScreenPresentation:
    """R7/DD-03: model selector renders as a ModalScreen dialog — the app
    behind is dimmed and the dialog is centered."""

    async def test_selector_is_modal_screen_with_dim_and_centered_dialog(self):
        app = _SelectorHarness()
        async with app.run_test() as pilot:
            await pilot.pause()
            sel = app.screen
            assert isinstance(sel, ModalScreen)
            assert sel._modal is True
            # Dim: inherited ModalScreen DEFAULT_CSS translucent backdrop.
            alpha = sel.styles.background.a
            assert 0.0 < alpha < 1.0
            # Centered: the dialog box is centered within the screen.
            dlg = sel.query_one("#model-selector-dialog")
            assert dlg.region.x == (sel.region.width - dlg.region.width) // 2
            assert dlg.region.y == (sel.region.height - dlg.region.height) // 2


class _SelectingApp(App[None]):
    """App that records the model chosen via ``_on_model_selected``."""

    def __init__(self) -> None:
        super().__init__()
        self.selected: tuple[str, str] | None = None

    def compose(self):
        yield Static(id="app-behind")

    def on_mount(self) -> None:
        self.push_screen(ModelSelector())

    def _on_model_selected(self, provider: dict, model: dict) -> None:
        self.selected = (provider["name"], model["name"])


class TestSelectDismisses:
    """Enter selects the model, applies it, and dismisses the screen."""

    async def test_select_applies_model_and_dismisses(self):
        app = _SelectingApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sel = app.screen
            sel.providers = _providers()
            sel.focus()
            await pilot.press("enter")
            await pilot.pause()
            assert app.selected == ("anthropic", "claude-sonnet-4-6")
            assert not isinstance(app.screen, ModelSelector)
