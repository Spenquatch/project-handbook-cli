---
title: PH Spec Contract — ph/status/exports/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: (TBD)

## Ownership
- Owner: CLI.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - (none)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - `*.tar.gz` (export bundle)
  - `*.tar.gz.sha256`
  - `*.manifest.txt`
  - `*.paths.txt`
  - `*.README.txt`
- Overwrite rules:
  - The CLI MAY regenerate exports, but SHOULD avoid collisions by choosing deterministic, unique names; it MUST NOT overwrite an existing export file unless `--force` is provided.

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
