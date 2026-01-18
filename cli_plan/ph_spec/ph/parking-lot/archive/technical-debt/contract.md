---
title: PH Spec Contract — ph/parking-lot/archive/technical-debt/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: Archived technical-debt parking-lot items (immutable record), organized as one directory per item under the `technical-debt/` archive category.

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
  - Technical-debt parking-lot items are archived by moving an existing `ph/parking-lot/technical-debt/<DEBT-...>/` directory into `ph/parking-lot/archive/technical-debt/<DEBT-...>/` (manual or future CLI command).
- Non-destructive:
  - Archiving MUST refuse to overwrite an existing destination directory unless `--force` is provided.
  - The CLI MUST NOT rewrite archived markdown bodies (read-only content).

## Required Files and Directories
- Required layout for each archived item directory:
  - `<ITEM_DIR>/README.md`
- Allowed item directory names:
  - `DEBT-<YYYYMMDD>-<slug>` (recommended; legacy-parity)
  - Examples MAY use an `EXAMPLE-` prefix.

## Schemas
- `README.md` MUST follow the archived parking-lot schema described in `ph/parking-lot/archive/contract.md` and MUST include:
  - `type: technical-debt`
  - `status: archived`
  - required archival metadata keys (`archived_at`, `archived_by_task`, `archived_by_sprint`)
- YAML front matter MAY include additional keys; unknown keys MUST be preserved as content.

## Invariants
- Archived technical-debt parking-lot items are immutable:
  - the CLI MUST treat all items under this directory as read-only content.

## Validation Rules
- `ph validate` SHOULD enforce:
  - each item directory contains `README.md`
  - `README.md` front matter `type` matches `technical-debt`
  - `README.md` front matter `status` is `archived` and archival metadata keys are present

## Examples Mapping
- `examples/DEBT-20260102-standardize-task-directory-slu/README.md` demonstrates an archived technical-debt item with required archival metadata.
