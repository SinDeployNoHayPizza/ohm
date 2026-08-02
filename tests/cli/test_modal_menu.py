"""Tests for the command palette: live filter (R5), ModalScreen presentation
(R7), selection contract (``dismiss(entry)``), and the modal single-toggle
guard (R6/DD-09)."""

from textual.app import App
from textual.screen import ModalScreen
from textual.widgets import Input, Static

from ohm.cli.app import OhmApp
from ohm.cli.widgets.modal_menu import CommandPalette
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
    """Minimal app that pushes a CommandPalette for headless interaction."""

    def __init__(self, entries: list[PaletteEntry]) -> None:
        super().__init__()
        self.entries = entries

    def compose(self):
        yield Static(id="app-behind")

    def on_mount(self) -> None:
        self.push_screen(CommandPalette(self.entries))


class _SelectionHarness(App[None]):
    """App capturing the palette's ``dismiss(entry)`` result via callback."""

    def __init__(self, entries: list[PaletteEntry]) -> None:
        super().__init__()
        self.entries = entries
        self.selected: PaletteEntry | None = "sentinel"

    def compose(self):
        yield Static(id="app-behind")

    def on_mount(self) -> None:
        self.push_screen(CommandPalette(self.entries), self._on_select)

    def _on_select(self, entry: PaletteEntry | None) -> None:
        self.selected = entry


class TestApplyFilter:
    """R5/DD-10: typing narrows by name/description and resets selection."""

    def _menu(self) -> CommandPalette:
        return CommandPalette(entries=[
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
            pal = app.screen
            await pilot.press("s", "e", "s", "s")

            assert [e.name for e in pal.filtered_commands] == [
                "/sessions", "/session list",
            ]
            assert pal.selected_index == 0
            # The visible list re-renders into the Static widget.
            list_text = pal.query_one("#command-list", expect_type=Static).content
            assert "/sessions" in str(list_text)
            assert "/clear" not in str(list_text)

    async def test_filter_input_focused_when_pushed(self):
        app = _PaletteHarness(entries=[_entry("/run", "Execute a prompt")])
        async with app.run_test() as pilot:
            await pilot.pause()
            focused = app.focused
            assert isinstance(focused, Input)
            assert focused.id == "palette-filter"


class TestModalScreenPresentation:
    """R7/DD-03: palette renders as a ModalScreen dialog — the app behind is
    dimmed (inherited ModalScreen backdrop) and the dialog is centered."""

    async def test_palette_is_modal_screen_with_dim_and_centered_dialog(self):
        app = _PaletteHarness(entries=[
            _entry("/run", "Execute a prompt"),
            _entry("/status", "Show status"),
        ])
        async with app.run_test() as pilot:
            await pilot.pause()
            pal = app.screen
            # Modal contract: ModalScreen subclass with the modal flag set.
            assert isinstance(pal, ModalScreen)
            assert pal._modal is True
            # Dim: the inherited ModalScreen DEFAULT_CSS applies a translucent
            # backdrop so the app behind shows through dimmed.
            alpha = pal.styles.background.a
            assert 0.0 < alpha < 1.0
            # Centered: the dialog box is centered within the screen.
            dlg = pal.query_one("#palette-dialog")
            assert dlg.region.x == (pal.region.width - dlg.region.width) // 2
            assert dlg.region.y == (pal.region.height - dlg.region.height) // 2


class TestSelectionContract:
    """``dismiss(entry)``: Enter returns the chosen entry, Escape cancels."""

    async def test_enter_dismisses_with_selected_entry(self):
        app = _SelectionHarness(entries=[
            _entry("/run", "Execute a prompt", action="run"),
            _entry("/status", "Show status"),
        ])
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            assert app.selected is not None
            assert app.selected.name == "/run"
            assert not isinstance(app.screen, CommandPalette)

    async def test_escape_dismisses_with_none(self):
        app = _SelectionHarness(entries=[_entry("/run", "Execute a prompt")])
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            assert app.selected is None
            assert not isinstance(app.screen, CommandPalette)


class _DummyModal(ModalScreen[None]):
    """A minimal modal screen type for guard tests."""


class TestModalGuard:
    """R6/DD-09: repeated hotkeys never push a second modal."""

    @staticmethod
    def _push_for_test(app: OhmApp, screen: ModalScreen) -> None:
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

    async def test_ctrl_k_toggles_palette(self):
        """R6: Ctrl+K opens the palette; a repeated Ctrl+K pops it (no stack)."""
        app = OhmApp()
        async with app.run_test() as pilot:
            await pilot.press("ctrl+k")
            await pilot.pause()
            assert isinstance(app.screen, CommandPalette)
            assert len(app.screen_stack) == 2
            await pilot.press("ctrl+k")
            await pilot.pause()
            assert not isinstance(app.screen, CommandPalette)
            assert len(app.screen_stack) == 1
