# Archive Report: Structured Logging and Metrics

- **Change**: `structured-logging-metrics`
- **Branch**: `feature/structured-logging-metrics` (HEAD `b4d5a02`)
- **Archived**: 2026-08-02 → `openspec/changes/archive/2026-08-02-structured-logging-metrics/`
- **Artifact store mode**: openspec (file-based) + Engram (`sdd/structured-logging-metrics/archive-report`)
- **SDD pipeline**: explore → propose → spec → design → tasks → apply → verify → **archive** (cycle complete)

## Classification

**COMPLETED — Verify PASS, no blockers, no CRITICAL, no WARNING findings.**

- Verify verdict: `pass` (`openspec/changes/archive/2026-08-02-structured-logging-metrics/verify-report.md`)
- Blockers: 0 | Critical findings: 0 | Warnings: 0 | Suggestions: 3 (non-blocking, tracked below)
- Requirements: 10/10 compliant (OBS-1..OBS-9 = 17 scenarios + PC-1 = 3 scenarios → 20/20 scenarios)
- Tests: 236 passed / 0 failed / 0 skipped (`uv run pytest`, exit 0); ruff clean on 7 changed source files
- TDD: 22/22 tasks complete (all `[x]` in archived `tasks.md`), strict TDD 6/6 checks passed
- Runtime smoke: `ohm doctor --json` / `ohm status --json` include nested `metrics` section; stdout purity guard passes

### Gates

| Gate | Result | Evidence |
|------|--------|----------|
| Task completion | ✅ PASS | `tasks.md` 22/22 `[x]` (1.1–5.2); no stale unchecked tasks |
| Verify verdict | ✅ PASS | 0 blockers, 0 CRITICAL; verdict `pass` |
| Native review receipt | N/A | Change predates the native review system (no `review/{transaction,ledger,receipt,gate-context}` artifacts); verify-report is the gate evidence |
| Action context | ✅ PASS | Mode `openspec`; no workspace-planning mode; operations confined to repo root |
| Merge destructiveness | ✅ PASS | Provider-config merge is purely additive (1 requirement appended, 4 preserved); observability no-op |

## Summary of the Change

Delivered OHM's first real observability layer with **zero new dependencies**:

- **Logging bootstrap** (`src/ohm/core/observability.py` + `cli/main.py`): `setup_logging(cfg)` applies `log_level` at CLI/TUI entry (OBS-1), optional JSON formatter with an allowlist-only serializer (OBS-2, OBS-8), stderr-only handler preserving the `ohm run` stdout purity contract (OBS-3).
- **Metrics registry**: Lock-guarded `MetricsRegistry` with README-named `ohm.metrics.*` counters/histograms, `metrics_enabled` opt-out, `cost.usd = 0.0` slot (OBS-4, OBS-7); instrumentation in `Agent.run/stream` (OBS-5) and `Provider.retry`/`FallbackProvider` (OBS-6) is failure-isolated and never alters results.
- **CLI surfaces**: nested `metrics` snapshot in `ohm doctor --json` and `ohm status --json` (OBS-9, D4).
- **Config**: `log_format` + `metrics_enabled` keys, `OHM_LOG_LEVEL` stays authoritative, validation fallbacks with warnings (PC-1).
- **Docs**: README.md/README.es.md metric-name fix (`ohm.metrics.runs.success`), CHANGELOG v0.1.10.
- Deferred to Stage 2 (per proposal/spec): `ohm observe --export`, correlation IDs, real cost computation, `self.log()` re-wiring.

## Spec Merge Actions

| Domain | Action | Details |
|--------|--------|---------|
| observability | Verified (no-op) | Canonical `openspec/specs/observability/spec.md` is byte-identical to the delta written during the spec phase — OBS-1..OBS-9 (17 scenarios) complete and stable. No merge needed. |
| provider-config | Updated (+1 requirement) | Appended `### Requirement: Observability Configuration Keys (PC-1)` (3 scenarios) to `openspec/specs/provider-config/spec.md`; preserved the 4 existing requirements (Provider Resolution, Env Mapping, AgentConfig Merged, Availability Discovery). Added provenance note to the status header. |

## Artifact Traceability (archived)

| Artifact | Path (archived) | Notes |
|----------|-----------------|-------|
| Exploration | `exploration.md` | Requirement clarification |
| Proposal | `proposal.md` | Intent, scope, approach |
| Change-level spec | `spec.md` | OBS-1..OBS-9 requirements + scenarios |
| Delta specs | `specs/observability/spec.md`, `specs/provider-config/spec.md` | OBS + PC-1 deltas |
| Design | `design.md` | D1–D6 decisions, interfaces, contracts |
| Tasks | `tasks.md` | 22/22 `[x]`, work-unit forecast S1–S4 |
| Apply progress | `apply-progress.md` | TDD cycle evidence, work-unit evidence, files changed |
| Verify report | `verify-report.md` | PASS, 20/20 scenarios, 236 tests |

Engram mirror: `sdd/structured-logging-metrics/archive-report` (this report).

## Follow-ups Logged

Logged to `docs/follow-ups.md` (Open):

- **FU-017** (SUGGESTION): `src/ohm/commands/run.py:48` echoes `[run] prompt: {args.prompt}` to stderr — prompt content visible on stderr under DEBUG sessions. Pre-existing UI print (not a log record; stdout purity unaffected; OBS-8 governs log records only). Verify suggestion 2; documented in design.md open questions. Proposed fix: redact prompt echo in a future change.
- **FU-018** (SUGGESTION): `ohm.metrics.cost.usd` is a fixed `0.0` slot — no cost source in Stage 1 (OBS-7, D6). Proposed fix: compute real cost from `PROVIDER_CATALOG` once pricing data exists (Stage 2).

## Verify Suggestions (non-blocking, recorded here)

1. `apply-progress.md` "Files Changed" table misattributes per-class test counts (`TestLoggingBootstrap (9), TestJsonFormatterAllowlist (1)`; actual 8 + 2). Total (24) and per-work-unit counts correct — cosmetic only; remediation deferred because the file is now a frozen audit trail (not reused).
2. `run.py:48` stderr prompt echo — see FU-017.
3. Baseline safety-net "212" verified by arithmetic (236 − 24 new, all in one new file), not re-executed against pre-change tree — internally consistent.

## Verification of Archive

- [x] Main specs updated: provider-config PC-1 merged; observability verified identical
- [x] Change folder moved: `openspec/changes/archive/2026-08-02-structured-logging-metrics/`
- [x] Archive contains all artifacts (exploration, proposal, spec, specs/, design, tasks, apply-progress, verify-report, archive-report)
- [x] Archived `tasks.md` has no unchecked implementation tasks (22/22 `[x]`)
- [x] Active changes directory no longer contains this change
- [x] Docs follow-ups updated (FU-017, FU-018 added)

## SDD Cycle Complete

The change has been fully planned, implemented, verified, and archived. Ready for the next change.
