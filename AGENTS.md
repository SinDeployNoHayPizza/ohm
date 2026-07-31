# Code Review Rules — OHM

## Python
- Use Python 3.12+ features, strict typing, and dataclasses/pydantic models.
- Standard imports ordering: stdlib, third-party, local `ohm` packages.
- Strict TDD mode: unit tests must accompany new core/cli logic.

## Architecture
- Core components reside in `src/ohm/core/`.
- CLI & TUI widgets reside in `src/ohm/cli/`.
- Commands reside in `src/ohm/commands/`.
- Keep provider models decoupled via abstract `Provider` interface.
