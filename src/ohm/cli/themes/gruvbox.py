"""OHM Gruvbox Theme - Retro groove warm colors."""

from textual.theme import Theme

OHM_GRUVBOX = Theme(
    name="ohm-gruvbox",
    primary="#b8bb26",      # Green - main accent
    secondary="#d3869b",    # Purple - secondary actions
    accent="#fe8019",       # Orange - highlights/warnings
    background="#282828",   # bg0 - dark background
    surface="#3c3836",      # bg1 - cards/panels
    panel="#504945",        # bg2 - borders
    success="#b8bb26",      # Green - positive states
    warning="#fabd2f",      # Yellow - warnings
    error="#fb4934",        # Red - errors
    foreground="#ebdbb2",   # fg - primary text
    dark=True,
)


OHM_GRUVBOX_COLORS = {
    "primary": "#b8bb26",
    "secondary": "#d3869b",
    "accent": "#fe8019",
    "background": "#282828",
    "surface": "#3c3836",
    "panel": "#504945",
    "success": "#b8bb26",
    "warning": "#fabd2f",
    "error": "#fb4934",
    "foreground": "#ebdbb2",
    "text_low": "#a89984",
    "cyan": "#8ec07c",
    "purple": "#d3869b",
    "amber": "#fe8019",
    "green": "#b8bb26",
    "red": "#fb4934",
    "blue": "#83a598",
    "magenta": "#d3869b",
}
