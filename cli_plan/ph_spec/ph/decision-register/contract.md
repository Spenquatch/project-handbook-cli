---
title: PH Spec Contract — ph/decision-register/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: (TBD)

## Ownership
- Owner: Project (human-directed).
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `README.md`
  - `DR-*.md` (decision register entries)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none)
- Overwrite rules:
  - The CLI MUST NOT modify decision register entries after creation.

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
