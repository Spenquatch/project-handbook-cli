---
title: PH Spec Contract — ph/backlog/archive/work-items/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: Archived work-item backlog entries (immutable historical record), organized as one directory per work-item.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `WORK-*/README.md` (archived work-item backlog items)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none)
- Overwrite rules:
  - The CLI MUST NOT overwrite archived `WORK-*/README.md` without explicit `--force`.

## Creation
- Created/updated by:
  - `ph init` (creates directory structure).
  - Work-items are archived by moving an existing `ph/backlog/work-items/<WORK-...>/` directory into `ph/backlog/archive/work-items/<WORK-...>/` (manual or future CLI command).
- Non-destructive:
  - Archiving MUST refuse to overwrite an existing destination directory unless `--force` is provided.
  - The CLI MUST NOT rewrite archived markdown bodies.

## Required Files and Directories
- Required layout for each archived work-item directory:
  - `<WORK_DIR>/README.md`
- Allowed item directory names:
  - `WORK-<severity>-<YYYYMMDD>-<HHMM|HHMMSS>[--<slug>]` (recommended)
  - Examples MAY use an `EXAMPLE-` prefix.

## Schemas
- `README.md` MUST include YAML front matter with at least:
  - `title: <string>`
  - `type: work-items`
  - `severity: P0|P1|P2|P3|P4`
  - `status: closed`
  - `created: YYYY-MM-DD`
  - `owner: <string>` (e.g. `unassigned` or `@handle`)
  - `archived_at: <RFC3339 timestamp>`
  - `archived_by_task: <TASK-... | manual>`
  - `archived_by_sprint: <SPRINT-... | manual>`
- Optional keys:
  - `input_type: <string>` (preserves the original intake classification; treated as an opaque string)
- YAML front matter MAY include additional keys; unknown keys MUST be preserved as content.

## Invariants
- Archived work-items MUST be closed:
  - `README.md` front matter `status` MUST be `closed`.
- Archival metadata is required:
  - `archived_at` MUST be present and parseable as an RFC3339 timestamp.

## Validation Rules
- `ph validate` SHOULD enforce:
  - required file presence (`README.md`)
  - required front matter keys and allowed values (severity/status/date formats)
- `ph backlog` commands MUST NOT mutate archived items (read-only).

## Examples Mapping
- `examples/WORK-P4-20260104-1919/` demonstrates a closed, archived work-item `README.md` with required archival metadata fields (and an optional `input_type` field).
