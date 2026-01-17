---
title: PH Spec Contract — ph/parking-lot/archive/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: Archived parking lot items, grouped by the same allowed categories as the active parking lot.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `features/**/README.md`
  - `technical-debt/**/README.md`
  - `research/**/README.md`
  - `external-requests/**/README.md`
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none; see `ph/parking-lot/contract.md` for `index.json`)
- Overwrite rules:
  - Parking-lot archive content is treated as immutable; the CLI MUST NOT edit archived item `README.md` bodies.
  - The CLI MAY move entire item directories into/out of `archive/`, but MUST refuse to overwrite an existing destination directory unless `--force` is provided.

## Creation
- Created/updated by: (TBD; `ph ...` commands)
- Non-destructive: MUST NOT overwrite user-owned files without explicit flags

## Required Files and Directories
- Required directories:
  - `features/`
  - `technical-debt/`
  - `research/`
  - `external-requests/`
- Allowed categories (authoritative): `features`, `technical-debt`, `research`, `external-requests`

## Schemas
- (TBD; file formats, required keys, constraints)

## Invariants
- (TBD)

## Validation Rules
- `allowed_categories` MUST match `process/checks/validation_rules.json` (`parking_lot.allowed_categories`).

## Examples Mapping
- (TBD; example fixtures that demonstrate this contract)
