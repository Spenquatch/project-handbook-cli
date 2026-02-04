---
title: PH Spec Contract — backlog/bugs/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/backlog/bugs/`
- Summary: Active bug backlog entries (P0–P4), organized as one directory per bug item.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `BUG-*/README.md` (one directory per bug backlog item)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none; see `ph/backlog/contract.md` for `index.json`)
- Overwrite rules:
  - The CLI MUST NOT overwrite `BUG-*/README.md` without explicit `--force`.

## Creation
- Created/updated by:
  - `pnpm make -- backlog-add type=bugs ...` (creates a new bug item directory + `README.md`).
    - Compatibility: the underlying manager normalizes `bug|bugs` → `bugs`.
  - `pnpm make -- backlog-triage issue=<BUG-...>` (MAY create `triage.md` for analysis; primarily used for P0s).
- Non-destructive:
  - `ph backlog add` MUST refuse to overwrite an existing `<BUG_DIR>/` unless `--force` is provided.
  - `ph backlog triage` MUST refuse to overwrite an existing `triage.md` unless `--force` is provided.

## Required Files and Directories
- Required layout for each bug item directory:
  - `<BUG_DIR>/README.md`
- Optional files:
  - `<BUG_DIR>/triage.md` (P0 analysis template; may be absent; does not require front matter)
- Allowed item directory names:
  - `BUG-<severity>-<YYYYMMDD>-<HHMM|HHMMSS>[--<slug>]` (recommended)
  - Examples MAY use an `EXAMPLE-` prefix.

## Schemas
- `README.md` MUST include YAML front matter with at least:
  - `title: <string>`
  - `type: bugs`
  - `input_type: <string>` (legacy; typically `bugs`)
  - `severity: P0|P1|P2|P3|P4`
  - `status: <string>` (legacy default: `open`)
  - `created: YYYY-MM-DD`
  - `owner: <string>` (e.g. `unassigned` or `@handle`)
- `README.md` MUST NOT include archival metadata keys (these are reserved for archived items under `ph/backlog/archive/bugs/`):
  - `archived_at`
  - `archived_by_task`
  - `archived_by_sprint`
- `triage.md` is free-form Markdown and MAY omit front matter (it is treated as a working analysis doc/template).
- YAML front matter MAY include additional keys; unknown keys MUST be preserved as content.

## Invariants
- Bug item directories MUST contain exactly one primary `README.md`.
- If `triage.md` exists, it MUST be a regular file (not a directory).

## Validation Rules
- `ph validate` SHOULD enforce:
  - required file presence (`README.md`)
  - required front matter keys and allowed values (severity/status/date formats)
  - P0 triage: if `severity: P0`, `triage.md` SHOULD exist (warning if missing)
  - archival keys are forbidden under non-archive items
- `ph backlog list` and `ph backlog stats` MAY use these directories as inputs; they MUST NOT rewrite markdown bodies.

## Examples Mapping
- `examples/EXAMPLE-BUG-P0-20250922-1144/` demonstrates:
  - a bug `README.md` with required keys,
  - an optional `triage.md` analysis template.
