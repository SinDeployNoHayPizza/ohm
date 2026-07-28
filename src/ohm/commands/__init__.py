"""CLI commands package - auto-discovery of all command modules.

Each module in this package should define a ``register(registry)`` function
that registers itself with the CLI registry.  Alternatively, subclasses of
``BaseCommand`` are auto-discovered via ``register_class``.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ohm.cli.registry import Registry


def register_all(registry: Registry) -> None:
    """Auto-discover and register every command module in this package.

    Each module may define either:
      - ``register(registry)`` — called directly, or
      - ``COMMAND`` — a ``BaseCommand`` subclass instance (auto-registered).
    """
    import ohm.commands as pkg

    for _importer, modname, _ispkg in pkgutil.iter_modules(pkg.__path__):
        if modname.startswith("_"):
            continue
        module = importlib.import_module(f"ohm.commands.{modname}")

        if hasattr(module, "register") and callable(module.register):
            module.register(registry)

        if hasattr(module, "COMMAND"):
            cmd = module.COMMAND
            registry.register_subcommand(
                name=cmd.name,
                help_text=cmd.help_text,
                handler=cmd.execute,
                args_setup=cmd.register_args,
            )
