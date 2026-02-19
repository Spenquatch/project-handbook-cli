# Changelog

## v0.0.11 (2026-02-19)

- `ph help task` now documents `--type` (allowed values + `task_type`↔`session` mapping).
- `ph release status|show|progress` now accept `--release current|vX.Y.Z`.
- `ph sprint plan` slot planning shows slot-scoped features (with “other release features” collapsed).
- Sprint dependency checks accept `depends_on: []` as a valid start node; `FIRST_TASK` can be used multiple times.
- Task templates standardize on `ph task status` and include an absolute evidence-path helper for tools run via `pnpm -C ...`.

