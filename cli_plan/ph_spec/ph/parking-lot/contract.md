---
title: PH Spec Contract — ph/parking-lot/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: A categorized parking lot for ideas/requests that are not yet promoted into the roadmap/backlog.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `features/**/README.md`
  - `technical-debt/**/README.md`
  - `research/**/README.md`
  - `external-requests/**/README.md`
  - `archive/**/README.md` (archived items; treated as immutable content)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - `index.json` (catalog of parking-lot items and metadata)
- Overwrite rules:
  - The CLI MAY regenerate `index.json`.
  - The CLI MUST NOT overwrite any `README.md` content without explicit `--force`.

## Creation
- Created/updated by: (TBD; `ph ...` commands)
- Non-destructive: MUST NOT overwrite user-owned files without explicit flags

## Required Files and Directories
- Required file:
  - `index.json`
- Required directories:
  - `features/`
  - `technical-debt/`
  - `research/`
  - `external-requests/`
  - `archive/`
- Allowed categories (authoritative): `features`, `technical-debt`, `research`, `external-requests`

## Schemas
- (TBD; file formats, required keys, constraints)

## Invariants
- (TBD)

## Validation Rules
- `allowed_categories` MUST match `process/checks/validation_rules.json` (`parking_lot.allowed_categories`).

## Examples Mapping
- (TBD; example fixtures that demonstrate this contract)
