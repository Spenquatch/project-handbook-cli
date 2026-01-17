---
title: PH Spec Contract — ph/backlog/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: (TBD)

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `bugs/**/README.md`
  - `work-items/**/README.md`
  - `wildcards/**/README.md`
  - `archive/**/README.md` (archived items; treated as immutable content)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - `index.json` (catalog of backlog items and metadata)
- Overwrite rules:
  - The CLI MAY regenerate `index.json`.
  - The CLI MUST NOT overwrite any `README.md` content without explicit `--force`.

## Creation
- Created/updated by: (TBD; `ph ...` commands)
- Non-destructive: MUST NOT overwrite user-owned files without explicit flags

## Required Files and Directories
- (TBD)

## Schemas
- (TBD; file formats, required keys, constraints)

## Invariants
- (TBD)

## Validation Rules
- (TBD; what `ph check` / `ph check-all` should enforce here)

## Examples Mapping
- (TBD; example fixtures that demonstrate this contract)
