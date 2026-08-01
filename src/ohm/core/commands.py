"""OHM Command Registry - Command definitions and handling."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Mapping, Sequence


class CommandCategory(Enum):
    """Command categories."""
    CORE = "core"
    OPS = "ops"
    SETTINGS = "settings"
    UI = "ui"
    INFO = "info"
    SYSTEM = "system"


class CommandKind(Enum):
    """How a command behaves inside the TUI (R1 classification).

    - ``REAL``: wired to a live TUI action — dispatch runs ``action_{action}``.
    - ``DISPLAY_ONLY``: rendered in the catalog; executing shows a chat message.
    - ``TUI_IRRELEVANT``: CLI-only surface (e.g. ``doctor``) — never rendered.
    """

    REAL = "real"
    DISPLAY_ONLY = "display_only"
    TUI_IRRELEVANT = "tui_irrelevant"


@dataclass
class Command:
    """A registered command."""
    name: str
    description: str
    category: CommandCategory
    hotkey: str | None = None
    handler: Callable[..., Any] | None = None
    requires_args: bool = False
    hidden: bool = False
    kind: CommandKind = CommandKind.DISPLAY_ONLY
    action: str | None = None          # TUI action name, e.g. "session_browser"
    payload: str | None = None         # dynamic argument, e.g. skill name
    cli_equivalent: str | None = None  # matching CLI subcommand name (R1)


@dataclass(frozen=True)
class PaletteEntry:
    """A single renderable entry in the Ctrl+K palette / ``/`` dropdown."""

    name: str
    description: str
    hotkey: str | None
    action: str | None
    payload: str | None
    kind: CommandKind


class CommandRegistry:
    """Registry for OHM commands."""

    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register default OHM commands."""
        self.register(Command(
            name="/run",
            description="Execute a prompt",
            category=CommandCategory.CORE,
            hotkey="Ctrl+Enter",
            cli_equivalent="run",
        ))
        self.register(Command(
            name="/fix",
            description="Fix a specific file or issue",
            category=CommandCategory.CORE,
            hotkey="Ctrl+F",
            requires_args=True,
        ))
        self.register(Command(
            name="/test",
            description="Run test suite",
            category=CommandCategory.CORE,
            hotkey="Ctrl+T",
            cli_equivalent="test",
        ))
        self.register(Command(
            name="/review",
            description="Review code changes",
            category=CommandCategory.CORE,
            hotkey="Ctrl+R",
        ))
        self.register(Command(
            name="/goal",
            description="Set autonomous goal with subtask breakdown",
            category=CommandCategory.CORE,
            hotkey="Ctrl+G",
            requires_args=True,
            cli_equivalent="goal",
        ))
        self.register(Command(
            name="/loop",
            description="Run task in loop until goal/condition met",
            category=CommandCategory.CORE,
            hotkey="Ctrl+.",
            requires_args=True,
            cli_equivalent="loop",
        ))
        self.register(Command(
            name="/deploy",
            description="Deploy to staging/production",
            category=CommandCategory.OPS,
        ))
        self.register(Command(
            name="/config",
            description="Open configuration",
            category=CommandCategory.SETTINGS,
            hotkey="Ctrl+,",
            cli_equivalent="config",
        ))
        self.register(Command(
            name="/model",
            description="Switch model",
            category=CommandCategory.SETTINGS,
            hotkey="Ctrl+M",
        ))
        self.register(Command(
            name="/provider",
            description="Switch provider",
            category=CommandCategory.SETTINGS,
            hotkey="Ctrl+P",
        ))
        self.register(Command(
            name="/clear",
            description="Clear chat history",
            category=CommandCategory.UI,
            hotkey="Ctrl+L",
        ))
        self.register(Command(
            name="/help",
            description="Show help",
            category=CommandCategory.UI,
            hotkey="F1",
        ))
        self.register(Command(
            name="/status",
            description="Show system status",
            category=CommandCategory.INFO,
            cli_equivalent="status",
        ))
        self.register(Command(
            name="/history",
            description="Show command history",
            category=CommandCategory.INFO,
            hotkey="Ctrl+H",
        ))
        self.register(Command(
            name="/theme",
            description="Change theme",
            category=CommandCategory.UI,
        ))
        self.register(Command(
            name="/exit",
            description="Exit OHM",
            category=CommandCategory.SYSTEM,
            hotkey="Ctrl+Q",
        ))
        # Real TUI actions (R1 class "real"): session browser + shortcuts.
        # `/session list` shares the browser action per R2; `/sessions` is
        # the short alias for the same surface.
        self.register(Command(
            name="/sessions",
            description="Browse saved sessions",
            category=CommandCategory.CORE,
            hotkey="F3",
            kind=CommandKind.REAL,
            action="session_browser",
            cli_equivalent="session",
        ))
        self.register(Command(
            name="/session list",
            description="Browse saved sessions",
            category=CommandCategory.CORE,
            kind=CommandKind.REAL,
            action="session_browser",
            cli_equivalent="session",
        ))
        self.register(Command(
            name="/session continue",
            description="Resume the last session",
            category=CommandCategory.CORE,
            kind=CommandKind.REAL,
            action="session_continue",
            cli_equivalent="session",
        ))
        self.register(Command(
            name="/session clear",
            description="Delete all saved sessions",
            category=CommandCategory.CORE,
            kind=CommandKind.REAL,
            action="session_clear",
            cli_equivalent="session",
        ))

    def register(self, command: Command) -> None:
        """Register a command."""
        self._commands[command.name] = command

    def get(self, name: str) -> Command | None:
        """Get a command by name."""
        return self._commands.get(name)

    def search(self, query: str) -> list[Command]:
        """Search commands by query."""
        if not query:
            return list(self._commands.values())
        return [
            cmd for cmd in self._commands.values()
            if query.lower() in cmd.name.lower()
            or query.lower() in cmd.description.lower()
        ]

    def get_by_category(self, category: CommandCategory) -> list[Command]:
        """Get commands by category."""
        return [
            cmd for cmd in self._commands.values()
            if cmd.category == category
        ]

    def get_all(self) -> list[Command]:
        """Get all registered commands."""
        return list(self._commands.values())


def palette_entries(
    commands: Sequence[Command],
    skills: Mapping[str, object] | Sequence[object] | None = None,
) -> list[PaletteEntry]:
    """Build the shared TUI catalog for the Ctrl+K palette and ``/`` dropdown.

    Catalog entries keep registration order; skills are appended LAST as
    ``/skill <name>`` entries, sorted by name (DD-04, R3). Pure function —
    the registry is data, this is the view (DD-07).
    """
    entries = [
        PaletteEntry(
            name=cmd.name,
            description=cmd.description,
            hotkey=cmd.hotkey,
            action=cmd.action,
            payload=cmd.payload,
            kind=cmd.kind,
        )
        for cmd in commands
    ]
    if skills is None:
        return entries
    if isinstance(skills, str):  # tolerate a bare skill name
        skills = [skills]
    if isinstance(skills, Mapping):
        skill_names = sorted(skills)
    else:
        skill_names = sorted(getattr(skill, "name", skill) for skill in skills)
    for name in skill_names:
        entries.append(
            PaletteEntry(
                name=f"/skill {name}",
                description=f"Run skill: {name}",
                hotkey=None,
                action="skill_run",
                payload=name,
                kind=CommandKind.REAL,
            )
        )
    return entries


# R1 parity authority: every CLI subcommand (plus the two flag surfaces)
# maps to exactly one TUI class.  Keep this in sync with `register_all`
# (src/ohm/commands/__init__.py) — the parity test asserts the bijection.
CLI_TUI_MAPPING: dict[str, CommandKind] = {
    # real — wired to a live TUI action
    "session": CommandKind.REAL,
    "skills": CommandKind.REAL,
    "skill": CommandKind.REAL,
    # display-only — rendered in the catalog; dispatch shows a chat message
    "config": CommandKind.DISPLAY_ONLY,
    "test": CommandKind.DISPLAY_ONLY,
    "run": CommandKind.DISPLAY_ONLY,
    "status": CommandKind.DISPLAY_ONLY,
    "goal": CommandKind.DISPLAY_ONLY,
    "loop": CommandKind.DISPLAY_ONLY,
    # tui-irrelevant — CLI-only surfaces, never rendered in the TUI
    "doctor": CommandKind.TUI_IRRELEVANT,
    "mcp": CommandKind.TUI_IRRELEVANT,
    "cron": CommandKind.TUI_IRRELEVANT,
    "init": CommandKind.TUI_IRRELEVANT,
    "serve": CommandKind.TUI_IRRELEVANT,
    "plugin": CommandKind.TUI_IRRELEVANT,
    "--version": CommandKind.TUI_IRRELEVANT,
    "-h": CommandKind.TUI_IRRELEVANT,
}
