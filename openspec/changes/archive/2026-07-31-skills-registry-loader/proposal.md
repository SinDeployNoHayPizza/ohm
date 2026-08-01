# Proposal: Skills Registry & Loader (Fase 2)

## Intent

Implement an enterprise-grade Skills Registry & Loader for OHM. Skills are declarative, autonomous capability packages containing `SKILL.md` definitions, tool configurations, and prompt templates. The loader must discover, validate, register, and load skills dynamically into the agent runtime.

## Scope

1. **Skill Specification & Schema**: Standardized directory structure (`SKILL.md`, `tools.yaml`, `prompts/`).
2. **Discovery & Resolver**: Auto-discover skills in `.agents/skills`, `.claude/skills`, `~/.ohm/skills`, and explicit `--skills` paths.
3. **Skill Registry**: In-memory and persistent registry managing active skills, permissions, and tool bindings.
4. **CLI Integration**: `ohm skill list`, `ohm skill install`, and `ohm run --skills <skill-names>`.
