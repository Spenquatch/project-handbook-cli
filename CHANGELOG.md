# Changelog

## v0.0.19 (2026-02-20)

- System-scope routing/enforcement is now opt-in (disabled by default); new handbooks no longer seed
  `process/automation/system_scope_config.json`.
- Adds `ph process refresh --disable-system-scope-enforcement` to turn off enforcement in existing repos and delete the
  system-scope config file.
- Adds `ph reset --include-system` and `ph reset-smoke --include-system` to optionally wipe `.project-handbook/system/**`
  (default behavior preserves system scope).
- Removes `ph migrate system-scope`.
- Replaces `handbook/automation` lane examples with `ops/automation`.

## v0.0.18 (2026-02-20)

- `ph validate` now enforces expected structure for the current sprint plan (required headings + order) and flags
  “heading pasted into a list item” formatting drift.

## v0.0.17 (2026-02-19)

- Adds `ph next` (one-screen current context + ranked next actions), with `--format text|json`.

## v0.0.16 (2026-02-19)

- `ph parking review` is now non-interactive (no prompts) and supports `--format text|json`.
- `ph` now prints a shell-safe `cd -- …` hint after location paths for task/feature/release creation.

## v0.0.15 (2026-02-19)

- No functional changes; fixes ruff `E501` line-length lint failures in CLI/task output code and tests.

## v0.0.14 (2026-02-19)

- Post-hook validation now runs `validate --quick` only for selected mutating commands/subcommands (and never for read-only/reporting commands).
- Post-hook validation output is now errors-only and written to stderr (stdout stays clean for JSON/table output).
- `ph sprint plan` now auto-scaffolds a required `task_type: sprint-gate` task for new/forced-regenerated sprints (gate exists Day 0; expected to close last).

## v0.0.13 (2026-02-19)

- Adds `.project-handbook/releases/current.txt` as a tooling-friendly pointer to the active release version (symlink remains).
- Release readiness is now **gate-first**; feature completion is labeled as historical context to avoid misleading “ready” states.

## v0.0.12 (2026-02-19)

- **Breaking**: `ph release draft --format json` output keys renamed and wrapped in a self-describing envelope:
  - Adds: `type=release-draft`, `schema_version=1`, `commands`
  - Renames:
    - `base` → `base_release`
    - `candidates` → `candidate_features`
    - `suggested_assignments` → `suggested_features`
    - `operator_question_pack` → `operator_questions`
    - `suggested_add_feature_commands` → `commands.release_add_feature`
    - `suggested_research_discovery_tasks` → `commands.research_discovery`
- Adds `ph release draft --schema` to print the JSON schema for the payload.
- `ph help release` now documents the JSON payload shape and points to `--schema`.

## v0.0.11 (2026-02-19)

- `ph help task` now documents `--type` (allowed values + `task_type`↔`session` mapping).
- `ph release status|show|progress` now accept `--release current|vX.Y.Z`.
- `ph sprint plan` slot planning shows slot-scoped features (with “other release features” collapsed).
- Sprint dependency checks accept `depends_on: []` as a valid start node; `FIRST_TASK` can be used multiple times.
- Task templates standardize on `ph task status` and include an absolute evidence-path helper for tools run via `pnpm -C ...`.
