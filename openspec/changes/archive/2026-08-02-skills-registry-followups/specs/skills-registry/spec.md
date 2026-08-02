# Delta for skills-registry

## ADDED Requirements

### Requirement: Skill Inspection

`ohm skill inspect <name>` MUST display a registered skill's name, description, absolute path, enabled state, and instructions in the style of `ohm skill list`, exiting 0. For an unknown name it MUST print a not-found message and exit 1.

#### Scenario: Inspect a known skill

- GIVEN a registered skill named `python-debugger`
- WHEN `ohm skill inspect python-debugger` runs
- THEN output shows name, description, path, enabled state, and instructions
- AND the exit code is 0

#### Scenario: Inspect an unknown skill

- GIVEN no registered skill named `bogus`
- WHEN `ohm skill inspect bogus` runs
- THEN a not-found message is printed
- AND the exit code is 1

### Requirement: ASCII-Safe Skill Output

`ohm skill list` output MUST use only ASCII printable characters (no `•` or `—`), so it renders correctly on legacy-codepage consoles.

#### Scenario: List output is ASCII-only

- GIVEN a discovered skill
- WHEN `ohm skill list` output is captured
- THEN every character's code point is at or below 0x7E

### Requirement: Priority Override

When the same skill name exists in multiple search directories, the loader MUST keep the highest-priority instance (first-wins) and MUST NOT overwrite it; tests MUST cover this.

#### Scenario: Same-name skill across search paths

- GIVEN skill `foo` in `.agents/skills/foo` and `~/.ohm/skills/foo`
- WHEN skills are discovered via the default search paths
- THEN the `.agents/skills` instance is registered
- AND the other is not

### Requirement: Absolute Skill Path

Every discovered skill MUST expose `path` as an absolute path to its skill folder, and tests MUST assert this.

#### Scenario: Discovered skill path is absolute

- GIVEN a skill discovered from a relative search path
- WHEN its `path` is inspected
- THEN `path.is_absolute()` is true
- AND it points at the folder containing `SKILL.md`

### Requirement: Skill Parsing Entry Point

The loader MUST expose skill-file parsing as `SkillLoader.parse_skill_file`; callers and tests MUST use this canonical name, not the archived `parse_skill_md`.

#### Scenario: Canonical parse name is used

- GIVEN the loader module and its tests
- WHEN references to the parsing entry point are checked
- THEN code, callers, and tests use `parse_skill_file`
- AND none use `parse_skill_md`

### Requirement: Defensive Unknown Skill Action

The `ohm skill` handler MUST return exit code 1 with an error message for an unknown `skill_action`, and tests MUST cover this via direct invocation.

#### Scenario: Handler called with unknown action

- GIVEN the handler invoked directly with `skill_action="unknown"`
- WHEN the handler runs
- THEN it prints an "Unknown skill action" message
- AND returns exit code 1

### Requirement: Clean Imports

Skill command, loader, registry, and their tests MUST NOT contain unused imports; `uv run ruff check` MUST report zero F401.

#### Scenario: Ruff reports no unused imports

- GIVEN the skill sources and their tests
- WHEN `uv run ruff check` is run
- THEN no F401 violations are reported

## MODIFIED Requirements

### Requirement: Skill Discovery

The loader MUST discover skills in target directories in priority order:

1. Local workspace `.agents/skills/<skill-name>/`
2. Local workspace `.ohm/skills/<skill-name>/`
3. User home `~/.ohm/skills/<skill-name>/`
4. System shared `~/.gemini/skills/<skill-name>/`

Each skill directory MUST contain a `SKILL.md` file. Metadata MUST be parsed from YAML frontmatter only; Markdown headers MUST NOT be parsed as metadata. A `SKILL.md` without frontmatter MUST fall back to its directory name and a generic description.

(Previously: required "a valid SKILL.md frontmatter or header", implying header parsing; now frontmatter-only with directory-name fallback.)

#### Scenario: Frontmatter skill discovery

- GIVEN a skill directory whose `SKILL.md` has YAML frontmatter
- WHEN discovery runs
- THEN the skill registers with the frontmatter name and description

#### Scenario: Header-only SKILL.md fallback

- GIVEN a `SKILL.md` with no YAML frontmatter
- WHEN discovery runs
- THEN the skill registers with its directory name and a generic description
- AND full file text becomes instructions
