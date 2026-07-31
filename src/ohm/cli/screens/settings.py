"""OHM Modal Screen - Settings and configuration."""

from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Label, Button
from textual.binding import Binding

from ohm.core.config import get_config
from ohm.core.provider import PROVIDER_CATALOG


class SettingsModal(ModalScreen[None]):
    """Settings modal screen."""

    CSS = """
    SettingsModal {
        align: center middle;
    }
    #settings-dialog {
        width: 70;
        height: 30;
        background: $surface;
        border: thick $primary;
        padding: 2 4;
    }
    #settings-title {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
        text-style: bold;
    }
    .settings-section {
        margin-bottom: 1;
    }
    .settings-label {
        text-style: bold;
        width: 15;
    }
    .settings-value {
        width: 1fr;
    }
    Button {
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the settings dialog."""
        cfg = get_config()
        catalog = PROVIDER_CATALOG.get(cfg.provider)
        provider_label = catalog.display_name if catalog else cfg.provider
        model_label = cfg.model
        if catalog:
            for model in catalog.models:
                if model.id == cfg.model:
                    model_label = model.name
                    break
        sandbox_label = "enabled" if cfg.sandbox else "disabled"

        with Vertical(id="settings-dialog"):
            yield Static("⚙️  Settings", id="settings-title")

            with Vertical(classes="settings-section"):
                yield Label("Provider:", classes="settings-label")
                yield Label(provider_label, classes="settings-value")

            with Vertical(classes="settings-section"):
                yield Label("Model:", classes="settings-label")
                yield Label(model_label, classes="settings-value")

            with Vertical(classes="settings-section"):
                yield Label("Sandbox:", classes="settings-label")
                yield Label(sandbox_label, classes="settings-value")

            with Horizontal():
                yield Button("Close", variant="primary", id="close-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "close-btn":
            self.dismiss()

    def action_cancel(self) -> None:
        """Cancel and close."""
        self.dismiss()
