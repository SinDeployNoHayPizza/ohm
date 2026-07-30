"""Fake data for OHM TUI demo.

Provides realistic mock data for testing the TUI without real API keys or config.
All data is designed to look authentic and demonstrate the full UI capabilities.
"""

from datetime import datetime, timedelta
import random

# ──────────────────────────────────────────────────────────────
# Provider & Model Data
# ──────────────────────────────────────────────────────────────

FAKE_PROVIDERS = [
    {
        "name": "anthropic",
        "display_name": "Anthropic",
        "models": [
            {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4", "context_window": 200000, "cost_input": 3.0, "cost_output": 15.0},
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "context_window": 200000, "cost_input": 15.0, "cost_output": 75.0},
            {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "context_window": 200000, "cost_input": 0.25, "cost_output": 1.25},
        ],
        "status": "healthy",
        "latency_ms": 2340,
    },
    {
        "name": "openai",
        "display_name": "OpenAI",
        "models": [
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context_window": 128000, "cost_input": 10.0, "cost_output": 30.0},
            {"id": "gpt-4", "name": "GPT-4", "context_window": 8192, "cost_input": 30.0, "cost_output": 60.0},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "context_window": 16385, "cost_input": 0.5, "cost_output": 1.5},
        ],
        "status": "healthy",
        "latency_ms": 1890,
    },
    {
        "name": "google",
        "display_name": "Google Gemini",
        "models": [
            {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "context_window": 1000000, "cost_input": 1.25, "cost_output": 5.0},
            {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "context_window": 1000000, "cost_input": 0.15, "cost_output": 0.60},
            {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "context_window": 1000000, "cost_input": 0.10, "cost_output": 0.40},
        ],
        "status": "healthy",
        "latency_ms": 1560,
    },
    {
        "name": "nvidia",
        "display_name": "NVIDIA NIM",
        "models": [
            {"id": "nemotron-70b", "name": "Nemotron 70B", "context_window": 128000, "cost_input": 0.80, "cost_output": 3.20},
            {"id": "mistral-large", "name": "Mistral Large", "context_window": 128000, "cost_input": 1.00, "cost_output": 3.00},
            {"id": "deepseek-r1", "name": "DeepSeek R1", "context_window": 128000, "cost_input": 0.55, "cost_output": 2.19},
        ],
        "status": "healthy",
        "latency_ms": 1720,
    },
    {
        "name": "ollama-cloud",
        "display_name": "Ollama Cloud",
        "models": [
            {"id": "llama-3.3-70b", "name": "Llama 3.3 70B", "context_window": 128000, "cost_input": 0.20, "cost_output": 0.80},
            {"id": "qwen-2.5-72b", "name": "Qwen 2.5 72B", "context_window": 128000, "cost_input": 0.25, "cost_output": 1.00},
            {"id": "deepseek-v3", "name": "DeepSeek V3", "context_window": 128000, "cost_input": 0.14, "cost_output": 0.28},
            {"id": "gemma-3-27b", "name": "Gemma 3 27B", "context_window": 128000, "cost_input": 0.10, "cost_output": 0.40},
        ],
        "status": "healthy",
        "latency_ms": 980,
    },
    {
        "name": "local",
        "display_name": "Local (Ollama)",
        "models": [
            {"id": "llama-3-8b", "name": "Llama 3 8B", "context_window": 8192, "cost_input": 0.0, "cost_output": 0.0},
            {"id": "mistral-7b", "name": "Mistral 7B", "context_window": 8192, "cost_input": 0.0, "cost_output": 0.0},
            {"id": "phi-3", "name": "Phi-3 Mini", "context_window": 4096, "cost_input": 0.0, "cost_output": 0.0},
        ],
        "status": "degraded",
        "latency_ms": 450,
    },
]

# ──────────────────────────────────────────────────────────────
# Chat Messages
# ──────────────────────────────────────────────────────────────

FAKE_CHAT_MESSAGES = [
    {
        "role": "system",
        "content": "OHM initialized. Provider: Anthropic | Model: Claude Sonnet 4 | Sandbox: enabled",
        "timestamp": datetime.now() - timedelta(minutes=5),
    },
    {
        "role": "user",
        "content": "Fix the authentication bug in src/auth/login.py",
        "timestamp": datetime.now() - timedelta(minutes=4),
    },
    {
        "role": "agent",
        "content": "I'll analyze the authentication module to identify the bug.",
        "timestamp": datetime.now() - timedelta(minutes=4, seconds=30),
    },
    {
        "role": "agent",
        "content": "**Analyzing** `src/auth/login.py`...\n\nFound issue on line 47: JWT token expiration is not being validated.\n\n```python\n# Current (broken)\ndef validate_token(token: str) -> dict:\n    payload = jwt.decode(token, SECRET_KEY, algorithms=[\"HS256\"])\n    return payload\n\n# Fixed\ndef validate_token(token: str) -> dict:\n    payload = jwt.decode(token, SECRET_KEY, algorithms=[\"HS256\"])\n    if payload.get(\"exp\") < time.time():\n        raise TokenExpiredError(\"Token has expired\")\n    return payload\n```",
        "timestamp": datetime.now() - timedelta(minutes=3, seconds=45),
    },
    {
        "role": "user",
        "content": "Apply the fix and run the tests",
        "timestamp": datetime.now() - timedelta(minutes=3),
    },
    {
        "role": "agent",
        "content": "Applying fix to `src/auth/login.py`...\n\n```\n✓ File modified: src/auth/login.py\n✓ Added expiration check\n✓ Updated error handling\n```\n\nRunning test suite...\n\n```\ntests/test_auth.py::test_validate_token_valid PASSED\n tests/test_auth.py::test_validate_token_expired PASSED\n tests/test_auth.py::test_validate_token_invalid PASSED\n tests/test_auth.py::test_login_success PASSED\n\n============================== 4 passed in 0.82s ==============================\n```\n\nAll tests passing. The fix adds JWT expiration validation to prevent expired tokens from being accepted.",
        "timestamp": datetime.now() - timedelta(minutes=2, seconds=15),
    },
    {
        "role": "user",
        "content": "/goal Implement complete auth system with JWT, OAuth2, and RBAC",
        "timestamp": datetime.now() - timedelta(minutes=1, seconds=30),
    },
    {
        "role": "agent",
        "content": "**[GOAL MODE]** Autonomous execution started.\n\n**Goal:** Implement complete auth system with JWT, OAuth2, and RBAC\n\n**Breakdown into 6 subtasks:**\n1. Design authentication architecture\n2. Implement JWT token service\n3. Implement OAuth2 provider integration\n4. Create RBAC middleware\n5. Write integration tests\n6. Update API documentation\n\nI'll work through these autonomously. Use `/stop` to interrupt.",
        "timestamp": datetime.now() - timedelta(minutes=1, seconds=15),
    },
    {
        "role": "user",
        "content": "/loop /test --fix --max 5 --until 'all tests pass'",
        "timestamp": datetime.now() - timedelta(minutes=1),
    },
    {
        "role": "agent",
        "content": "**[LOOP MODE]** Starting test-driven loop.\n\n**Config:**\n- Command: `/test --fix`\n- Max iterations: 5\n- Condition: all tests pass\n- Auto-fix: enabled\n\n**Iteration 1/5:** Running tests...\n```\n18 passed, 4 failed\n```\nAuto-fixing 4 failures...",
        "timestamp": datetime.now() - timedelta(minutes=50, seconds=30),
    },
]

# ──────────────────────────────────────────────────────────────
# Token Usage
# ──────────────────────────────────────────────────────────────

FAKE_TOKEN_USAGE = {
    "input_tokens": 12450,
    "output_tokens": 892,
    "total_tokens": 13342,
    "max_tokens": 200000,
    "cost_usd": 0.089,
    "session_cost_usd": 0.234,
    "requests_count": 6,
    "avg_latency_ms": 2100,
}

# ──────────────────────────────────────────────────────────────
# Commands
# ──────────────────────────────────────────────────────────────

# Commands shared by both / dropdown and Ctrl+K palette.
# Entries with a "key" field map to a real OhmApp action; others are display-only.
FAKE_COMMANDS = [
    {"name": "/run", "description": "Execute a prompt", "category": "core", "hotkey": "Ctrl+Enter"},
    {"name": "/fix", "description": "Fix a specific file or issue", "category": "core", "hotkey": "Ctrl+F"},
    {"name": "/test", "description": "Run test suite", "category": "core", "hotkey": "Ctrl+T"},
    {"name": "/review", "description": "Review code changes", "category": "core", "hotkey": "Ctrl+R"},
    {"name": "/goal", "description": "Set autonomous goal with subtask breakdown", "category": "core", "hotkey": "Ctrl+G"},
    {"name": "/loop", "description": "Run task in loop until goal/condition met", "category": "core", "hotkey": "Ctrl+."},
    {"name": "/deploy", "description": "Deploy to staging/production", "category": "ops", "hotkey": None},
    {"name": "/config", "description": "Open configuration", "category": "settings", "hotkey": "Ctrl+,"},
    {"name": "/model", "description": "Switch model", "category": "settings", "hotkey": "Ctrl+M"},
    {"name": "/provider", "description": "Switch provider", "category": "settings", "hotkey": "Ctrl+P"},
    {"name": "/clear", "description": "Clear chat history", "category": "ui", "hotkey": "Ctrl+L"},
    {"name": "/help", "description": "Show help", "category": "ui", "hotkey": "F1"},
    {"name": "/status", "description": "Show system status", "category": "info", "hotkey": None},
    {"name": "/history", "description": "Show command history", "category": "info", "hotkey": "Ctrl+H"},
    {"name": "/theme", "description": "Change theme", "category": "ui", "hotkey": None},
    {"name": "/exit", "description": "Exit OHM", "category": "system", "hotkey": "Ctrl+Q"},
    # ── Real session commands (wired to OhmApp actions) ──
    {"name": "/sessions", "description": "Browse saved sessions", "category": "session", "hotkey": "F3", "key": "session_browser"},
    {"name": "/session list", "description": "List saved sessions", "category": "session", "hotkey": "F3", "key": "session_browser"},
    {"name": "/session continue", "description": "Resume the last session", "category": "session", "hotkey": None, "key": "session_continue"},
    {"name": "/session clear", "description": "Delete all sessions", "category": "session", "hotkey": None, "key": "session_clear"},
]

# ──────────────────────────────────────────────────────────────
# File Tree (for # file inclusion demo)
# ──────────────────────────────────────────────────────────────

FAKE_FILE_TREE = {
    "src/": {
        "ohm/": {
            "__init__.py": {"lines": 12, "size": "245B"},
            "cli/": {
                "app.py": {"lines": 156, "size": "4.2KB"},
                "screens/": {
                    "main.py": {"lines": 89, "size": "2.1KB"},
                    "modal.py": {"lines": 67, "size": "1.8KB"},
                },
                "widgets/": {
                    "chat.py": {"lines": 234, "size": "6.7KB"},
                    "input.py": {"lines": 178, "size": "5.1KB"},
                    "sidebar.py": {"lines": 145, "size": "3.9KB"},
                },
            },
            "core/": {
                "agent.py": {"lines": 312, "size": "8.9KB"},
                "provider.py": {"lines": 267, "size": "7.3KB"},
                "models.py": {"lines": 89, "size": "2.4KB"},
            },
        },
    },
    "tests/": {
        "test_agent.py": {"lines": 156, "size": "4.1KB"},
        "test_provider.py": {"lines": 123, "size": "3.3KB"},
    },
    "pyproject.toml": {"lines": 28, "size": "512B"},
    "README.md": {"lines": 450, "size": "12.8KB"},
}

# ──────────────────────────────────────────────────────────────
# Fake File Content (for preview)
# ──────────────────────────────────────────────────────────────

FAKE_FILE_CONTENT = {
    "src/ohm/cli/app.py": '''"""OHM TUI Application - Main entry point."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual import on

from ohm.cli.screens.main import MainScreen
from ohm.cli.themes.default import OHM_DEFAULT, OHM_LIGHT, OHM_OCEAN


class OhmApp(App[None]):
    """OHM TUI Application."""

    TITLE = "OHM"
    SUB_TITLE = "Orchestrator & Harness for Models"

    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear", "Clear", show=True),
        Binding("ctrl+k", "command_palette", "Commands", show=True),
        Binding("ctrl+s", "toggle_sidebar", "Sidebar", show=True),
        Binding("ctrl+d", "toggle_theme", "Theme", show=True),
    ]

    THEMES = {
        "default": OHM_DEFAULT,
        "light": OHM_LIGHT,
        "ocean": OHM_OCEAN,
    }

    def __init__(self) -> None:
        super().__init__()
        self.current_theme_name = "default"
        self.apply_theme(self.THEMES["default"])

    def compose(self) -> ComposeResult:
        yield MainScreen()

    def action_clear(self) -> None:
        """Clear the chat area."""
        self.query_one("ChatArea").clear()

    def action_toggle_sidebar(self) -> None:
        """Toggle the sidebar visibility."""
        sidebar = self.query_one("Sidebar")
        sidebar.visible = not sidebar.visible

    def action_toggle_theme(self) -> None:
        """Cycle through themes."""
        themes = list(self.THEMES.keys())
        idx = themes.index(self.current_theme_name)
        self.current_theme_name = themes[(idx + 1) % len(themes)]
        self.apply_theme(self.THEMES[self.current_theme_name])


def main() -> None:
    """Run the OHM TUI."""
    app = OhmApp()
    app.run()


if __name__ == "__main__":
    main()
''',
    "src/ohm/core/agent.py": '''"""Agent placeholder for OHM demo."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentConfig:
    """Configuration for an OHM agent."""
    name: str = "ohm-agent"
    model: str = "claude-sonnet-4-20250514"
    provider: str = "anthropic"
    sandbox: bool = True
    max_tokens: int = 4096
    temperature: float = 0.7
    skills: list[str] = field(default_factory=list)


@dataclass
class AgentResponse:
    """Response from an agent execution."""
    content: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    success: bool = True
    error: str | None = None


class Agent:
    """Placeholder agent for OHM demo."""

    def __init__(self, config: AgentConfig | None = None) -> None:
        self.config = config or AgentConfig()
        self.history: list[dict[str, str]] = []

    async def run(self, prompt: str) -> AgentResponse:
        """Execute a prompt (placeholder)."""
        # TODO: Implement real agent execution
        return AgentResponse(
            content=f"[DEMO] Agent received: {prompt}",
            tokens_used=150,
            latency_ms=2340.0,
            cost_usd=0.003,
        )

    def get_status(self) -> dict[str, Any]:
        """Get current agent status."""
        return {
            "name": self.config.name,
            "model": self.config.model,
            "provider": self.config.provider,
            "sandbox": self.config.sandbox,
            "history_length": len(self.history),
        }
''',
}


# ──────────────────────────────────────────────────────────────
# Hotkeys
# ──────────────────────────────────────────────────────────────

FAKE_HOTKEYS = [
    {"key": "Ctrl+K", "action": "Command Palette", "category": "Navigation"},
    {"key": "Ctrl+L", "action": "Clear Chat", "category": "UI"},
    {"key": "Ctrl+P", "action": "Switch Provider", "category": "Provider"},
    {"key": "Ctrl+M", "action": "Switch Model", "category": "Provider"},
    {"key": "Ctrl+S", "action": "Toggle Sidebar", "category": "UI"},
    {"key": "Ctrl+D", "action": "Toggle Theme", "category": "UI"},
    {"key": "Ctrl+Q", "action": "Quit", "category": "System"},
    {"key": "Ctrl+Enter", "action": "Send Message", "category": "Chat"},
    {"key": "Ctrl+T", "action": "Run Tests", "category": "Core"},
    {"key": "Ctrl+R", "action": "Review Code", "category": "Core"},
    {"key": "Ctrl+F", "action": "Fix File", "category": "Core"},
    {"key": "Ctrl+G", "action": "Set Goal", "category": "Core"},
    {"key": "Ctrl+.", "action": "Run Loop", "category": "Core"},
    {"key": "Ctrl+H", "action": "Command History", "category": "Info"},
    {"key": "Ctrl+,", "action": "Open Settings", "category": "Settings"},
    {"key": "F1", "action": "Show Help", "category": "UI"},
    {"key": "Esc", "action": "Close Modal", "category": "UI"},
    {"key": "Tab", "action": "Autocomplete", "category": "Input"},
]


# ──────────────────────────────────────────────────────────────
# ASCII Art Logo
# ──────────────────────────────────────────────────────────────

OHM_LOGO = """
 ██████╗ ██╗  ██╗███╗   ███╗
██╔═══██╗██║  ██║████╗ ████║
██║   ██║███████║██╔████╔██║
██║   ██║██╔══██║██║╚██╔╝██║
╚██████╔╝██║  ██║██║ ╚═╝ ██║
 ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝

     Orchestration & Harness for Models
"""

OHM_LOGO_SMALL = """
 ██████╗ ██╗  ██╗███╗   ███╗
██╔═══██╗██║  ██║████╗ ████║
██║   ██║███████║██╔████╔██║
██║   ██║██╔══██║██║╚██╔╝██║
╚██████╔╝██║  ██║██║ ╚═╝ ██║
 ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝

     Orchestration & Harness for Models
"""

# ─── ANSI color logo variants ─────────────────────────────────
# Render with: Text.from_ansi(OHM_LOGO_VARIANTS[name]) (Rich)
# Pick one randomly via get_random_logo()

import random as _random

_LOGO_COMMON = (
    "\x1b[0;90;1;40m░░▒▓▓██▓▓▒░░\x1b[0;37;40m "
    "\x1b[0;90;1;40m█▓▓▒▒▌\x1b[0;37;40m "
    "\x1b[0;90;1;40m█▓▓▒▒\x1b[0;37;40m "
    "\x1b[0;90;1;40m█▓▓▒▒▌▓░\x1b[0;37;40m "
    "\x1b[0;90;1;40m█▓▓▒▒\x1b[0m\n"
    "\x1b[0;37;40m \x1b[0;90;1;40m░▒▓▓██▓▓▒░\x1b[0;37;40m  "
    "\x1b[0;90;1;40m█▓▓▒▒▌\x1b[0;37;40m "
    "\x1b[0;90;1;40m█▓▓▒▒\x1b[0;37;40m "
    "\x1b[0;90;1;40m█▓▓▒▒▌▐\x1b[0;37;40m  "
    "\x1b[0;90;1;40m█▓▓▒▒\x1b[0m"
)

_LOGO_LINE1 = "\x1b[0;37;40m ▄▀▀▀▀▀▀▀▀▄  █▀▀▀█  █▀▀▀█ █▀▀▀█    █▀▀▀█\x1b[0m\n"

def _make_variant(border, fg, bg, bright):
    """Build an ANSI logo variant from color numbers."""
    return (
        _LOGO_LINE1 +
        f"\x1b[{border}m░\x1b[0;{fg};40m░░░\x1b[0;37;40m▄▄▄\x1b[0;{fg};40m░░░░\x1b[{border}m░\x1b[0;37;40m "
        f"\x1b[{border}m░\x1b[0;{fg};40m░░░\x1b[{border}m░\x1b[0;37;40m  "
        f"\x1b[{border}m░\x1b[0;{fg};40m░░░\x1b[{border}m░\x1b[0;37;40m "
        f"\x1b[{border}m░\x1b[0;{fg};40m░░░\x1b[0;37;{bg}m▐\x1b[0;37;40m▌  ▐\x1b[0;37;{bg}m▌\x1b[0;{fg};40m░░░\x1b[{border}m░\x1b[0m\n"
        f"\x1b[{border}m▒\x1b[0;{fg};40m▒▒▒\x1b[{border}m▒\x1b[0;90;1;40m▓▓\x1b[{border}m▒\x1b[0;{fg};40m▒▒▒\x1b[{border}m▒\x1b[0;37;40m "
        f"\x1b[{border}m▒\x1b[0;{fg};40m▒▒▒\x1b[{border}m▒\x1b[0;37;40m  "
        f"\x1b[{border}m▒\x1b[0;{fg};40m▒▒▒\x1b[{border}m▒\x1b[0;37;40m "
        f"\x1b[{border}m▒\x1b[0;{fg};40m▒▒▒▒\x1b[{border}m▒\x1b[0;37;40m  "
        f"\x1b[{border}m▒\x1b[0;{fg};40m▒▒▒▒\x1b[{border}m▒\x1b[0m\n"
        f"\x1b[{border}m▓\x1b[0;{fg};40m▓▓▓\x1b[{border}m▓\x1b[0;90;1;40m▒▒\x1b[{border}m▓\x1b[0;{fg};40m▓▓▓\x1b[{border}m▓\x1b[0;37;40m "
        f"\x1b[{border}m▓\x1b[0;{fg};40m▓▓▓\x1b[{border}m▓\x1b[0;37;40m  "
        f"\x1b[{border}m▓\x1b[0;{fg};40m▓▓▓\x1b[{border}m▓\x1b[0;37;40m "
        f"\x1b[{border}m▓\x1b[0;{fg};40m▓▓▓▓\x1b[0;{bright};1;{bg}m▐\x1b[0;97;1;40m▌▐\x1b[0;{bright};1;{bg}m▌\x1b[0;{fg};40m▓▓▓▓\x1b[{border}m▓\x1b[0m\n"
        f"\x1b[{border}m█\x1b[0;{fg};40m███\x1b[{border}m█\x1b[0;37;40m  "
        f"\x1b[{border}m█\x1b[0;{fg};40m███\x1b[{border}m█\x1b[0;37;40m "
        f"\x1b[{border}m█\x1b[0;{fg};40m███\x1b[0;{bright};1;{bg}m▀▀▀▀\x1b[0;{fg};40m███\x1b[{border}m█\x1b[0;37;40m "
        f"\x1b[{border}m█\x1b[0;{fg};40m█████\x1b[{border}m██\x1b[0;{fg};40m█████\x1b[{border}m█\x1b[0m\n"
        f"\x1b[0;97;1;40m█\x1b[0;{bright};1;{bg}m░░░\x1b[0;97;1;40m█\x1b[0;37;40m  "
        f"\x1b[0;97;1;{bg}m█\x1b[0;{bright};1;{bg}m░░░\x1b[0;97;1;{bg}m█\x1b[0;37;40m "
        f"\x1b[0;97;1;40m█\x1b[0;{bright};1;{bg}m░░░\x1b[0;97;1;{bg}m▄▄▄▄\x1b[0;{bright};1;{bg}m░░░\x1b[0;97;1;40m█\x1b[0;37;40m "
        f"\x1b[0;97;1;{bg}m█\x1b[0;{bright};1;{bg}m░░░\x1b[0;97;1;{bg}m▄\x1b[0;{bright};1;{bg}m░\x1b[0;97;1;{bg}m▀▀\x1b[0;{bright};1;{bg}m░\x1b[0;97;1;{bg}m▄\x1b[0;{bright};1;{bg}m░░░\x1b[0;97;1;{bg}m█\x1b[0m\n"
        f"\x1b[0;90;1;47m▓\x1b[0;{bright};1;{bg}m▒▒▒\x1b[0;90;1;47m▓\x1b[0;37;40m  "
        f"\x1b[0;90;1;47m▓\x1b[0;{bright};1;{bg}m▒▒▒\x1b[0;90;1;47m▓\x1b[0;37;40m "
        f"\x1b[0;90;1;47m▓\x1b[0;{bright};1;{bg}m▒▒▒\x1b[0;90;1;47m▓\x1b[0;90;1;40m▓▓\x1b[0;90;1;47m▓\x1b[0;{bright};1;{bg}m▒▒▒\x1b[0;90;1;47m▓\x1b[0;37;40m "
        f"\x1b[0;90;1;47m▓\x1b[0;{bright};1;{bg}m▒▒▒\x1b[0;90;1;47m▓▒\x1b[0;{bright};1;{bg}m▒▒\x1b[0;90;1;47m▒▓\x1b[0;{bright};1;{bg}m▒▒▒\x1b[0;90;1;47m▓\x1b[0m\n"
        f"\x1b[0;90;1;47m▒\x1b[0;{bright};1;{bg}m▓▓▓\x1b[0;90;1;47m▒\x1b[0;90;1;40m▄▄\x1b[0;90;1;47m▒\x1b[0;{bright};1;{bg}m▓▓▓\x1b[0;90;1;47m▒\x1b[0;37;40m "
        f"\x1b[0;90;1;47m▒\x1b[0;{bright};1;{bg}m▓▓▓\x1b[0;90;1;47m▒\x1b[0;90;1;40m▓▓\x1b[0;90;1;47m▒\x1b[0;{bright};1;{bg}m▓▓▓\x1b[0;90;1;47m▒\x1b[0;37;40m "
        f"\x1b[0;90;1;47m▒\x1b[0;{bright};1;{bg}m▓▓▓\x1b[0;90;1;47m▒▌\x1b[0;{bright};1;47m▐▌\x1b[0;90;1;47m▐▒\x1b[0;{bright};1;{bg}m▓▓▓\x1b[0;90;1;47m▒\x1b[0m\n"
        f"\x1b[0;90;1;47m░\x1b[0;{bright};1;{bg}m███\x1b[0;{bright};1;40m█\x1b[0;{bright};1;47m▄▄\x1b[0;{bright};1;{bg}m████\x1b[0;90;1;47m░\x1b[0;37;40m "
        f"\x1b[0;90;1;47m░\x1b[0;{bright};1;{bg}m███\x1b[0;90;1;47m░\x1b[0;90;1;40m▌\x1b[0;37;40m "
        f"\x1b[0;90;1;47m░\x1b[0;{bright};1;{bg}m███\x1b[0;90;1;47m░\x1b[0;37;40m "
        f"\x1b[0;90;1;47m░\x1b[0;{bright};1;{bg}m███\x1b[0;90;1;47m░\x1b[0;90;1;40m▓\x1b[0;90;1;47m░░\x1b[0;90;1;40m▒\x1b[0;90;1;47m░\x1b[0;{bright};1;{bg}m███\x1b[0;90;1;47m░\x1b[0m\n"
        f"\x1b[0;90;1;40m░\x1b[0;90;1;47m▄\x1b[0;37;{bg}m▄▄▄▄▄▄▄▄\x1b[0;90;1;47m▄\x1b[0;90;1;40m░\x1b[0;37;40m "
        f"█\x1b[0;37;{bg}m▄▄▄\x1b[0;37;40m█\x1b[0;90;1;40m▌\x1b[0;37;40m "
        f"█\x1b[0;37;{bg}m▄▄▄\x1b[0;37;40m█ "
        f"█\x1b[0;37;{bg}m▄▄▄\x1b[0;37;40m█\x1b[0;90;1;40m▓\x1b[0;90;1;47m▌▐\x1b[0;90;1;40m░\x1b[0;37;40m█\x1b[0;37;{bg}m▄▄▄\x1b[0;37;40m█\x1b[0m\n"
        + _LOGO_COMMON
    )

# Variant definitions: (border_code, fg_num, bg_num, bright_num)
_LOGO_VARIANT_DEFS = {
    "blue":        ("0;97;1;47", 32, 42, 92),
    "cyan":        ("0;97;1;47", 33, 43, 93),
    "green":       ("0;97;1;47", 32, 42, 92),
    "purple":      ("0;97;1;47", 35, 45, 95),
    "red":         ("0;96;1;47", 34, 44, 94),
    "silver":      ("0;97;1;47", 37, 47, 97),
}

OHM_LOGO_VARIANTS: dict[str, str] = {
    name: _make_variant(*params)
    for name, params in _LOGO_VARIANT_DEFS.items()
}

OHM_LOGO_ANSI = OHM_LOGO_VARIANTS["blue"]  # default

def get_random_logo() -> str:
    """Return a random ANSI logo variant."""
    return _random.choice(list(OHM_LOGO_VARIANTS.values()))


# ──────────────────────────────────────────────────────────────
# Status Data
# ──────────────────────────────────────────────────────────────

FAKE_STATUS = {
    "version": "0.1.0-alpha",
    "uptime": "2h 34m 12s",
    "sandbox_status": "active",
    "sandbox_mode": "strict",
    "mcp_status": "connected",
    "acp_status": "standby",
    "a2a_status": "disabled",
    "memory_usage": "245MB",
    "cpu_usage": "12%",
    "active_skills": ["python-debugger", "git-ops", "code-review"],
    "pending_tasks": 0,
    "completed_tasks": 23,
    "failed_tasks": 1,
}


# ──────────────────────────────────────────────────────────────
# Goal / Loop Data (for autonomous execution demo)
# ──────────────────────────────────────────────────────────────

FAKE_GOAL = {
    "description": "Implement complete authentication system with JWT, OAuth2, and role-based access control",
    "status": "in_progress",
    "created_at": datetime.now() - timedelta(minutes=15),
    "subtasks": [
        {
            "id": "goal-001",
            "description": "Design authentication architecture",
            "status": "completed",
            "files_changed": ["docs/auth-architecture.md"],
            "duration_s": 45,
        },
        {
            "id": "goal-002",
            "description": "Implement JWT token service",
            "status": "completed",
            "files_changed": ["src/auth/jwt.py", "src/auth/config.py"],
            "duration_s": 120,
        },
        {
            "id": "goal-003",
            "description": "Implement OAuth2 provider integration",
            "status": "in_progress",
            "files_changed": ["src/auth/oauth.py"],
            "duration_s": 0,
        },
        {
            "id": "goal-004",
            "description": "Create RBAC middleware",
            "status": "pending",
            "files_changed": [],
            "duration_s": 0,
        },
        {
            "id": "goal-005",
            "description": "Write integration tests",
            "status": "pending",
            "files_changed": [],
            "duration_s": 0,
        },
        {
            "id": "goal-006",
            "description": "Update API documentation",
            "status": "pending",
            "files_changed": [],
            "duration_s": 0,
        },
    ],
    "total_tokens_used": 8420,
    "total_cost_usd": 0.127,
    "elapsed_time_s": 165,
}


FAKE_LOOP = {
    "description": "Run tests until all pass or max iterations reached",
    "command": "/test --watch",
    "status": "running",
    "current_iteration": 3,
    "max_iterations": 10,
    "condition": "all tests pass",
    "started_at": datetime.now() - timedelta(minutes=2),
    "iterations": [
        {
            "iteration": 1,
            "timestamp": datetime.now() - timedelta(minutes=2),
            "result": "failed",
            "tests_passed": 18,
            "tests_failed": 4,
            "duration_s": 12.3,
            "fixes_applied": ["Fixed import in test_auth.py", "Updated mock in test_provider.py"],
        },
        {
            "iteration": 2,
            "timestamp": datetime.now() - timedelta(minutes=1, seconds=30),
            "result": "failed",
            "tests_passed": 20,
            "tests_failed": 2,
            "duration_s": 11.8,
            "fixes_applied": ["Fixed assertion in test_jwt.py"],
        },
        {
            "iteration": 3,
            "timestamp": datetime.now() - timedelta(minutes=1),
            "result": "running",
            "tests_passed": 0,
            "tests_failed": 0,
            "duration_s": 0,
            "fixes_applied": [],
        },
    ],
    "total_tokens_used": 3200,
    "total_cost_usd": 0.048,
}


# Goal/Loop status messages for chat display
FAKE_GOAL_MESSAGES = [
    {"role": "system", "content": "[GOAL] Starting autonomous execution: Implement complete authentication system"},
    {"role": "agent", "content": "**Goal分解:** Breaking down into 6 subtasks...\n\n1. Design authentication architecture\n2. Implement JWT token service\n3. Implement OAuth2 provider integration\n4. Create RBAC middleware\n5. Write integration tests\n6. Update API documentation"},
    {"role": "agent", "content": "**[1/6] Design authentication architecture**\n\nAnalyzing existing codebase patterns...\nCreating architecture document...\n```\n+ docs/auth-architecture.md (created)\n```"},
    {"role": "agent", "content": "**[2/6] Implement JWT token service**\n\nImplementing JWT with RS256 signing...\nAdding token refresh logic...\n```\n+ src/auth/jwt.py (created, 156 lines)\n+ src/auth/config.py (modified)\n```"},
    {"role": "agent", "content": "**[3/6] Implement OAuth2 provider integration** (in progress)\n\nConnecting to Google OAuth2 endpoint...\nImplementing PKCE flow..."},
]

FAKE_LOOP_MESSAGES = [
    {"role": "system", "content": "[LOOP] Starting loop: /test --watch (max: 10 iterations, condition: all tests pass)"},
    {"role": "agent", "content": "**Iteration 1/10** running test suite...\n\n```\nFAILED tests/test_auth.py::test_validate_token_expired\nFAILED tests/test_auth.py::test_oauth_callback\nFAILED tests/test_provider.py::test_rate_limit\nFAILED tests/test_jwt.py::test_refresh_token\n\n18 passed, 4 failed in 12.3s\n```"},
    {"role": "agent", "content": "**Auto-fixing** 4 failing tests...\n- Fixed import in test_auth.py\n- Updated mock in test_provider.py\n- Corrected assertion in test_jwt.py"},
    {"role": "agent", "content": "**Iteration 2/10** running test suite...\n\n```\nFAILED tests/test_auth.py::test_oauth_callback\nFAILED tests/test_jwt.py::test_refresh_token\n\n20 passed, 2 failed in 11.8s\n```"},
    {"role": "agent", "content": "**Auto-fixing** 2 remaining tests...\n- Fixed assertion in test_jwt.py"},
    {"role": "agent", "content": "**Iteration 3/10** running test suite...\n\n```\n22 passed, 0 failed in 10.2s\n```"},
    {"role": "system", "content": "[LOOP] Condition met: all tests pass. Loop completed in 3 iterations."},
]
