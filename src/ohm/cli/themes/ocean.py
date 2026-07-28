"""OHM Ocean Theme - Deep ocean blue palette."""

from textual.theme import Theme

OHM_OCEAN = Theme(
    name="ohm-ocean",
    primary="#06b6d4",      # Cyan 500 - main accent
    secondary="#8b5cf6",    # Violet 500 - secondary actions
    accent="#fbbf24",       # Amber 400 - highlights
    background="#0c1222",   # Deep navy - background
    surface="#162032",      # Dark navy - cards/panels
    panel="#1e3a5f",        # Ocean blue - borders
    success="#34d399",      # Emerald 400 - positive states
    warning="#fbbf24",      # Amber 400 - warnings
    error="#f87171",        # Red 400 - errors
    foreground="#e2e8f0",   # Slate 200 - primary text
    dark=True,
)


# Custom ocean palette for Rich
OCEAN_COLORS = {
    "primary": "#06b6d4",
    "secondary": "#8b5cf6",
    "accent": "#fbbf24",
    "background": "#0c1222",
    "surface": "#162032",
    "panel": "#1e3a5f",
    "success": "#34d399",
    "warning": "#fbbf24",
    "error": "#f87171",
    "foreground": "#e2e8f0",
    "text_low": "#7dd3fc",
    "ocean_deep": "#0c1222",
    "ocean_mid": "#162032",
    "ocean_light": "#1e3a5f",
    "ocean_surface": "#2563eb",
}
