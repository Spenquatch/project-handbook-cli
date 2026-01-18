---
title: PH Spec Contract — ph/parking-lot/technical-debt/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: Active technical-debt parking-lot items (not yet promoted into roadmap/backlog), organized as one directory per item.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `**/README.md` (one directory per parking-lot item)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none; see `ph/parking-lot/contract.md` for `index.json`)
- Overwrite rules:
  - The CLI MUST NOT overwrite item `README.md` without explicit `--force`.

## Creation
- Created/updated by:
  - `ph init` (creates directory structure).
  - `ph parking add --type technical-debt ...` (creates a new item directory + `README.md` and updates `ph/parking-lot/index.json`).
- Non-destructive:
  - `ph parking add` MUST refuse to overwrite an existing `<ITEM_DIR>/` unless `--force` is provided.
  - The CLI MUST NOT overwrite item `README.md` content without explicit `--force`.

## Required Files and Directories
- Required layout for each item directory:
  - `<ITEM_DIR>/README.md`
- Allowed item directory names:
  - `DEBT-<YYYYMMDD>-<slug>` (recommended; legacy-parity)
  - Examples MAY use an `EXAMPLE-` prefix.

## Schemas
- `README.md` MUST follow the parking-lot item schema described in `ph/parking-lot/contract.md` and MUST include:
  - `type: technical-debt`
  - `status: parking-lot`
- YAML front matter MAY include additional keys; unknown keys MUST be preserved as content.

## Invariants
- Each item directory MUST contain exactly one primary `README.md`.

## Validation Rules
- `ph validate` SHOULD enforce:
  - each item directory contains `README.md`
  - `README.md` front matter `type` matches `technical-debt`
  - `README.md` front matter `status` is `parking-lot`
  - archival metadata keys are forbidden under non-archive items:
    - `archived_at`
    - `archived_by_task`
    - `archived_by_sprint`

## Examples Mapping
- `examples/DEBT-20260102-standardize-task-directory-slu/README.md` demonstrates a technical-debt parking-lot item `README.md` with required front matter keys.
