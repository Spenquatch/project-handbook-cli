---
title: PH Spec Contract — ph/parking-lot/archive/features/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: Archived feature parking-lot items (immutable record), organized as one directory per item under the `features/` archive category.

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
  - `ph init` (creates directory structure).
  - Feature parking-lot items are archived by moving an existing `ph/parking-lot/features/<FEAT-...>/` directory into `ph/parking-lot/archive/features/<FEAT-...>/` (manual or future CLI command).
- Non-destructive:
  - Archiving MUST refuse to overwrite an existing destination directory unless `--force` is provided.
  - The CLI MUST NOT rewrite archived markdown bodies (read-only content).

## Required Files and Directories
- Required layout for each archived item directory:
  - `<ITEM_DIR>/README.md`
- Allowed item directory names:
  - `FEAT-<YYYYMMDD>-<slug>` (recommended; legacy-parity)
  - Examples MAY use an `EXAMPLE-` prefix.

## Schemas
- `README.md` MUST follow the archived parking-lot schema described in `ph/parking-lot/archive/contract.md` and MUST include:
  - `type: features`
  - `status: archived`
  - required archival metadata keys (`archived_at`, `archived_by_task`, `archived_by_sprint`)
- YAML front matter MAY include additional keys; unknown keys MUST be preserved as content.

## Invariants
- Archived feature parking-lot items are immutable:
  - the CLI MUST treat all items under this directory as read-only content.

## Validation Rules
- `ph validate` SHOULD enforce:
  - each item directory contains `README.md`
  - `README.md` front matter `type` matches `features`
  - `README.md` front matter `status` is `archived` and archival metadata keys are present

## Examples Mapping
- No `features` archive fixtures are currently provided in `examples/`; archived feature parking-lot items are created by moving an existing active item directory into this archive category.
