"""OHM Chat Widget - Scrollable chat display area with markdown and thinking status."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Container
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from ohm.utils.fake_data import OHM_LOGO_SMALL
from ohm import __version__


class MessageWidget(Static):
    """Widget to display a single message."""

    DEFAULT_CSS = """
    MessageWidget {
        margin: 1 0;
        padding: 0 1;
        width: 100%;
        height: auto;
    }
    .msg-user {
        border-left: thick $accent;
    }
    .msg-agent {
        border-left: thick $success;
    }
    .msg-system {
        border-left: thick #666;
        color: #888;
    }
    .msg-welcome {
        border: double $primary;
        padding: 1 2;
        margin: 1 2;
        background: $surface;
    }
    """

    def __init__(self, role: str, content: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.role = role
        self.content = content

    def on_mount(self) -> None:
        self.update_content()

    def update_content(self, new_content: str | None = None) -> None:
        """Update content and refresh rendering."""
        if new_content is not None:
            self.content = new_content

        if self.role == "welcome":
            self.add_class("msg-welcome")
            logo = f"[bold cyan]{OHM_LOGO_SMALL}[/]\n"
            version_info = f"[dim]v{__version__} | Orchestration & Harness for Models[/]\n\nType your command or prompt below. Press [bold cyan]F2[/] to change models."
            self.update(logo + version_info)
        elif self.role == "user":
            self.add_class("msg-user")
            self.update(Text.assemble(
                ("> You\n", "bold cyan"),
                f"  {self.content}"
            ))
        elif self.role == "agent":
            self.add_class("msg-agent")
            # Render Markdown for Agent's response
            try:
                self.update(Markdown(self.content))
            except Exception:
                self.update(Text(self.content))
        elif self.role == "system":
            self.add_class("msg-system")
            self.update(Text.assemble(
                ("ℹ ", "dim"),
                (self.content, "dim")
            ))


class ThinkingWidget(Static):
    """Widget to represent the agent's reasoning/thinking steps."""

    DEFAULT_CSS = """
    ThinkingWidget {
        margin: 0 2 1 2;
        padding: 0 1;
        border-left: dashed $warning;
        height: auto;
        width: 100%;
    }
    ThinkingWidget .title {
        color: $warning;
        text-style: bold;
    }
    ThinkingWidget .thought-content {
        color: $text;
        margin-top: 1;
        display: block;
    }
    ThinkingWidget.collapsed .thought-content {
        display: none;
    }
    """

    collapsed = reactive(True)
    thought_text = reactive("")
    is_active = reactive(True)
    duration = reactive(0.0)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.start_time = datetime.now()

    def compose(self) -> ComposeResult:
        yield Static("• Thinking...", classes="title", id="thinking-title")
        yield Static("", classes="thought-content", id="thinking-text")

    def watch_thought_text(self, text: str) -> None:
        """Update thought text when changed."""
        try:
            self.query_one("#thinking-text", Static).update(text)
        except Exception:
            pass

    def watch_is_active(self, active: bool) -> None:
        """Handle state change when finished thinking."""
        if not active:
            delta = (datetime.now() - self.start_time).total_seconds()
            self.duration = delta
            self.collapsed = True
            try:
                title = self.query_one("#thinking-title", Static)
                title.update(f"✔ Thought for {self.duration:.1f}s (Click to expand)")
                title.styles.color = "green"
            except Exception:
                pass

    def watch_collapsed(self, collapsed: bool) -> None:
        """Apply CSS class for collapsibility."""
        if collapsed:
            self.add_class("collapsed")
        else:
            self.remove_class("collapsed")

    def on_click(self) -> None:
        """Toggle expand/collapse on mouse click."""
        if not self.is_active:
            self.collapsed = not self.collapsed


class ChatArea(Widget):
    """Scrollable chat message area managing messages and thinking states."""

    DEFAULT_CSS = """
    ChatArea {
        height: 1fr;
        width: 100%;
        background: $background;
        padding: 1 2;
    }
    #chat-scroll {
        height: 100%;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="chat-scroll") as vs:
            # First message is our nice Logo
            yield MessageWidget(role="welcome", content="")

    def on_mount(self) -> None:
        self.scroll_to_bottom()

    def scroll_to_bottom(self) -> None:
        """Smoothly scroll to the bottom of the chat."""
        try:
            scroll = self.query_one("#chat-scroll", VerticalScroll)
            scroll.scroll_to(y=scroll.max_scroll_y, animate=False)
        except Exception:
            pass

    def add_message(self, role: str, content: str) -> MessageWidget:
        """Add a new MessageWidget to the chat."""
        scroll = self.query_one("#chat-scroll", VerticalScroll)
        msg = MessageWidget(role=role, content=content)
        scroll.mount(msg)
        
        # Auto scroll to bottom
        self.call_after_refresh(self.scroll_to_bottom)
        return msg

    def start_thinking(self) -> ThinkingWidget:
        """Spawn a new thinking widget."""
        scroll = self.query_one("#chat-scroll", VerticalScroll)
        widget = ThinkingWidget()
        scroll.mount(widget)
        self.call_after_refresh(self.scroll_to_bottom)
        return widget

    def clear(self) -> None:
        """Clear all messages and restore welcome logo."""
        scroll = self.query_one("#chat-scroll", VerticalScroll)
        for child in list(scroll.children):
            child.remove()
        scroll.mount(MessageWidget(role="welcome", content=""))
        self.call_after_refresh(self.scroll_to_bottom)
