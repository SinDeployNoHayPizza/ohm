"""OHM Light Theme - Light mode with blue accents."""

from textual.theme import Theme

OHM_LIGHT = Theme(
    name="ohm-light",
    primary="#0891b2",      # Cyan 600 - main accent
    secondary="#7c3aed",    # Violet 600 - secondary actions
    accent="#d97706",       # Amber 600 - highlights
    background="#f8fafc",   # Slate 50 - light background
    surface="#ffffff",      # White - cards/panels
    panel="#e2e8f0",        # Slate 200 - borders
    success="#16a34a",      # Green 600 - positive states
    warning="#d97706",      # Amber 600 - warnings
    error="#dc2626",        # Red 600 - errors
    foreground="#1e293b",   # Slate 800 - primary text
    dark=False,
)
