---
title: PH Spec Contract — backlog/archive/wildcards/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/backlog/archive/wildcards/`
- Summary: Archived wildcard backlog entries (immutable historical record), organized as one directory per wildcard item.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `WILD-*/README.md` (archived wildcard backlog items)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none)
- Overwrite rules:
  - The CLI MUST NOT overwrite archived `WILD-*/README.md` without explicit `--force`.

## Creation
- Created/updated by:
  - Wildcard items are archived by moving an existing `backlog/wildcards/<WILD-...>/` directory into `backlog/archive/wildcards/<WILD-...>/` (manual or via task tooling).
- Non-destructive:
  - Archiving MUST refuse to overwrite an existing destination directory unless `--force` is provided.
  - The CLI MUST NOT rewrite archived markdown bodies.

## Required Files and Directories
- Required layout for each archived wildcard item directory:
  - `<WILD_DIR>/README.md`
- Allowed item directory names:
  - `WILD-<severity>-<YYYYMMDD>-<HHMM|HHMMSS>[--<slug>]` (recommended)
  - Examples MAY use an `EXAMPLE-` prefix.

## Schemas
- `README.md` MUST include YAML front matter with at least:
  - `title: <string>`
  - `type: wildcards`
  - `severity: P0|P1|P2|P3|P4`
  - `status: closed`
  - `created: YYYY-MM-DD`
  - `owner: <string>` (e.g. `unassigned` or `@handle`)
  - `input_type: <string>` (optional; preserved if present)
  - `sprint: <SPRINT-... | null>` (optional; present if assignment metadata was recorded)
  - `archived_at: <RFC3339 timestamp>`
  - `archived_by_task: <TASK-... | manual>`
  - `archived_by_sprint: <SPRINT-... | manual>`
- YAML front matter MAY include additional keys; unknown keys MUST be preserved as content.

## Invariants
- Archived wildcard entries MUST be closed:
  - `README.md` front matter `status` MUST be `closed`.
- Archival metadata is required:
  - `archived_at` MUST be present and parseable as an RFC3339 timestamp.

## Validation Rules
- `ph validate` SHOULD enforce:
  - required file presence (`README.md`)
  - required front matter keys and allowed values (severity/status/date formats)
- `ph backlog` commands MUST NOT mutate archived items (read-only).

## Examples Mapping
- `examples/WILD-P2-20260101-2107/` demonstrates a closed, archived wildcard `README.md` with required archival metadata fields.
