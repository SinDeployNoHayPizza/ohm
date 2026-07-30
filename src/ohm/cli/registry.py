"""CLI Registry - Composable argument system for OHM subcommands.

Each module/subcommand registers itself via a registry. Adding a new
subcommand = adding one file in ``src/ohm/commands/``.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from typing import Callable

from ohm import __version__
from ohm.utils.fake_data import OHM_LOGO


# ── Exit codes ────────────────────────────────────────────────
EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_USAGE_ERROR = 2
EXIT_RUNTIME_ERROR = 3

_HELP_FLAGS = {"-h", "--help", "-?"}
_VERSION_FLAGS = {"--version", "-V"}


# ── Data structures ───────────────────────────────────────────

@dataclass
class SubcommandEntry:
    """A registered CLI subcommand."""

    name: str
    help_text: str
    handler: Callable[[argparse.Namespace], int]
    args_setup: Callable[[argparse._ActionsContainer], None] = field(
        default_factory=lambda: lambda _: None,
    )


@dataclass
class ParsedResult:
    """Outcome of argument parsing."""

    namespace: argparse.Namespace
    is_help: bool = False
    is_version: bool = False
    unknown_args: list[str] = field(default_factory=list)


# ── Registry ──────────────────────────────────────────────────

class Registry:
    """Composable CLI registry.

    Usage::

        reg = Registry()
        reg.register_subcommand(
            "run", "Run a prompt", handler=my_handler, args_setup=add_run_args,
        )
        result = reg.parse(sys.argv[1:])
        exit_code = reg.dispatch(result)
    """

    def __init__(self) -> None:
        self._subcommands: dict[str, SubcommandEntry] = {}
        self._global_args: list[tuple[list[str], dict]] = []

    # ── Registration ──────────────────────────────────────

    def register_global(
        self,
        *flags: str,
        dest: str | None = None,
        action: str | None = None,
        default: object = None,
        help: str | None = None,
        **kwargs: object,
    ) -> None:
        """Register a global (top-level) argument."""
        self._global_args.append((
            list(flags),
            {
                "dest": dest,
                "action": action,
                "default": default,
                "help": help,
                **kwargs,
            },
        ))

    def register_subcommand(
        self,
        name: str,
        help_text: str,
        handler: Callable[[argparse.Namespace], int],
        args_setup: Callable[[argparse._ActionsContainer], None] | None = None,
    ) -> None:
        """Register a subcommand with its handler and argument setup."""
        entry = SubcommandEntry(
            name=name,
            help_text=help_text,
            handler=handler,
            args_setup=args_setup or (lambda _: None),
        )
        self._subcommands[name] = entry

    # ── Parsing ───────────────────────────────────────────

    def _build_parser(self) -> argparse.ArgumentParser:
        """Build the top-level parser with global args and subparsers.

        All help handling is disabled — we pre-scan argv instead.
        """
        parser = argparse.ArgumentParser(
            prog="ohm",
            description="OHM - Orchestrator & Harness for Models",
            add_help=False,
        )

        # Version flag
        parser.add_argument(
            "--version", "-V",
            action="store_true",
            dest="version",
            default=False,
            help="Show version and exit",
        )

        # Global arguments
        for flags, kwargs in self._global_args:
            clean = {k: v for k, v in kwargs.items() if v is not None}
            parser.add_argument(*flags, **clean)

        # Subparsers — no help added; we handle it ourselves
        subparsers = parser.add_subparsers(dest="subcommand", help="Available commands")

        for name, entry in self._subcommands.items():
            sub = subparsers.add_parser(
                name,
                help=entry.help_text,
                add_help=False,
            )
            sub.add_argument(
                "--version", "-V",
                action="store_true",
                dest="version",
                default=False,
            )
            entry.args_setup(sub)

        return parser

    @staticmethod
    def _prescan(argv: list[str]) -> tuple[bool, bool, list[str]]:
        """Pre-scan argv for help/version flags and strip them.

        Returns:
            (has_help, has_version, cleaned_argv)
        """
        has_help = False
        has_version = False
        cleaned: list[str] = []

        i = 0
        while i < len(argv):
            arg = argv[i]
            if arg in _HELP_FLAGS:
                has_help = True
            elif arg in _VERSION_FLAGS:
                has_version = True
            elif arg.startswith("-") and "=" not in arg and i + 1 < len(argv):
                # Flag with a separate value (e.g. --provider anthropic)
                cleaned.append(arg)
                i += 1
                cleaned.append(argv[i])
            else:
                cleaned.append(arg)
            i += 1

        return has_help, has_version, cleaned

    def parse(self, argv: list[str] | None = None) -> ParsedResult:
        """Parse CLI arguments.

        Pre-scans for ``-h``/``--help``/``-?`` and ``--version``/``-V`` so
        they are never processed by argparse (which would trigger its own
        help/error handling).  Returns a ``ParsedResult`` for dispatch.
        """
        if argv is None:
            argv = sys.argv[1:]

        has_help, has_version, cleaned = self._prescan(argv)

        parser = self._build_parser()

        try:
            # Suppress argparse's own error output — we handle errors in dispatch
            old_stderr = sys.stderr
            sys.stderr = open("NUL", "w", encoding="utf-8")  # noqa: SIM115
            try:
                namespace, unknown = parser.parse_known_args(cleaned)
            finally:
                sys.stderr.close()
                sys.stderr = old_stderr
        except SystemExit:
            # argparse failed on bad args — extract subcommand from argv
            # so dispatch can still route to the right help/handler
            subcmd = cleaned[0] if cleaned and cleaned[0] in self._subcommands else None
            namespace = argparse.Namespace(subcommand=subcmd)
            unknown = cleaned

        return ParsedResult(
            namespace=namespace,
            is_help=has_help,
            is_version=has_version,
            unknown_args=unknown,
        )

    # ── Dispatch ──────────────────────────────────────────

    def dispatch(self, result: ParsedResult) -> int:
        """Execute the parsed command. Returns an exit code."""
        ns = result.namespace

        # Global --version
        if result.is_version and not getattr(ns, "subcommand", None):
            print(f"ohm {__version__}")
            return EXIT_SUCCESS

        # Global --help (no subcommand)
        if result.is_help and not getattr(ns, "subcommand", None):
            self._print_usage()
            return EXIT_SUCCESS

        subcommand = getattr(ns, "subcommand", None)

        if subcommand is None:
            # Check for unrecognized top-level arguments
            if result.unknown_args:
                for arg in result.unknown_args:
                    print(f"ohm: unrecognized argument '{arg}'", file=sys.stderr)
                print("Run 'ohm --help' for usage.", file=sys.stderr)
                return EXIT_USAGE_ERROR
            # No subcommand → launch TUI
            continue_mode = getattr(ns, "continue_", False)
            return self._launch_tui(continue_mode=continue_mode)

        entry = self._subcommands.get(subcommand)
        if entry is None:
            print(f"ohm: unknown command '{subcommand}'", file=sys.stderr)
            print("Run 'ohm --help' for usage.", file=sys.stderr)
            return EXIT_USAGE_ERROR

        # Subcommand --help
        if result.is_help:
            self._print_subcommand_help(subcommand, entry)
            return EXIT_SUCCESS

        # Subcommand --version (allowed on any subcommand)
        if result.is_version:
            print(f"ohm {__version__}")
            return EXIT_SUCCESS

        # Validate: unknown args are usage errors
        if result.unknown_args:
            for arg in result.unknown_args:
                print(f"ohm {subcommand}: unrecognized argument '{arg}'", file=sys.stderr)
            print(f"Run 'ohm {subcommand} --help' for usage.", file=sys.stderr)
            return EXIT_USAGE_ERROR

        # Dispatch to handler
        try:
            return entry.handler(ns)
        except SystemExit as exc:
            return exc.code if isinstance(exc.code, int) else EXIT_GENERAL_ERROR
        except KeyboardInterrupt:
            return EXIT_GENERAL_ERROR
        except Exception as exc:  # noqa: BLE001
            print(f"Error: {exc}", file=sys.stderr)
            return EXIT_RUNTIME_ERROR

    # ── Helpers ───────────────────────────────────────────

    def _launch_tui(self, continue_mode: bool = False) -> int:
        """Launch the TUI application.

        Args:
            continue_mode: When True, load the last saved session and
                pass it to OhmApp so the user can resume.
        """
        try:
            from ohm.cli.app import OhmApp

            session_data = None
            if continue_mode:
                from ohm.commands.session import _load_last_session
                session_data = _load_last_session()
                if not session_data:
                    print("No previous session to continue.")
                    print("Starting a fresh session.")

            app = OhmApp(continue_session=session_data)
            app.run()

            # Exit banner
            print(OHM_LOGO)
            print("Continue last session:  ohm -c")
            print("Session browser:        ohm session list")
            return EXIT_SUCCESS
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to launch TUI: {exc}", file=sys.stderr)
            return EXIT_RUNTIME_ERROR

    def _print_usage(self) -> None:
        """Print top-level usage."""
        lines = [
            f"ohm {__version__} - Orchestrator & Harness for Models",
            "",
            "Usage: ohm [OPTIONS] [COMMAND]",
            "",
            "Options:",
            "  -h, --help, -?    Show this help message and exit",
            "  --version, -V     Show version and exit",
            "  -c, --continue    Resume the last session",
            "",
            "Commands:",
        ]
        for name, entry in self._subcommands.items():
            lines.append(f"  {name:<14} {entry.help_text}")

        lines.extend([
            "",
            "Run 'ohm <command> --help' for help on a specific command.",
            "",
            "If no command is given, OHM launches the interactive TUI.",
        ])
        print("\n".join(lines))

    def _print_subcommand_help(self, name: str, entry: SubcommandEntry) -> None:
        """Print help for a specific subcommand."""
        lines = [
            f"ohm {name} - {entry.help_text}",
            "",
            f"Usage: ohm {name} [OPTIONS] [ARGS]",
            "",
            "Options:",
            "  -h, --help, -?    Show this help message and exit",
            "  --version, -V     Show version and exit",
        ]
        # Collect subcommand-specific args by building a temporary parser
        tmp_parser = argparse.ArgumentParser(prog=f"ohm {name}", add_help=False)
        entry.args_setup(tmp_parser)
        for action in tmp_parser._actions:
            if isinstance(action, argparse._HelpAction):
                continue
            if action.option_strings:
                opts = ", ".join(action.option_strings)
                desc = action.help or ""
                lines.append(f"  {opts:<20} {desc}")

        print("\n".join(lines))
