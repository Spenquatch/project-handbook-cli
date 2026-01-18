---
title: PH Spec Contract — ph/backlog/work-items/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: Active work-item backlog entries (P0–P4), organized as one directory per work-item.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `WORK-*/README.md` (one directory per work-item backlog item)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none; see `ph/backlog/contract.md` for `index.json`)
- Overwrite rules:
  - The CLI MUST NOT overwrite `WORK-*/README.md` without explicit `--force`.

## Creation
- Created/updated by:
  - `ph init` (creates directory structure).
  - `ph backlog add --type work-items ...` (creates a new work-item directory + `README.md`).
- Non-destructive:
  - `ph backlog add` MUST refuse to overwrite an existing `<WORK_DIR>/` unless `--force` is provided.

## Required Files and Directories
- Required layout for each work-item directory:
  - `<WORK_DIR>/README.md`
- Allowed item directory names:
  - `WORK-<severity>-<YYYYMMDD>-<HHMM|HHMMSS>[--<slug>]` (recommended)
  - Examples MAY use an `EXAMPLE-` prefix.

## Schemas
- `README.md` MUST include YAML front matter with at least:
  - `title: <string>`
  - `type: work-items`
  - `severity: P0|P1|P2|P3|P4`
  - `status: open|closed`
  - `created: YYYY-MM-DD`
  - `owner: <string>` (e.g. `unassigned` or `@handle`)
- `README.md` MUST NOT include archival metadata keys (these are reserved for archived items under `ph/backlog/archive/work-items/`):
  - `archived_at`
  - `archived_by_task`
  - `archived_by_sprint`
- Optional keys:
  - `input_type: <string>` (preserves the original intake classification; treated as an opaque string)
- YAML front matter MAY include additional keys; unknown keys MUST be preserved as content.

## Invariants
- Work-item directories MUST contain exactly one primary `README.md`.

## Validation Rules
- `ph validate` SHOULD enforce:
  - required file presence (`README.md`)
  - required front matter keys and allowed values (severity/status/date formats)
  - archival keys are forbidden under non-archive items
- `ph backlog` commands MUST NOT rewrite markdown bodies unless explicitly requested via a dedicated update command/flag.

## Examples Mapping
- `examples/WORK-P2-20260106-213751/` demonstrates a work-item `README.md` with the required front matter fields (and an optional `input_type` field).
