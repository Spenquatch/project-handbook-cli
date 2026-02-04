---
title: PH Spec Contract — sprints/archive/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/sprints/archive/`
- Summary: Archived sprints and their immutable artifacts, plus an `index.json` catalog of archived sprint metadata.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `YYYY/SPRINT-*/plan.md` body
  - `YYYY/SPRINT-*/tasks/**` task docs
  - `YYYY/SPRINT-*/retrospective.md` body
  - `YYYY/SPRINT-*/burndown.md` (may include human commentary)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - `index.json` (catalog of archived sprint metadata; MAY be regenerated from the filesystem)
- Overwrite rules:
  - The CLI MUST NOT overwrite an existing archived sprint directory without explicit `--force`.
- Mutability:
  - CLI-managed: `index.json` updates.
  - Human-edited: post-hoc notes inside archived sprint markdowns (front matter MUST be preserved).
  - Archived sprint directories SHOULD be treated as immutable records; `ph` MUST NOT modify archived sprint contents except as part of an explicit repair operation (e.g. a future `--force`/`--repair` command).

## Creation
- Created/updated by:
  - `ph sprint close` (moves the current sprint into `sprints/archive/YYYY/<sprint-id>/`, updates `index.json`)
  - `ph sprint archive [--sprint SPRINT-...]` (moves the specified sprint into `sprints/archive/YYYY/<sprint-id>/`, updates `index.json`)
  - `pnpm make -- sprint-close` (moves the current sprint into `sprints/archive/YYYY/<sprint-id>/`, updates `index.json`)
  - `pnpm make -- sprint-archive [sprint=SPRINT-...]` (moves the specified sprint into `sprints/archive/YYYY/<sprint-id>/`, updates `index.json`)
- Non-destructive: MUST refuse to overwrite an existing archived sprint directory.

## Required Files and Directories
- Required files:
  - `index.json`
- Archived sprint directory layout (canonical):
  - Date/ISO-week ids:
    - `YYYY/SPRINT-<...>/`
      - `plan.md`
      - `tasks/` (may be empty)
      - `retrospective.md`
      - `burndown.md`
  - Sequence ids:
    - `SEQ/SPRINT-SEQ-####/`
      - `plan.md`
      - `tasks/` (may be empty)
      - `retrospective.md`
      - `burndown.md`

## Schemas
- `index.json` MUST be a JSON object with:
  - `sprints`: array of objects containing at least:
    - `sprint` (string; sprint id `SPRINT-...`)
    - `archived_at` (string; RFC3339 timestamp, UTC preferred)
    - `path` (string; path relative to `PH_ROOT/` such as `sprints/archive/2026/SPRINT-2026-01-09`)
    - `start` (string; `YYYY-MM-DD`)
    - `end` (string; `YYYY-MM-DD`)
- `YYYY/SPRINT-*/plan.md` MUST be Markdown with YAML front matter containing at least:
  - `type: sprint-plan`
  - `sprint: SPRINT-...` (matching the directory name)
- `YYYY/SPRINT-*/retrospective.md` MUST be Markdown with YAML front matter containing at least:
  - `type: sprint-retrospective`
  - `sprint: SPRINT-...` (matching the directory name)
- `YYYY/SPRINT-*/burndown.md` MUST be Markdown with YAML front matter containing at least:
  - `type: sprint-burndown`
  - `sprint: SPRINT-...` (matching the directory name)
- YAML front matter MAY include additional keys; unknown keys MUST be preserved.

## Invariants
- `ph sprint close` MUST:
  - create `retrospective.md` in the sprint directory before archiving, and
  - ensure a final `burndown.md` exists in the sprint directory before archiving.
- On archive, tooling SHOULD rewrite any `sprints/current/tasks/...` links into immutable archived paths (to avoid historical tasks pointing at a moving `current` pointer). This is legacy behavior in `process/automation/sprint_manager.py` (via `process/automation/link_rewriter.py`).
- On archive, `sprints/current` MUST NOT be left pointing at a non-existent sprint directory.
- For date/ISO-week ids, the sprint directory year partition `YYYY/` MUST equal the year segment in the sprint id (`SPRINT-YYYY-...`).
- Every entry in `index.json.sprints[*].path` MUST be under `sprints/archive/`.

## Validation Rules
- `index.json` MUST exist and be valid JSON.
- Every sprint referenced by `index.json` MUST exist at the referenced `path`.
- For every archived sprint directory `YYYY/SPRINT-*`:
  - `plan.md`, `retrospective.md`, and `burndown.md` MUST exist
  - these files MUST satisfy the front matter requirements above

## Examples Mapping
- `examples/index.json` demonstrates the `index.json` shape and how `path` values point at `sprints/archive/YYYY/SPRINT-...` entries.
- `examples/2026/SPRINT-2026-01-09/plan.md` demonstrates a valid sprint plan front matter (`type: sprint-plan`, `sprint: ...`).
- `examples/2026/SPRINT-2026-01-09/retrospective.md` demonstrates a valid sprint retrospective front matter (`type: sprint-retrospective`, `sprint: ...`).
- `examples/2026/SPRINT-2026-01-09/burndown.md` demonstrates a valid sprint burndown front matter (`type: sprint-burndown`, `sprint: ...`).
