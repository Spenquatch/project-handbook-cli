---
title: PH Spec Contract — parking-lot/archive/external-requests/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/parking-lot/archive/external-requests/`
- Summary: Archived external request parking-lot items (immutable record), organized as one directory per item under the `external-requests/` archive category.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `**/README.md` (archived parking-lot items)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none)
- Overwrite rules:
  - The CLI MUST NOT overwrite archived item `README.md` without explicit `--force`.

## Creation
- Created/updated by:
  - External-request items are archived by moving an existing `parking-lot/external-requests/<EXT-...>/` directory into `parking-lot/archive/external-requests/<EXT-...>/` (manual).
- Non-destructive:
  - Archiving MUST refuse to overwrite an existing destination directory unless `--force` is provided.
  - The CLI MUST NOT rewrite archived markdown bodies (read-only content).

## Required Files and Directories
- Required layout for each archived item directory:
  - `<ITEM_DIR>/README.md`
- Allowed item directory names:
  - `EXT-<YYYYMMDD>-<slug>` (recommended; legacy-parity)
  - Examples MAY use an `EXAMPLE-` prefix.

## Schemas
- `README.md` MUST follow the archived parking-lot schema described in `parking-lot/archive/contract.md` and MUST include:
  - `type: external-requests`
  - `status: archived`
  - required archival metadata keys (`archived_at`, `archived_by_task`, `archived_by_sprint`)
- YAML front matter MAY include additional keys; unknown keys MUST be preserved as content.

## Invariants
- Archived external requests are immutable:
  - the CLI MUST treat all items under this directory as read-only content.

## Validation Rules
- `ph validate` SHOULD enforce:
  - each item directory contains `README.md`
  - `README.md` front matter `type` matches `external-requests`
  - `README.md` front matter `status` is `archived` and archival metadata keys are present

## Examples Mapping
- No `external-requests` archive fixtures are currently provided in `examples/`; archived external requests are created by moving an existing active item directory into this archive category.
