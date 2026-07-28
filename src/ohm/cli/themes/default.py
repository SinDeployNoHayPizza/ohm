"""OHM Default Theme - Dark mode with teal/cyan accents."""

from textual.theme import Theme

OHM_DEFAULT = Theme(
    name="ohm-dark",
    primary="#00d4aa",      # Teal/cyan - main accent
    secondary="#7c3aed",    # Purple - secondary actions
    accent="#f59e0b",       # Amber - highlights/warnings
    background="#0f172a",   # Slate 900 - deep dark
    surface="#1e293b",      # Slate 800 - cards/panels
    panel="#334155",        # Slate 700 - borders
    success="#22c55e",      # Green - positive states
    warning="#f59e0b",      # Amber - warnings
    error="#ef4444",        # Red - errors
    foreground="#f8fafc",   # Slate 50 - primary text
    dark=True,
)


# ANSI color palette for Rich integration
OHM_COLORS = {
    "primary": "#00d4aa",
    "secondary": "#7c3aed",
    "accent": "#f59e0b",
    "background": "#0f172a",
    "surface": "#1e293b",
    "panel": "#334155",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "foreground": "#f8fafc",
    "text_low": "#94a3b8",
    "cyan": "#00d4aa",
    "purple": "#7c3aed",
    "amber": "#f59e0b",
    "green": "#22c55e",
    "red": "#ef4444",
    "blue": "#3b82f6",
    "magenta": "#ec4899",
}
