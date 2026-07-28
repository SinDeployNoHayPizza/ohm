"""OHM Main Screen - Primary chat interface."""

from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.binding import Binding

from ohm.cli.widgets.banner import Banner
from ohm.cli.widgets.chat import ChatArea
from ohm.cli.widgets.input import CommandInput
from ohm.cli.widgets.sidebar import Sidebar
from ohm.cli.widgets.status import StatusBar
from ohm.cli.widgets.progress import ContextProgress
from ohm.cli.widgets.modal_menu import ModalMenu
from ohm.cli.widgets.file_includer import FileIncluder


class MainScreen(Screen):
    """Main chat interface screen."""

    CSS = """
    MainScreen {
        layout: vertical;
    }
    #main-container {
        height: 1fr;
        width: 100%;
    }
    #chat-column {
        width: 1fr;
        height: 100%;
    }
    #chat-area {
        width: 1fr;
        height: 1fr;
    }
    #sidebar {
        width: 35;
        height: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the main screen layout."""
        with Horizontal(id="main-container"):
            with Vertical(id="chat-column"):
                yield ChatArea(id="chat-area")
                yield ContextProgress()
                yield CommandInput()
            yield Sidebar(id="sidebar")
        yield StatusBar()
        yield ModalMenu(id="modal-menu")
        yield FileIncluder(id="file-includer")
