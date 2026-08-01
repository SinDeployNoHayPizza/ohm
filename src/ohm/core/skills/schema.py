"""Schema definitions for OHM Skills."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Skill:
    """Represents a loaded skill capability package."""

    name: str
    description: str
    path: Path
    instructions: str
    enabled: bool = True
    metadata: dict = field(default_factory=dict)
