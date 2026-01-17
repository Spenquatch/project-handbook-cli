---
title: PH Spec Contract — ph/backlog/wildcards/
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
  - `WILD-*/README.md` (one directory per wildcard backlog item)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none; see `ph/backlog/contract.md` for `index.json`)
- Overwrite rules:
  - The CLI MUST NOT overwrite `WILD-*/README.md` without explicit `--force`.

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
