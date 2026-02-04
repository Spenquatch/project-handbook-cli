---
title: PH Spec Contract — backlog/wildcards/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/backlog/wildcards/`
- Summary: Active wildcard backlog entries (P0–P4), organized as one directory per wildcard item.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `WILD-*/README.md` (one directory per wildcard backlog item)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none; see `ph/backlog/contract.md` for `index.json`)
- Overwrite rules:
  - The CLI MUST NOT overwrite `WILD-*/README.md` without explicit `--force`.

## Creation
- Created/updated by:
  - `ph backlog add --type wildcards ...` (creates a new wildcard item directory + `README.md`).
  - `pnpm make -- backlog-add type=wildcards ...` (creates a new wildcard item directory + `README.md`).
- Non-destructive:
  - `ph backlog add` MUST refuse to overwrite an existing `<WILD_DIR>/` unless `--force` is provided.

## Required Files and Directories
- Required layout for each wildcard item directory:
  - `<WILD_DIR>/README.md`
- Allowed item directory names:
  - `WILD-<severity>-<YYYYMMDD>-<HHMM|HHMMSS>[--<slug>]` (recommended)
  - Examples MAY use an `EXAMPLE-` prefix.

## Schemas
- `README.md` MUST include YAML front matter with at least:
  - `title: <string>`
  - `type: wildcards`
  - `input_type: <string>` (legacy; typically `wildcards`)
  - `severity: P0|P1|P2|P3|P4`
  - `status: <string>` (legacy default: `open`)
  - `created: YYYY-MM-DD`
  - `owner: <string>` (e.g. `unassigned` or `@handle`)
- `README.md` MUST NOT include archival metadata keys (these are reserved for archived items under `ph/backlog/archive/wildcards/`):
  - `archived_at`
  - `archived_by_task`
  - `archived_by_sprint`
- YAML front matter MAY include additional keys; unknown keys MUST be preserved as content.

## Invariants
- Wildcard item directories MUST contain exactly one primary `README.md`.

## Validation Rules
- `ph validate` SHOULD enforce:
  - required file presence (`README.md`)
  - required front matter keys and allowed values (severity/status/date formats)
  - archival keys are forbidden under non-archive items
- `ph backlog` commands MUST NOT rewrite markdown bodies unless explicitly requested via a dedicated update command/flag.

## Examples Mapping
- `examples/WILD-P2-20260103-2109/` demonstrates a wildcard `README.md` with the required front matter fields.
