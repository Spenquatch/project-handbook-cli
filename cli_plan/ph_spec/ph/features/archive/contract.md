---
title: PH Spec Contract — ph/features/archive/
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
  - `*/**/*.md` (archived feature docs; treated as immutable content)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none)
- Overwrite rules:
  - The CLI MAY move entire feature directories into/out of `ph/features/archive/`, but MUST refuse to overwrite an existing destination directory unless `--force` is provided.

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
