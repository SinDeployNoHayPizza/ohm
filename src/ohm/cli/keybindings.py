"""OHM Keybindings - Global hotkey definitions."""

from dataclasses import dataclass


@dataclass
class KeyBinding:
    """A single keybinding definition."""
    key: str
    action: str
    description: str
    category: str
    show_in_bar: bool = True


# Global keybindings for OHM
GLOBAL_BINDINGS = [
    KeyBinding("ctrl+k", "command_palette", "Command Palette", "Navigation"),
    KeyBinding("ctrl+l", "clear_chat", "Clear Chat", "UI"),
    KeyBinding("ctrl+p", "switch_provider", "Switch Provider", "Provider"),
    KeyBinding("ctrl+m", "switch_model", "Switch Model", "Provider"),
    KeyBinding("ctrl+s", "toggle_sidebar", "Toggle Sidebar", "UI"),
    KeyBinding("ctrl+d", "toggle_theme", "Toggle Theme", "UI"),
    KeyBinding("ctrl+q", "quit", "Quit", "System"),
    KeyBinding("ctrl+enter", "send_message", "Send Message", "Chat"),
    KeyBinding("ctrl+t", "run_tests", "Run Tests", "Core"),
    KeyBinding("ctrl+r", "review_code", "Review Code", "Core"),
    KeyBinding("ctrl+f", "fix_file", "Fix File", "Core"),
    KeyBinding("ctrl+h", "command_history", "Command History", "Info"),
    KeyBinding("ctrl+,", "open_settings", "Open Settings", "Settings"),
    KeyBinding("f1", "show_help", "Show Help", "UI"),
    KeyBinding("escape", "close_modals", "Close Modal", "UI"),
    KeyBinding("tab", "autocomplete", "Autocomplete", "Input"),
]


def get_bindings_by_category(category: str) -> list[KeyBinding]:
    """Get keybindings filtered by category."""
    return [b for b in GLOBAL_BINDINGS if b.category == category]


def get_all_categories() -> list[str]:
    """Get all unique categories."""
    return list(set(b.category for b in GLOBAL_BINDINGS))
