---
title: PH Spec Contract — ph/releases/planning/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: Optional staging area for draft/next release planning artifacts (not required for v1 command execution).

## Ownership
- Owner: Project (human-authored).
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `**/*` (all files in this subtree)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none)
- Mutability: Human-edited only (v1 `ph release *` commands do not read/write here).
- Overwrite rules:
  - The CLI MUST NOT overwrite any files here.

## Creation
- Created by: `ph init` (directory-only; may be empty).
- Non-destructive: CLI MUST NOT overwrite any files here.

## Required Files and Directories
- No required files for v1.

## Schemas
- (TBD; file formats, required keys, constraints)

## Invariants
- (TBD)

## Validation Rules
- (TBD; what `ph check` / `ph check-all` should enforce here)

## Examples Mapping
- (TBD; example fixtures that demonstrate this contract)
