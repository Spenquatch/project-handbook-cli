---
title: PH Spec Contract — ph/backlog/archive/bugs/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: Archived bug backlog entries (immutable historical record), organized as one directory per bug item.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `BUG-*/README.md` (archived bug backlog items)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none)
- Overwrite rules:
  - The CLI MUST NOT overwrite archived `BUG-*/README.md` without explicit `--force`.

## Creation
- Created/updated by:
  - `ph init` (creates directory structure).
  - Bug items are archived by moving an existing `ph/backlog/bugs/<BUG-...>/` directory into `ph/backlog/archive/bugs/<BUG-...>/` (manual or future CLI command).
- Non-destructive:
  - Archiving MUST refuse to overwrite an existing destination directory unless `--force` is provided.
  - The CLI MUST NOT rewrite archived markdown bodies.

## Required Files and Directories
- Required layout for each archived bug item directory:
  - `<BUG_DIR>/README.md`
- Optional files:
  - `<BUG_DIR>/triage.md` (P0 analysis template; may be absent; does not require front matter)
- Allowed item directory names:
  - `BUG-<severity>-<YYYYMMDD>-<HHMM>[--<slug>]` (recommended)
  - Examples MAY use an `EXAMPLE-` prefix.

## Schemas
- `README.md` MUST include YAML front matter with at least:
  - `title: <string>`
  - `type: bugs`
  - `severity: P0|P1|P2|P3|P4`
  - `status: closed`
  - `created: YYYY-MM-DD`
  - `owner: <string>` (e.g. `unassigned` or `@handle`)
  - `archived_at: <RFC3339 timestamp>`
  - `archived_by_task: <TASK-... | manual>`
  - `archived_by_sprint: <SPRINT-... | manual>`
- `triage.md` is free-form Markdown and MAY omit front matter (it is treated as a working analysis doc/template).

## Invariants
- Archived bug entries MUST be closed:
  - `README.md` front matter `status` MUST be `closed`.
- Archival metadata is required:
  - `archived_at` MUST be present and parseable as an RFC3339 timestamp.

## Validation Rules
- `ph validate` SHOULD enforce:
  - required file presence (`README.md`)
  - required front matter keys and allowed values (severity/status/date formats)
  - `triage.md` is allowed without front matter
- `ph backlog` commands MUST NOT mutate archived items (read-only).

## Examples Mapping
- `examples/EXAMPLE-BUG-P0-20250922-1144/` demonstrates:
  - a closed, archived bug `README.md` with archival metadata fields,
  - an optional `triage.md` analysis template.
