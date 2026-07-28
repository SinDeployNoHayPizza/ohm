"""Base class for CLI commands.

Every command module in ``ohm.commands`` should subclass ``BaseCommand``
and call ``register(registry)`` at module level (or be auto-discovered).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


class BaseCommand(ABC):
    """Abstract base for CLI subcommands."""

    name: str
    help_text: str

    @abstractmethod
    def register_args(self, parser: argparse._ActionsContainer) -> None:
        """Add arguments to the subparser."""

    @abstractmethod
    def execute(self, args: argparse.Namespace) -> int:
        """Execute the command. Returns an exit code."""
