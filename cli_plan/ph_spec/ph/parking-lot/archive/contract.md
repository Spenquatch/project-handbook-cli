---
title: PH Spec Contract — parking-lot/archive/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/parking-lot/archive/`
- Summary: Archived parking lot items, grouped by the same allowed categories as the active parking lot.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `features/**/README.md`
  - `technical-debt/**/README.md`
  - `research/**/README.md`
  - `external-requests/**/README.md`
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none; see `parking-lot/contract.md` for `index.json`)
- Overwrite rules:
  - Parking-lot archive content is treated as immutable; the CLI MUST NOT edit archived item `README.md` bodies.
  - The CLI MAY move entire item directories into/out of `archive/`, but MUST refuse to overwrite an existing destination directory unless `--force` is provided.

## Creation
- Created/updated by:
  - Parking-lot items are archived by moving an existing `parking-lot/<category>/<ITEM-ID>/` directory into `parking-lot/archive/<category>/<ITEM-ID>/` (manual).
- Non-destructive:
  - Archiving MUST refuse to overwrite an existing destination directory unless `--force` is provided.
  - The CLI MUST NOT rewrite archived markdown bodies (read-only content).

## Required Files and Directories
- Category directories are created on demand and MAY be absent when empty.
- Allowed categories (authoritative): `features`, `technical-debt`, `research`, `external-requests`

## Schemas
- Each archived item directory MUST contain:
  - `<ITEM_DIR>/README.md`
- `README.md` MUST include YAML front matter with at least:
  - `title: <string>`
  - `type: features|technical-debt|research|external-requests` (MUST match the category directory)
  - `status: archived`
  - `created: YYYY-MM-DD`
  - `owner: <string>` (e.g. `unassigned` or `@handle`)
  - `tags: [<string>, ...]` (may be empty)
  - `archived_at: <RFC3339 timestamp>`
  - `archived_by_task: <TASK-... | manual>`
  - `archived_by_sprint: <SPRINT-... | manual>`
- YAML front matter MAY include additional keys; unknown keys MUST be preserved as content.

## Invariants
- Parking-lot archive content is treated as immutable:
  - archived item directories MUST be treated as read-only content.
  - archived items MUST NOT be modified by `ph parking` commands (read-only).

## Validation Rules
- `allowed_categories` MUST match `process/checks/validation_rules.json` (`parking_lot.allowed_categories`).
- `ph validate` SHOULD enforce:
  - archived item directories contain `README.md`
  - archived item `README.md` front matter includes `status: archived` and required archival metadata fields
  - archived items are excluded from `parking-lot/index.json` (catalog contains only active parking-lot items)

## Examples Mapping
- `examples/research/RES-20251230-process-fix-session-end-index-/README.md` demonstrates an archived research item with required archival metadata.
- `examples/technical-debt/DEBT-20260102-standardize-task-directory-slu/README.md` demonstrates an archived technical-debt item with required archival metadata.
