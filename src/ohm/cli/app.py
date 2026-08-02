"""OHM TUI Application - Main entry point.

Enterprise-grade orchestrator and harness for LLMs.
Provides a rich terminal UI for interacting with AI agents.
"""

import asyncio
import json
from typing import Any
from pathlib import Path
from datetime import datetime
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static, TextArea
from textual import on

from ohm.cli.widgets.banner import Banner
from ohm.cli.widgets.chat import ChatArea
from ohm.cli.widgets.input import CommandInput
from ohm.cli.widgets.sidebar import Sidebar
from ohm.cli.widgets.status import StatusBar
from ohm.cli.widgets.progress import ContextProgress
from ohm.cli.widgets.file_includer import FileIncluder
from ohm.cli.widgets.model_selector import ModelSelector
from ohm.cli.themes.default import OHM_DEFAULT
from ohm.cli.themes.light import OHM_LIGHT
from ohm.cli.themes.ocean import OHM_OCEAN
from ohm.cli.themes.gruvbox import OHM_GRUVBOX
from ohm.core.agent import Agent, AgentConfig
from ohm.core.commands import (
    CommandKind,
    CommandRegistry,
    PaletteEntry,
    palette_entries,
)
from ohm.core.provider import resolve_context_window
from ohm.core.skills.loader import DEFAULT_SKILL_SEARCH_PATHS, SkillLoader
from ohm.commands.session import _gen_session_id, _save_session, _load_last_session


# ──────────────────────────────────────────────────────────────
# Quit Confirmation Dialog
# ──────────────────────────────────────────────────────────────

class QuitConfirm(ModalScreen[bool]):
    """Quit confirmation dialog."""

    CSS = """
    QuitConfirm {
        align: center middle;
    }
    #quit-dialog {
        width: 50;
        height: auto;
        max-height: 12;
        background: $surface;
        border: thick $primary;
        padding: 2 4;
        align: center middle;
    }
    #quit-title {
        text-align: center;
        width: 100%;
        text-style: bold;
        margin-bottom: 1;
        color: $warning;
    }
    #quit-message {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }
    #quit-buttons {
        width: 100%;
        align: center middle;
        height: auto;
    }
    Button {
        margin: 0 2;
        min-width: 12;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("y", "confirm", "Yes"),
        Binding("n", "cancel", "No"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="quit-dialog"):
            yield Static("Quit OHM?", id="quit-title")
            yield Static("Session will be saved automatically.", id="quit-message")
            with Horizontal(id="quit-buttons"):
                yield Button("Yes, Quit", variant="error", id="quit-yes")
                yield Button("Cancel", variant="primary", id="quit-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit-yes":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


# ──────────────────────────────────────────────────────────────
# OHM Application
# ──────────────────────────────────────────────────────────────

class OhmApp(App[None]):
    """OHM TUI Application."""

    TITLE = "OHM"
    SUB_TITLE = "Orchestration & Harness for Models"

    CSS = """
    Screen {
        layout: vertical;
    }
    #main-container {
        height: 1fr;
        width: 100%;
        layout: horizontal;
    }
    #chat-column {
        width: 1fr;
        height: 100%;
    }
    #chat-area {
        width: 1fr;
        height: 1fr;
    }
    #sidebar {
        width: 35;
        height: 100%;
        display: block;
    }
    #main-container.sidebar-hidden #sidebar {
        display: none;
    }
    #command-dropdown {
        width: 100%;
        height: auto;
        max-height: 12;
        background: $surface;
        border-top: solid $panel;
        padding: 0 2;
        display: none;
        overflow-y: auto;
    }
    #file-includer-wrap {
        dock: bottom;
        height: auto;
        width: 100%;
        align: center middle;
        layer: modal;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit_ohm", "Quit", show=True, priority=True),
        Binding("ctrl+l", "clear", "Clear", show=True, priority=True),
        Binding("ctrl+k", "command_palette", "Commands", show=True, priority=True),
        Binding("ctrl+s", "toggle_sidebar", "Sidebar", show=True, priority=True),
        Binding("ctrl+d", "toggle_theme", "Theme", show=True, priority=True),
        Binding("ctrl+o", "settings", "Settings", show=True, priority=True),
        Binding("f2", "model_selector", "Model", show=True, priority=True),
        Binding("f3", "session_browser", "Sessions", show=True, priority=True),
    ]

    THEMES = {
        "default": OHM_DEFAULT,
        "light": OHM_LIGHT,
        "ocean": OHM_OCEAN,
        "gruvbox": OHM_GRUVBOX,
    }

    def __init__(self, continue_session: dict | None = None) -> None:
        super().__init__()
        from ohm.core.config import get_config
        self.config = get_config()
        self.current_theme_name = self.config.theme or "default"
        self._dropdown_open = False

        # Current provider/model state
        self.current_provider = self.config.provider
        self.current_model = self.config.model
        self.current_model_name = self.config.model
        self._current_context_window = self._resolve_context_window(
            self.current_provider, self.current_model
        )

        for theme in self.THEMES.values():
            self.register_theme(theme)

        theme_map = {
            "default": "ohm-dark",
            "light": "ohm-light",
            "ocean": "ohm-ocean",
            "gruvbox": "ohm-gruvbox",
        }
        self.theme = theme_map.get(self.current_theme_name, "ohm-dark")

        self.agent = Agent(AgentConfig(
            provider=self.config.provider,
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            sandbox=self.config.sandbox,
            tools=self.config.tools,
            system_prompt=self.config.system_prompt or AgentConfig.system_prompt,
            base_url=self.config.base_url,
        ))
        self.commands = CommandRegistry()
        self._skills: dict = {}  # populated once in on_mount (FU-013/R3)

        self._total_tokens_used = 0
        self._continue_session = continue_session

        self._session_data: dict = {
            "session_id": _gen_session_id(),
            "messages": [],
            "started_at": datetime.now().isoformat(),
            "theme": self.current_theme_name,
            "provider": self.current_provider,
            "model": self.current_model,
        }

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        with Horizontal(id="main-container"):
            with Vertical(id="chat-column"):
                yield ChatArea(id="chat-area")
                yield ContextProgress()
                yield Static(id="command-dropdown")
                yield CommandInput()
            yield Sidebar(id="sidebar")
        yield StatusBar()
        with Horizontal(id="file-includer-wrap"):
            yield FileIncluder(id="file-includer")
        with Horizontal(id="model-selector-wrap"):
            yield ModelSelector(id="model-selector")

    def on_mount(self) -> None:
        """Called when app is mounted. Replay continue session or restore."""
        # FU-013/R3: discover skills once — feeds the shared TUI catalog.
        self._skills = SkillLoader.discover_skills(DEFAULT_SKILL_SEARCH_PATHS())

        if self._continue_session:
            msgs = self._continue_session.get("messages", [])
            if msgs:
                chat = self.query_one(ChatArea)
                scroll = chat.query_one("#chat-scroll")
                scroll.remove_children()
                for m in msgs:
                    chat.add_message(m["role"], m["content"])
                # Preserve loaded messages so they aren't lost on save
                self._session_data["messages"] = list(msgs)
                last_ts = self._continue_session.get("ended_at") or self._continue_session.get("started_at", "unknown")
                self.notify(
                    f"Resumed session ({len(msgs)} messages, ended {last_ts})",
                    severity="info",
                    timeout=4,
                )
            # Restore session metadata
            saved_id = self._continue_session.get("session_id")
            if saved_id:
                self._session_data["session_id"] = saved_id
        else:
            saved = _load_last_session()
            if saved:
                self.notify(
                    "Previous session available. Press F3 to browse or use ohm -c to resume.",
                    severity="info",
                    timeout=5,
                )

        # Set initial context window from config model
        try:
            self.query_one(ContextProgress).update(
                tokens_used=0,
                context_window=self._current_context_window,
            )
        except Exception:
            pass

    def on_unmount(self) -> None:
        """Called when app unmounts. Save session for recovery."""
        self._session_data["theme"] = self.current_theme_name
        self._session_data["ended_at"] = datetime.now().isoformat()
        self._session_data["total_tokens"] = self._total_tokens_used
        _save_session(self._session_data)

    # ── Hotkey Actions ──────────────────────────────────────

    def _is_open(self, screen_type: type) -> bool:
        """True when a screen of type ``screen_type`` is on the stack (R6).

        Guards hotkey actions so a repeated press (F3/F2/Ctrl+K/settings/
        quit) never stacks a second modal (DD-09).
        """
        return any(isinstance(screen, screen_type) for screen in self.screen_stack)

    def action_quit_ohm(self) -> None:
        """Show quit confirmation dialog (R6: never push a second one)."""
        if self._is_open(QuitConfirm):
            return

        def on_confirm(confirmed: bool | None) -> None:
            if confirmed:
                self._session_data["theme"] = self.current_theme_name
                self._session_data["ended_at"] = datetime.now().isoformat()
                self._session_data["total_tokens"] = self._total_tokens_used
                _save_session(self._session_data)
                self.exit()
        self.push_screen(QuitConfirm(), on_confirm)

    def action_clear(self) -> None:
        """Clear the chat area."""
        try:
            self.query_one("ChatArea").clear()
        except Exception as exc:
            self.notify(f"Clear failed: {exc}", severity="warning")

    def action_toggle_sidebar(self) -> None:
        """Toggle the sidebar visibility."""
        try:
            container = self.query_one("#main-container")
            container.toggle_class("sidebar-hidden")
        except Exception as exc:
            self.notify(f"Sidebar toggle failed: {exc}", severity="warning")

    def action_toggle_theme(self) -> None:
        """Cycle through themes."""
        themes = list(self.THEMES.keys())
        idx = themes.index(self.current_theme_name)
        self.current_theme_name = themes[(idx + 1) % len(themes)]

        theme_map = {
            "default": "ohm-dark",
            "light": "ohm-light",
            "ocean": "ohm-ocean",
            "gruvbox": "ohm-gruvbox",
        }
        self.theme = theme_map[self.current_theme_name]
        
        # Persist theme selection globally
        try:
            from ohm.core.config import get_config, save_global_config
            cfg = get_config()
            cfg.theme = self.current_theme_name
            save_global_config(cfg)
        except Exception as exc:
            self.notify(f"Failed to save theme: {exc}", severity="warning")

        self.notify(f"Theme: {self.current_theme_name}", severity="info")

    def action_command_palette(self) -> None:
        """Open/close the command palette modal (R6 toggle, DD-09).

        The palette is a pushed ``CommandPalette(ModalScreen)`` (FU-015/R7).
        A repeated Ctrl+K pops it; the dismiss callback dispatches the
        selected entry (DD-12).
        """
        from ohm.cli.widgets.modal_menu import CommandPalette

        if self._is_open(CommandPalette):
            self.pop_screen()
            return

        def on_select(entry: PaletteEntry | None) -> None:
            if entry is not None:
                self._dispatch_command(entry)
            try:
                self.query_one("#command-input").focus()
            except Exception as exc:
                self.notify(f"Focus return failed: {exc}", severity="warning")

        self.push_screen(CommandPalette(self._palette_entries()), on_select)

    def _palette_entries(self) -> list[PaletteEntry]:
        """The shared TUI catalog (R2): palette and dropdown render identical sets."""
        return palette_entries(self.commands.get_all(), self._skills)

    def _dispatch_command(self, entry: PaletteEntry) -> None:
        """Execute a palette/dropdown entry (DD-12).

        REAL entries dispatch their TUI action (e.g. ``session_browser``);
        DISPLAY_ONLY entries post a chat message.  Both the Ctrl+K palette
        and the ``/`` dropdown submit through this single path (R2).
        """
        chat = self.query_one("ChatArea")
        if entry.kind is CommandKind.REAL and entry.action:
            action = getattr(self, f"action_{entry.action}", None)
            if action is not None:
                if entry.payload:
                    action(entry.payload)
                else:
                    action()
                return
        chat.add_message("system", f"Command executed: {entry.name}")

    def action_skill_run(self, skill_name: str) -> None:
        """Inject a discovered skill's instructions into the chat (FU-014).

        Minimal contract: post a chat marker and append the skill body as
        the next user turn so the agent acts on it.
        """
        skill = (self._skills or {}).get(skill_name)
        chat = self.query_one("ChatArea")
        if skill is None:
            chat.add_message("system", f"Skill not found: {skill_name}")
            self.notify(f"Skill not found: {skill_name}", severity="warning", timeout=3)
            return
        chat.add_message("system", f"Skill loaded: {skill_name}")
        body = getattr(skill, "instructions", "")[:4000]
        self._session_data["messages"].append({
            "role": "user",
            "content": f"[Skill: {skill_name}]\n{body}".strip(),
            "timestamp": datetime.now().isoformat(),
        })
        self.notify(f"Skill {skill_name} loaded into chat", severity="info", timeout=3)

    def action_settings(self) -> None:
        """Open settings modal (R6: never push a second one)."""
        from ohm.cli.screens.settings import SettingsModal
        if self._is_open(SettingsModal):
            return
        self.push_screen(SettingsModal())

    def action_session_browser(self) -> None:
        """Open the session browser modal (R6: never push a second one)."""
        from ohm.cli.screens.session_browser import SessionBrowser
        if self._is_open(SessionBrowser):
            return

        def on_select(result: dict | None) -> None:
            if result is not None:
                # Replay and continue from selected session
                chat = self.query_one(ChatArea)
                scroll = chat.query_one("#chat-scroll")
                scroll.remove_children()
                msgs = result.get("messages", [])
                for m in msgs:
                    chat.add_message(m["role"], m["content"])
                # Preserve loaded messages so they aren't lost on save
                self._session_data["messages"] = list(msgs)
                saved_id = result.get("session_id")
                if saved_id:
                    self._session_data["session_id"] = saved_id
                    self._session_data["started_at"] = result.get("started_at", self._session_data["started_at"])
                    self._session_data["theme"] = result.get("theme", self._session_data["theme"])
                self.notify(
                    f"Loaded session ({len(msgs)} messages)",
                    severity="info",
                    timeout=3,
                )
        self.push_screen(SessionBrowser(), on_select)

    def action_session_continue(self) -> None:
        """Resume the last session from within the TUI."""
        from ohm.commands.session import _load_last_session
        data = _load_last_session()
        if not data:
            self.notify("No previous session found.", severity="warning", timeout=3)
            return
        # Replay messages like action_session_browser does
        chat = self.query_one(ChatArea)
        scroll = chat.query_one("#chat-scroll")
        scroll.remove_children()
        msgs = data.get("messages", [])
        for m in msgs:
            chat.add_message(m["role"], m["content"])
        # Preserve loaded messages so they aren't lost on save
        self._session_data["messages"] = list(msgs)
        saved_id = data.get("session_id")
        if saved_id:
            self._session_data["session_id"] = saved_id
            self._session_data["started_at"] = data.get("started_at", self._session_data["started_at"])
            self._session_data["theme"] = data.get("theme", self._session_data["theme"])
        self.notify(
            f"Resumed session ({len(msgs)} messages)",
            severity="info",
            timeout=3,
        )

    def action_session_clear(self) -> None:
        """Delete all sessions with confirmation."""
        from ohm.commands.session import _list_session_files
        import shutil
        from pathlib import Path
        from ohm.core.config import SESSIONS_DIR
        files = _list_session_files()
        if not files:
            self.notify("No sessions to delete.", severity="info", timeout=2)
            return
        count = len(files)
        # Use push_screen with a simple confirmation
        from textual.screen import ModalScreen
        from textual.widgets import Static, Button
        from textual.containers import Horizontal, Vertical

        class ConfirmClear(ModalScreen[bool]):
            CSS = """
            ConfirmClear { align: center middle; }
            #dialog { width: 50; height: auto; padding: 2 4; background: $surface; border: thick $error; }
            #title { text-align: center; text-style: bold; margin-bottom: 1; }
            #buttons { align: center middle; }
            Button { margin: 0 2; min-width: 12; }
            """
            BINDINGS = [Binding("escape", "cancel", "Cancel"), Binding("y", "confirm", "Yes")]

            def compose(self):
                with Vertical(id="dialog"):
                    yield Static(f"Delete ALL {count} session(s)?", id="title")
                    yield Static(f"This removes {count} saved conversation(s) permanently.", id="message")
                    with Horizontal(id="buttons"):
                        yield Button("Yes, Delete All", variant="error", id="confirm-yes")
                        yield Button("Cancel", variant="primary", id="confirm-cancel")

            def on_button_pressed(self, event: Button.Pressed):
                self.dismiss(event.button.id == "confirm-yes")

            def action_confirm(self): self.dismiss(True)
            def action_cancel(self): self.dismiss(False)

        def on_confirm(confirmed: bool | None):
            if confirmed:
                import shutil
                for f in files:
                    f.unlink()
                self.notify(f"Deleted {count} session(s)", severity="info", timeout=3)
        self.push_screen(ConfirmClear(), on_confirm)

    def action_model_selector(self) -> None:
        """Open/close the model selector."""
        selector = self.query_one("#model-selector")
        if selector.is_shown:
            selector.hide()
            try:
                self.query_one("#command-input").focus()
            except Exception as exc:
                self.notify(f"Focus return failed: {exc}", severity="warning")
        else:
            selector.show()

    def _resolve_context_window(self, provider_name: str, model_id: str) -> int:
        """Look up context_window for a given provider/model ID."""
        return resolve_context_window(provider_name, model_id)

    def _on_model_selected(self, provider: dict, model: dict) -> None:
        """Called when a model is selected from the ModelSelector."""
        self.current_provider = provider["name"]
        self.current_model = model["id"]
        self.current_model_name = model["name"]
        self._current_context_window = model.get("context_window", 200000)

        try:
            self.query_one(ContextProgress).update(
                tokens_used=0,
                context_window=self._current_context_window,
            )
        except Exception:
            pass

        try:
            self.query_one("Sidebar").refresh()
            self.query_one("StatusBar").refresh()
        except Exception as exc:
            self.notify(f"Refresh failed: {exc}", severity="warning")

        self.notify(
            f"Model: {provider['display_name']} / {model['name']}",
            severity="info",
        )

    # ── Slash command handling ──────────────────────────────

    @on(TextArea.Changed, "#command-input")
    def on_input_changed(self, event: TextArea.Changed) -> None:
        """Handle input changes for / command filtering."""
        text = event.text_area.text.strip()
        dropdown = self.query_one("#command-dropdown", expect_type=Static)

        if text.startswith("/") and len(text) >= 1:
            query = text[1:].lower()
            matches = [
                entry for entry in self._palette_entries()
                if query in entry.name.lower() or query in entry.description.lower()
            ]
            if matches:
                lines = []
                for entry in matches:
                    hotkey = f" ({entry.hotkey})" if entry.hotkey else ""
                    lines.append(f" [bold cyan]{entry.name}[/] {entry.description}{hotkey}")
                dropdown.update("\n".join(lines))
                dropdown.styles.display = "block"
                self._dropdown_open = True
                return

        dropdown.styles.display = "none"
        self._dropdown_open = False

    def _handle_input_submit(self, text: str) -> None:
        """Handle submitted input text (shared by action and internal calls)."""
        chat = self.query_one("ChatArea")

        if text.startswith("/"):
            full_cmd = text.strip().lower()
            cmd_name = full_cmd.split()[0] if full_cmd else ""
            # Match full command first (/session list), then the prefix word.
            entries = self._palette_entries()
            entry = next(
                (e for e in entries if e.name.lower() == full_cmd),
                next((e for e in entries if e.name.lower() == cmd_name), None),
            )
            if entry:
                self._dispatch_command(entry)
            else:
                chat.add_message("system", f"Unknown command: {cmd_name}")
        elif text:
            chat.add_message("user", text)
            self._session_data["messages"].append({
                "role": "user",
                "content": text,
                "timestamp": datetime.now().isoformat(),
            })
            thinking_widget = chat.start_thinking()
            self.run_worker(
                self._stream_agent_response(text, thinking_widget),
                exclusive=False,
            )

        try:
            dropdown = self.query_one("#command-dropdown")
            dropdown.styles.display = "none"
            self._dropdown_open = False
        except Exception as exc:
            self.notify(f"Dropdown close failed: {exc}", severity="warning")

    async def _stream_agent_response(self, prompt: str, thinking_widget: Any) -> None:
        """Stream response from agent in background worker."""
        import time as _time
        _t0 = _time.monotonic()
        self.log(f"[stream] Starting prompt={prompt[:60]!r}...")

        # Yield to event loop so UI renders user message + thinking widget immediately
        await asyncio.sleep(0)
        chat = self.query_one("ChatArea")
        agent_msg = None
        full_response = ""

        try:
            # Check if agent has API key configured
            provider = self.current_provider
            api_key = self.config.api_key_for(provider)

            if provider != "ollama" and not api_key:
                thinking_widget.is_active = False
                chat.add_message(
                    "system",
                    f"Warning: No API key configured for '{provider}'. "
                    f"Set {provider.upper()}_API_KEY in .env or run 'ohm config' to change provider."
                )
                chat.add_message(
                    "agent",
                    f"I'm ready to help! However, I need an API key for **{provider.capitalize()}** to generate responses. "
                    f"Please add your API key to `.env` or switch to Ollama (local) with `F2`."
                )
                return

            _SKIP_TYPES = {"tool_use", "tool_result", "function_call",
                           "function_result", "error", "warning", "status", "meta"}

            event_count = 0
            has_text = False
            stream_iter = self.agent.stream(prompt).__aiter__()
            while True:
                try:
                    event = await asyncio.wait_for(
                        stream_iter.__anext__(), timeout=120
                    )
                except StopAsyncIteration:
                    break

                event_count += 1

                # ── Plain string → text ───────────────────────────
                if isinstance(event, str):
                    self.log(f"[stream]  #{event_count} str ({len(event)}c): {event[:80]!r}")
                    has_text = True
                    if thinking_widget.is_active:
                        thinking_widget.is_active = False
                    if agent_msg is None:
                        agent_msg = chat.add_message("agent", "")
                    full_response += event
                    agent_msg.update_content(full_response)
                    chat.scroll_to_bottom()
                    continue

                # ── Dict event ─────────────────────────────────────
                if not isinstance(event, dict):
                    self.log(f"[stream]  #{event_count} SKIP type={type(event).__name__}")
                    continue

                etype = event.get("type", "")
                self.log(f"[stream]  #{event_count} dict type={etype!r} keys={list(event.keys())}")

                # Reasoning / thought
                if etype == "reasoning" or "thought" in event:
                    thought = (event.get("thought") or event.get("reasoning")
                               or event.get("content") or event.get("data") or "")
                    if thought:
                        thinking_widget.thought_text += str(thought)
                    continue

                # Skip known non-text types
                if etype in _SKIP_TYPES:
                    continue

                # Check for known text keys (same logic as original working code)
                if any(k in event for k in ("delta", "response", "data", "text", "content")):
                    for key in ("delta", "response", "data", "text", "content"):
                        val = event.get(key)
                        if val is None or val == "":
                            continue
                        # Skip structured data (tool calls, metadata blocks)
                        if isinstance(val, (dict, list)):
                            continue
                        text_chunk = str(val)
                        if text_chunk:
                            self.log(f"[stream]  #{event_count} text via {key!r}: {text_chunk[:80]!r}")
                            has_text = True
                            if thinking_widget.is_active:
                                thinking_widget.is_active = False
                            if agent_msg is None:
                                agent_msg = chat.add_message("agent", "")
                            full_response += text_chunk
                            agent_msg.update_content(full_response)
                            chat.scroll_to_bottom()
                            break
                else:
                    self.log(f"[stream]  #{event_count} UNHANDLED: {event}")

            if thinking_widget.is_active:
                thinking_widget.is_active = False

            _elapsed = _time.monotonic() - _t0
            self.log(f"[stream] DONE {_elapsed:.1f}s | {event_count} events | "
                     f"has_text={has_text} | response_len={len(full_response)}")

            if not has_text and agent_msg is None:
                self.log(f"[stream] WARNING: no text received, showing fallback message")
                chat.add_message("agent", "Response received from agent.")

            # Capture agent response
            if full_response:
                self._session_data["messages"].append({
                    "role": "agent",
                    "content": full_response,
                    "timestamp": datetime.now().isoformat(),
                })

            # Accumulate tokens and update progress bar
            metrics = self.agent.last_metrics
            if metrics:
                self._total_tokens_used += metrics.get("total_tokens", 0)
            else:
                self._total_tokens_used += max(len(full_response) // 2, 0)
            try:
                self.query_one(ContextProgress).update(
                    tokens_used=self._total_tokens_used,
                    context_window=self._current_context_window,
                )
            except Exception:
                pass

        except asyncio.CancelledError:
            thinking_widget.is_active = False
            # Capture whatever partial response we received before cancellation
            if full_response:
                self._session_data["messages"].append({
                    "role": "agent",
                    "content": full_response + "\n\n_[Response interrupted — session ended]_",
                    "timestamp": datetime.now().isoformat(),
                })
                self.log(f"[stream] CANCELLED — captured partial response ({len(full_response)}c)")
            else:
                self.log("[stream] CANCELLED (app shutting down)")
        except asyncio.TimeoutError:
            thinking_widget.is_active = False
            chat.add_message("system", "Agent response timed out after 120s.")
            self.notify("Agent timed out", severity="error")
            self.log("[stream] TIMEOUT after 120s")
        except Exception as exc:
            thinking_widget.is_active = False
            # Capture partial response if any
            if full_response:
                self._session_data["messages"].append({
                    "role": "agent",
                    "content": full_response + f"\n\n_[Error: {exc}]_",
                    "timestamp": datetime.now().isoformat(),
                })
                self.log(f"[stream] ERROR — captured partial response ({len(full_response)}c): {exc}")
            else:
                chat.add_message("system", f"Agent error: {exc}")
                self.notify(f"Agent error: {exc}", severity="error")
                self.log(f"[stream] ERROR: {exc}")


def main(continue_session: dict | None = None) -> None:
    """Run the OHM TUI."""
    app = OhmApp(continue_session=continue_session)
    app.run()


if __name__ == "__main__":
    main()
