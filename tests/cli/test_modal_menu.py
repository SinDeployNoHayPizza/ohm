"""Tests for the command palette filter (R5), ModalMenu behavior, and the
modal single-toggle guard (R6)."""

from textual.app import App
from textual.screen import Screen
from textual.widgets import Input, Static

from ohm.cli.app import OhmApp
from ohm.cli.widgets.modal_menu import ModalMenu
from ohm.core.commands import CommandKind, PaletteEntry


def _entry(name: str, description: str = "desc", *, action: str | None = None) -> PaletteEntry:
    return PaletteEntry(
        name=name,
        description=description,
        hotkey=None,
        action=action,
        payload=None,
        kind=CommandKind.DISPLAY_ONLY,
    )


class _PaletteHarness(App[None]):
    """Minimal app hosting a visible ModalMenu for headless typing."""

    def __init__(self, entries: list[PaletteEntry]) -> None:
        super().__init__()
        self.entries = entries

    def compose(self):
        yield ModalMenu(id="menu", entries=self.entries)


class TestApplyFilter:
    """R5/DD-10: typing narrows by name/description and resets selection."""

    def _menu(self) -> ModalMenu:
        return ModalMenu(entries=[
            _entry("/sessions", "Browse saved sessions"),
            _entry("/session list", "Browse saved sessions"),
            _entry("/clear", "Clear chat history"),
            _entry("/theme", "Change theme"),
        ])

    def test_empty_query_keeps_all_entries(self):
        menu = self._menu()
        menu._apply_filter("")
        assert [e.name for e in menu.filtered_commands] == [
            "/sessions", "/session list", "/clear", "/theme",
        ]
        assert menu.selected_index == 0

    def test_filter_narrows_by_name(self):
        menu = self._menu()
        menu._apply_filter("sess")
        assert [e.name for e in menu.filtered_commands] == [
            "/sessions", "/session list",
        ]
        assert menu.selected_index == 0

    def test_filter_narrows_by_description(self):
        menu = self._menu()
        menu._apply_filter("chat")
        assert [e.name for e in menu.filtered_commands] == ["/clear"]
        assert menu.selected_index == 0

    def test_filter_resets_index_to_first_entry(self):
        menu = self._menu()
        menu.selected_index = 2
        menu._apply_filter("clear")
        assert menu.selected_index == 0

    def test_no_matches_leaves_empty_list(self):
        menu = self._menu()
        menu._apply_filter("zzz")
        assert menu.filtered_commands == []
        assert menu.selected_index == 0

    def test_filter_query_is_case_insensitive(self):
        menu = self._menu()
        menu._apply_filter("SESS")
        assert [e.name for e in menu.filtered_commands] == [
            "/sessions", "/session list",
        ]


class TestFilterInput:
    """R5 scenario: typing in the filter Input narrows live; first is selected."""

    async def test_typing_sess_narrows_and_selects_first(self):
        app = _PaletteHarness(entries=[
            _entry("/sessions", "Browse saved sessions"),
            _entry("/session list", "Browse saved sessions"),
            _entry("/clear", "Clear chat history"),
            _entry("/theme", "Change theme"),
        ])
        async with app.run_test() as pilot:
            menu = app.query_one("#menu", expect_type=ModalMenu)
            menu.show()
            await pilot.press("s", "e", "s", "s")

            assert [e.name for e in menu.filtered_commands] == [
                "/sessions", "/session list",
            ]
            assert menu.selected_index == 0
            # The visible list re-renders into the Static widget.
            list_text = menu.query_one("#command-list", expect_type=Static).content
            assert "/sessions" in str(list_text)
            assert "/clear" not in str(list_text)

    async def test_filter_input_focused_when_shown(self):
        app = _PaletteHarness(entries=[_entry("/run", "Execute a prompt")])
        async with app.run_test() as pilot:
            menu = app.query_one("#menu", expect_type=ModalMenu)
            menu.show()
            await pilot.pause()
            await pilot.pause()
            focused = app.focused
            assert isinstance(focused, Input)
            assert focused.id == "palette-filter"


class _DummyModal(Screen[None]):
    """A minimal modal screen type for guard tests."""


class TestModalGuard:
    """R6/DD-09: repeated hotkeys never push a second modal."""

    @staticmethod
    def _push_for_test(app: OhmApp, screen: Screen) -> None:
        """Push a screen onto the live stack without running the app.

        ``App.screen_stack`` returns a snapshot copy, so mutate the
        backing list directly to simulate an open modal.
        """
        app._screen_stacks[app._current_mode].append(screen)

    def test_is_open_reads_screen_stack(self):
        app = OhmApp()
        assert app._is_open(_DummyModal) is False
        self._push_for_test(app, _DummyModal())
        assert app._is_open(_DummyModal) is True

    def test_f3_does_not_push_second_browser(self):
        """GIVEN SessionBrowser is top screen WHEN F3 THEN stack unchanged."""
        from ohm.cli.screens.session_browser import SessionBrowser

        app = OhmApp()
        self._push_for_test(app, SessionBrowser())
        before = len(app.screen_stack)
        app.action_session_browser()
        assert len(app.screen_stack) == before

    def test_settings_does_not_push_second_modal(self):
        from ohm.cli.screens.settings import SettingsModal

        app = OhmApp()
        self._push_for_test(app, SettingsModal())
        before = len(app.screen_stack)
        app.action_settings()
        assert len(app.screen_stack) == before

    def test_quit_does_not_push_second_confirm(self):
        from ohm.cli.app import QuitConfirm

        app = OhmApp()
        self._push_for_test(app, QuitConfirm())
        before = len(app.screen_stack)
        app.action_quit_ohm()
        assert len(app.screen_stack) == before
