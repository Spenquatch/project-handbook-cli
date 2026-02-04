---
title: PH Spec Contract — parking-lot/archive/research/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/parking-lot/archive/research/`
- Summary: Archived research parking-lot items (immutable record), organized as one directory per item under the `research/` archive category.

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
  - Research parking-lot items are archived by moving an existing `parking-lot/research/<RES-...>/` directory into `parking-lot/archive/research/<RES-...>/` (manual).
- Non-destructive:
  - Archiving MUST refuse to overwrite an existing destination directory unless `--force` is provided.
  - The CLI MUST NOT rewrite archived markdown bodies (read-only content).

## Required Files and Directories
- Required layout for each archived item directory:
  - `<ITEM_DIR>/README.md`
- Allowed item directory names:
  - `RES-<YYYYMMDD>-<slug>` (recommended; legacy-parity)
  - Examples MAY use an `EXAMPLE-` prefix.

## Schemas
- `README.md` MUST follow the archived parking-lot schema described in `parking-lot/archive/contract.md` and MUST include:
  - `type: research`
  - `status: archived`
  - required archival metadata keys (`archived_at`, `archived_by_task`, `archived_by_sprint`)
- YAML front matter MAY include additional keys; unknown keys MUST be preserved as content.

## Invariants
- Archived research parking-lot items are immutable:
  - the CLI MUST treat all items under this directory as read-only content.

## Validation Rules
- `ph validate` SHOULD enforce:
  - each item directory contains `README.md`
  - `README.md` front matter `type` matches `research`
  - `README.md` front matter `status` is `archived` and archival metadata keys are present

## Examples Mapping
- `examples/RES-20251230-process-fix-session-end-index-/README.md` demonstrates an archived research item with required archival metadata.
