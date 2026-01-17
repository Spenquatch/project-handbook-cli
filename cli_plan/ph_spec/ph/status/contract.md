---
title: PH Spec Contract — ph/status/
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
  - `README.md`
  - `evidence/**` (evidence bundles; human-curated)
  - `daily/**` (daily status docs; human-edited unless explicitly generated)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - `current.json` (current status snapshot)
  - `current_summary.md` (current status summary)
  - `validation.json` (latest validation report)
- Overwrite rules:
  - The CLI MAY regenerate `current.json`, `current_summary.md`, and `validation.json`.
  - The CLI MUST NOT overwrite evidence or daily status docs without explicit `--force`.

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
