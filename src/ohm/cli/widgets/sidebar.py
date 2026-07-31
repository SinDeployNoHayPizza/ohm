"""OHM Sidebar Widget - Provider/model info, token usage, and real-time status."""

from __future__ import annotations

from textual.widget import Widget
from textual.app import RenderResult

from ohm.core.provider import PROVIDER_CATALOG


class Sidebar(Widget):
    """Right sidebar displaying real-time provider, model, token usage, and agent status."""

    DEFAULT_CSS = """
    Sidebar {
        width: 35;
        height: 100%;
        background: $surface;
        border-left: solid $panel;
        padding: 1 2;
    }
    """

    def render(self) -> RenderResult:
        """Render the sidebar with real data from app and agent state."""

        # ── Provider & model ────────────────────────────────────
        provider_name = getattr(self.app, "current_provider", "?")
        model_name = getattr(self.app, "current_model_name", "?")
        catalog = PROVIDER_CATALOG.get(provider_name)
        display_name = catalog.display_name if catalog else provider_name.capitalize()

        # Check API key status
        config = getattr(self.app, "config", None)
        api_key = config.api_key_for(provider_name) if config else None
        status_icon = "✓" if api_key else "✗"

        # ── Context window ──────────────────────────────────────
        context_window = getattr(self.app, "_current_context_window", 0)
        context_desc = f"{context_window // 1000}k window" if context_window else "?"

        # ── Token & cost (real data) ────────────────────────────
        total_tokens = getattr(self.app, "_total_tokens_used", 0)

        agent = getattr(self.app, "agent", None)
        agent_state = agent.state if agent else None

        if agent_state:
            total_cost = agent_state.total_cost_usd
            tasks_done = agent_state.tasks_completed
            tasks_failed = agent_state.tasks_failed
            is_running = agent_state.is_running
        else:
            total_cost = 0.0
            tasks_done = 0
            tasks_failed = 0
            is_running = False

        # Context usage percentage
        context_pct = (total_tokens / context_window * 100) if context_window > 0 else 0.0
        progress_bar = self._make_progress_bar(context_pct)

        # ── Formatting ─────────────────────────────────────────
        tokens_str = f"{total_tokens:,}" if total_tokens else "0"
        max_tokens_str = f"{context_window:,}" if context_window else "?"
        cost_str = f"${total_cost:.4f}" if total_cost else "$0.0000"

        # ── Agent config status ─────────────────────────────────
        sandbox_enabled = agent.config.sandbox if agent and agent.config else False
        sandbox_status = "enabled" if sandbox_enabled else "disabled"
        tools = agent.config.tools if agent and agent.config else []

        running_tag = "[green]active[/]" if is_running else "[dim]idle[/]"

        return f"""[bold]Provider[/]
[cyan]{display_name}[/] {status_icon}

[bold]Model[/]
[dim]{model_name}[/]

[bold]Context[/]
[dim]  {context_desc}[/]

[bold]Tokens[/]
Total:  [cyan]{tokens_str}[/] / {max_tokens_str}

[bold]Cost[/]
[cyan]{cost_str}[/]

[bold]Context Usage[/]
{progress_bar} [cyan]{context_pct:.1f}%[/]

[bold]Status[/]
Sandbox: [green]{sandbox_status}[/]
Agent:   {running_tag}
Tasks:   [cyan]{tasks_done}[/] done, [red]{tasks_failed}[/] failed

[bold]Tools ({len(tools)})[/]
{self._format_tools(tools)}
"""

    def _make_progress_bar(self, percentage: float, width: int = 20) -> str:
        """Create a visual progress bar."""
        filled = int(width * percentage / 100)
        empty = width - filled

        if percentage > 80:
            color = "red"
        elif percentage > 60:
            color = "yellow"
        else:
            color = "green"

        bar = f"[{color}]{'█' * filled}[/][dim]{'░' * empty}[/]"
        return bar

    def _format_tools(self, tools: list[str]) -> str:
        """Format tools list."""
        if not tools:
            return "  [dim]none[/]"
        return "\n".join(f"  * [cyan]{s}[/]" for s in tools)
