"""OHM Command Registry - Command definitions and handling."""

from dataclasses import dataclass
from typing import Callable, Any
from enum import Enum


class CommandCategory(Enum):
    """Command categories."""
    CORE = "core"
    OPS = "ops"
    SETTINGS = "settings"
    UI = "ui"
    INFO = "info"
    SYSTEM = "system"


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
        ))
        self.register(Command(
            name="/loop",
            description="Run task in loop until goal/condition met",
            category=CommandCategory.CORE,
            hotkey="Ctrl+.",
            requires_args=True,
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
