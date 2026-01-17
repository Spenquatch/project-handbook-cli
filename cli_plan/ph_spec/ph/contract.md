---
title: PH Spec Contract — ph/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: (TBD)

## Ownership
- Owner: Shared.
- Definitions:
  - Content artifacts: project-owned, human-directed files under `ph/**` (typically Markdown/YAML). They may be authored/edited by humans *or* AI agents, often via `ph` command inputs.
  - Derived/internal artifacts: machine-managed files under `ph/**` (indexes, catalogs, exports, reports) that are explicitly declared safe to regenerate by the contract for that directory.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - Default: everything under `ph/**` unless a directory contract explicitly lists it as derived/internal.
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - MUST be explicitly listed (by filename) in the directory contract that owns them.
- Default policy:
  - Everything under `ph/**` is treated as content unless a directory contract explicitly lists it as an internal artifact.
  - A directory contract MUST list internal artifacts by concrete filename(s) (not only by extension) when regeneration is allowed.
- Overwrite rules:
  - The CLI MUST NOT overwrite content artifacts without explicit `--force`.
  - The CLI MAY regenerate internal artifacts, but MUST NOT delete or mutate content artifacts as a side effect.

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
