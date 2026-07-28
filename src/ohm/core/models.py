"""OHM Data Models - Shared data structures."""

from dataclasses import dataclass, field
from typing import Any
from datetime import datetime
from enum import Enum


class MessageRole(Enum):
    """Message roles in a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Message:
    """A single message in a conversation."""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    tokens: int = 0
    cost_usd: float = 0.0


@dataclass
class Task:
    """A task to be executed by an agent."""
    id: str
    prompt: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: str | None = None
    error: str | None = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """A chat session."""
    id: str
    messages: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: MessageRole, content: str, **kwargs: Any) -> Message:
        """Add a message to the session."""
        msg = Message(role=role, content=content, **kwargs)
        self.messages.append(msg)
        self.updated_at = datetime.now()
        self.total_tokens += msg.tokens
        self.total_cost_usd += msg.cost_usd
        return msg

    def get_messages_for_provider(self) -> list[dict[str, str]]:
        """Get messages formatted for provider API."""
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in self.messages
        ]


@dataclass
class TokenUsage:
    """Token usage statistics."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    max_tokens: int = 200000
    cost_usd: float = 0.0

    @property
    def percentage(self) -> float:
        """Calculate context usage percentage."""
        if self.max_tokens == 0:
            return 0.0
        return (self.total_tokens / self.max_tokens) * 100

    @property
    def remaining(self) -> int:
        """Calculate remaining tokens."""
        return max(0, self.max_tokens - self.total_tokens)


@dataclass
class ProviderInfo:
    """Provider information."""
    name: str
    display_name: str
    status: str  # healthy, degraded, unhealthy
    models: list[dict[str, Any]] = field(default_factory=list)
    latency_ms: float = 0.0
