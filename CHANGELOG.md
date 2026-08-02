# Changelog

## v0.1.10 — 2026-08-02

### Added

- **Structured logging bootstrap**: `setup_logging(cfg)` in the new
  `src/ohm/core/observability.py` applies `log_level` (previously parsed but
  dead) and an optional `log_format=json` `JSONFormatter` (timestamp/level/
  logger/message allowlist), wired at the CLI entry point — logs go to stderr
  only, keeping `ohm run` stdout clean. (`#structured-logging-metrics`)
- **In-process metrics registry**: thread-safe `MetricsRegistry` singleton
  accumulating `ohm.metrics.*` counters and histograms
  (`runs.{success,failure}`, `tokens.{total,input,output}`, `cycles.total`,
  `tools.calls`/`tools.{name}`, `latency.ms`, `provider.retry.attempts`,
  `provider.transient.{429,503,5xx}`, `provider.failover`, `cost.usd`),
  honoring `metrics_enabled: false` and the `OHM_METRICS_ENABLED` env var.
  (`#structured-logging-metrics`)
- **Agent/provider telemetry**: `Agent.run`/`stream` and `Provider.retry`/
  `FallbackProvider` record run, token, tool, retry and failover metrics;
  instrumentation never raises or alters results. (`#structured-logging-metrics`)
- **CLI JSON surfaces**: `ohm doctor --json` and `ohm status --json` include a
  nested `metrics` snapshot section. (`#structured-logging-metrics`)

### Changed

- **Metric name alignment**: README metric example renamed
  `ohm.metrics.success` → `ohm.metrics.runs.success` to match the implemented
  naming. (`#structured-logging-metrics`)

## v0.1.9 — 2026-08-02

### Added

- **`ohm skill inspect <name>`**: new subcommand showing a skill's details (name,
  description, absolute path, enabled state, instructions) in the `list` output
  style; exits 0 for a known skill and 1 for an unknown one.
  (`#skills-registry-followups`)

### Changed

- **`Skill.path` is now absolute**: the loader resolves each skill directory via
  `path.parent.resolve()`, making the printed path spec-compliant ("Absolute
  Path") and environment-independent. (`#skills-registry-followups`)
- **ASCII-safe skill output**: `ohm skill list` uses ASCII-safe separators
  instead of non-ASCII glyphs, fixing mojibake in legacy-codepage Windows
  console captures. (`#skills-registry-followups`)
- **Skills registry cleanup**: removed all 11 unused imports (ruff F401) from
  `src/ohm/core/skills/registry.py` and the CLI tests. (`#skills-registry-followups`)

### Fixed

- **Skills registry follow-ups (FU-001..FU-008)**: implemented `inspect`,
  absolute paths, ASCII-safe output, priority-override test, header-only
  `SKILL.md` fallback coverage, `parse_skill_file` naming alignment, defensive
  unknown-action test, and import cleanup. (`#skills-registry-followups`)

## v0.1.8 — 2026-08-01

### Changed

- **TUI command unification (slice 3 — modal presentation)**: the command palette
  (`CommandPalette`) and model selector (`ModelSelector`) are now `ModalScreen`
  subclasses — translucent dim backdrop over the app with a centered dialog,
  matching the session modal presentation. Palette selection uses a
  `dismiss(entry)` contract; push/pop lifecycle unified with the single-toggle
  guard. (`#tui-command-unification`)

## v0.1.7 — 2026-08-01

### Added

- **TUI command unification (slice 2 — widget fixes)**: Ctrl+J inserts a newline
  in the chat input without submitting; Ctrl+M submits like Enter (alias symmetry).
  Command palette gains a live filter Input (`Input.Changed` → `_apply_filter`),
  narrowing by name/description and resetting selection to the first entry.
  (`#tui-command-unification`)
- **Modal single-toggle guard**: repeated F3/F2/Ctrl+K no longer stack modals —
  `_is_open(T)` reads `screen_stack`; toggle modals pop on repeat, push modals
  no-op. (`#tui-command-unification`)
- **Model selector branch navigation**: left/right arrows collapse/expand the
  selected provider's model branch in the expanded set. (`#tui-command-unification`)

### Removed

- Dead `get_filtered_commands` from `CommandInput` and unused `filter_commands`
  from the palette (replaced by `_apply_filter`). (`#tui-command-unification`)

## v0.1.6 — 2026-08-01

### Added

- **TUI command unification (slice 1 — catalog + parity + skills)**: `CommandRegistry`
  is now the single source of truth for the Ctrl+K palette and `/` dropdown via a
  pure `palette_entries(commands, skills)` builder; `CommandKind` enum
  (REAL/DISPLAY_ONLY/TUI_IRRELEVANT), frozen `PaletteEntry`, and `CLI_TUI_MAPPING`
  for the 15 CLI subcommands. Skills are discovered once and appended as
  `/skill <name>` entries in both surfaces. (`#tui-command-unification`)
- **CLI↔TUI parity guard test**: asserts every `register_all` subcommand maps to
  exactly one class and none is lost. (`#tui-command-unification`)

### Removed

- Dead command sources: `GLOBAL_BINDINGS` (`src/ohm/cli/keybindings.py` deleted),
  `FAKE_HOTKEYS`, and `FAKE_COMMANDS` retired from TUI UI paths. (`#tui-command-unification`)

## v0.1.5 — 2026-07-31

### Added

- **Skills Registry & Loader**: `Skill` dataclass, `SkillLoader`, and `SkillRegistry`
  in `src/ohm/core/skills/` — discovery from `~/.ohm/skills` and `.agents/skills`
  with same-name priority override, manifest parsing, and enable/disable management.
  (#skills-registry-loader)
- **`ohm skill list` CLI command**: lists discovered skills with status, wired into
  the command registry. (#skills-registry-loader)
- **Follow-ups tracking**: `docs/follow-ups.md` documents known non-blocking issues
  (FU-001..FU-008) so archived change warnings are not forgotten.

### Changed

- Roadmap: Skills registry marked done in Phase 2 — Core Engine.

## v0.1.3 — 2026-07-31

### Added
- **Widget Input Auto-Resize**: `CommandInput` auto-expands up to 40% of viewport height (max 10 lines) upon multi-line text input or paste (`#widget-input-progress`).
- **Real Token Usage Metrics**: `ContextProgress` bar now displays live token count and percentage of context window used (`#widget-input-progress`).

### Fixed
- **R3-001 (Gemini `base_url` Gating)**: Excluded `base_url` from Gemini model `client_args` to prevent SDK v2 `TypeError`, while maintaining `base_url` propagation through `AgentConfig` for other providers.
- **R4-001 (CLI Gateway Gating)**: `base_url` is now strictly gated by matching CLI provider to prevent leaking proxy URLs and credentials when switching providers via arguments.
- **Session Timestamp Sortability & Test Isolation**: Fixed timestamp sortability test timing and isolated project config override test from `.env` pollution.

## v0.1.2 — 2026-07-30

### Added

- **Session persistence**: Messages now survive TUI exit. Sessions are saved to
  `~/.ohm/sessions/{session_id}.json` with a `last_session.json` pointer for
  fast resume. (#session-management-cycle)
- **Session resume**: `ohm -c` / `ohm --continue` resumes the last session.
  `ohm session continue` sub-action does the same. Messages replay on TUI
  launch with no welcome screen. (#session-resume)
- **Session browser modal**: Press `F3` to browse saved sessions. ↑↓ navigate,
  Enter to select, Esc to dismiss. Shows session ID, started time, messages
  count, and theme. (#session-browser)
- **Exit banner**: Quitting the TUI now prints the OHM logo in ASCII art
  with instructions on how to resume the session.
- **Session browser command**: `/sessions` and `/session list` from the
  TUI command dropdown (`/`) and Ctrl+K modal menu. `/session continue` and
  `/session clear` also wired.
- **Partial response capture**: When the TUI closes while the agent is still
  streaming, the partial response is captured and saved with a note rather
  than lost entirely.
- **OHM_LOGO_VARIANTS**: 6 color variants of the OHM ASCII logo, randomly
  selected on TUI start.

### Fixed

- **UTF-8 encoding on Windows**: Session files now explicitly use `encoding="utf-8"`
  on all `Path.write_text()` calls. Windows defaults to cp1252, which corrupts
  non-ASCII content. Includes `UnicodeDecodeError` safety net in session loading.
- **Session messages lost on exit**: Loading an existing session now properly
  populates `_session_data["messages"]` before save, preventing empty-message
  overwrites on exit.
- **Repo URLs**: All placeholder `your-org` GitHub URLs replaced with the
  real `SinDeployNoHayPizza/ohm` repository.
- **`GOOGLE_API_KEY` → `GEMINI_API_KEY`**: Environment variable renamed across
  the entire codebase to match Google's current naming.
- **Streaming event parsing**: Improved text detection and logging in
  `_stream_agent_response` to handle variable event structures from different
  providers.

### Changed

- Bumped dependencies: deepagents, mcp, pydantic-ai, pydantic-evals,
  pydantic-graph, strands-agents, textual, rich.

### Notes

- Pre-existing test failure: `test_project_overrides_global` — caused by
  `OHM_MODEL=gemini-3.1-flash-lite` in `.env`; unrelated to this release.
- 15 auto-fixable `ruff` lint warnings (unused imports); deferred.
