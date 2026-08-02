# Design: Skills Registry Follow-ups (FU-001..FU-008)

## Technical Approach

Eight isolated, test-first edits closing the archived `skills-registry-loader` follow-ups. One new CLI sub-action (`inspect`), one loader change (`path.resolve()`), one cosmetic glyph fix, one import cleanup, six new/renamed tests, and a frontmatter-only spec-wording delta (FU-007). Priority first-wins (FU-004) and header-only fallback (FU-007) are **already correct in code** — they get regression tests and spec alignment only, no production change. No capabilities added; `strict_tdd: true` applies.

## Architecture Decisions

### D1: `ohm skill inspect <name>` wiring (FU-001)
| Option | Tradeoff | Decision |
|---|---|---|
| Subparser + handler branch via `get_skill` | Minimal, mirrors `list` pattern | ✅ |
| Rebuild CLI routing | Out of scope; breaks parity test | ❌ |

- `register_args` (skill.py:21): `p = subparsers.add_parser("inspect", help="Inspect a skill")`; `p.add_argument("name", help="Skill name")`. Sub-actions don't touch `CLI_TUI_MAPPING` or the 15-subcommand parity count.
- Handler branch: `name = getattr(args, "name", "")` (defensive for direct `Namespace`); `skill = registry.get_skill(name)`; found → print block, `return 0`; else `print(f"Skill not found: {name}")`, `return 1`. Discovery/registry build stays as-is (lines 34-39) — no restructuring.
- Output block (list style, ASCII-safe; ordering to confirm in tasks):
  ```
  Skill: {name}
  Status: enabled|disabled
  Description: {description}
  Path: {path}
  Instructions:
  {instructions}
  ```

### D2: Absolute `Skill.path` (FU-005)
`parse_skill_file` (loader.py:71): `path=path.parent.resolve()`. Verified by grep: sole consumer of `Skill.path` in src is skill.py:51 (list output); TUI stores the discover dict and only does `.get(name)` (app.py:252/388/414) — never `.path`. `resolve()` also normalizes `..`/symlinks; discovery order and first-wins untouched. Main spec already documents `path`: Absolute.

### D3: ASCII-safe list output (FU-002)
`rg "[^\x00-\x7F]"` on skill.py → only line 50. Replace `  • {name:<24} ({status}) — {desc}` with `  - {name:<24} ({status}) - {desc}`. Boundary: user-authored name/description text is **not** sanitized; the ASCII scenario uses an ASCII fixture.

### D4: Priority override first-wins (FU-004) — test-only
`discover_skills` (loader.py:90) already applies `if skill and skill.name not in skills` over priority-ordered `search_paths` — first-wins by construction. No code change; loader-layer regression test below.

### D5: Naming canonicalization (FU-006)
`parse_skill_md` survives only in archived docs (immutable), `docs/follow-ups.md:18` (historical tracking — out of scope), and test_skills.py:36 method name. Rename that method to `test_parse_skill_file_with_yaml_frontmatter`. Call sites already canonical: loader.py:38/89, test_skills.py:45.

### D6: Unknown-action test (FU-008) — test-only
Handler branch skill.py:54-55 already prints and returns 1. CLI-unreachable: unknown sub-action → `parse_known_args` unknown-args → `EXIT_USAGE_ERROR` (2) in dispatch (registry.py:268). Reachable only via direct `handler(Namespace(skill_action="unknown"))` — the spec's exact scenario. Exit semantics unchanged (2 = usage, 1 = general).

### D7: Header-only SKILL.md (FU-007) — spec delta + test
Code already matches the delta wording: no frontmatter → `name = path.parent.name`, `description = f"Skill {name}"`, `instructions = content` (loader.py:49-51); frontmatter-only parsing (lines 54-66); headers never parsed as metadata. No loader change; regression test + delta spec merged at archive.

## Data Flow

```
ohm skill inspect <name>
  → Namespace(skill_action="inspect", name=...)
  → SkillLoader.discover_skills(DEFAULT_SKILL_SEARCH_PATHS())   # first-wins; absolute paths
  → SkillRegistry.register(skill)                               # dict by name
  → registry.get_skill(name)
       ├─ found     → print details block → 0
       └─ not found → "Skill not found: …" → 1
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/ohm/commands/skill.py` | Modify | `inspect` subparser + handler branch; ASCII glyphs (line 50) |
| `src/ohm/core/skills/loader.py` | Modify | `path=path.parent.resolve()` (line 71) |
| `src/ohm/core/skills/registry.py` | Modify | remove unused `from typing import Sequence` (line 5) |
| `tests/test_cli.py` | Modify | drop 9 F401 imports; add 3 tests |
| `tests/test_skills.py` | Modify | drop `pytest` import; rename test; add 3 tests |

## Interfaces / Contracts

- `Skill.path: Path` — invariant becomes "always absolute" (documented in docstring).
- `handler(args) -> int` — returns raw 0/1 (existing style; no `EXIT_*` constants).
- `inspect` is a sub-action: `TestCliTuiParity` (15 subcommands) and `CLI_TUI_MAPPING` untouched.
- No new public API; `parse_skill_file` remains canonical.

## Testing Strategy (RED-first)

| Layer | What | Focused test name (file) |
|---|---|---|
| Unit | Priority first-wins: `foo` in `.agents/skills` (desc A) + `.ohm/skills` (desc B) via `DEFAULT_SKILL_SEARCH_PATHS()`; assert A wins | `test_discover_skills_priority_override_first_wins` (test_skills.py) |
| Unit | Path absolute from relative search dir; points at folder with `SKILL.md` | `test_discover_skills_path_is_absolute` (test_skills.py) |
| Unit | Header-only fallback: dirname + generic desc + full text; headers NOT metadata | `test_parse_skill_file_header_only_falls_back_to_dirname` (test_skills.py) |
| Unit | Inspect known skill: exit 0; name/desc/abs path/enabled/instructions | `test_skill_inspect_displays_skill_details` (test_cli.py) |
| Unit | Inspect unknown: exit 1 + not-found message | `test_skill_inspect_unknown_returns_one` (test_cli.py) |
| Unit | Direct `Namespace(skill_action="unknown")` → exit 1 + message | `test_skill_handler_unknown_action_returns_one` (test_cli.py) |
| Unit | List output all codepoints ≤ 0x7E | `test_skill_list_output_is_ascii_only` (test_cli.py) |
| Lint | Zero F401 on all five files | `uv run ruff check` (verify-time) |

Renamed: `test_parse_skill_md_with_yaml_frontmatter` → `test_parse_skill_file_with_yaml_frontmatter` (FU-006).

## Threat Matrix

| Boundary | Applicability | Reason |
|---|---|---|
| Documentation-like paths | N/A | no file classification/execution logic added |
| Git repository selection | N/A | no git interaction |
| Commit state | N/A | no index/worktree semantics |
| Push state | N/A | no ref resolution |
| PR commands | N/A | no external command composition |

In-process argparse routing + pre-existing `SKILL.md` file reads only; no shell, subprocess, or VCS boundary.

## Migration / Rollout

No migration. `resolve()` only changes printed output; nothing persisted. FU-007 delta (`specs/skills-registry/`) lands at archive via delta sync — no code effect.

## Open Questions

- None blocking. Low-risk conventions adopted (documented in D1/D6): not-found message prints to stdout (matches unknown-action branch), output-block field order confirmable during tasks.
