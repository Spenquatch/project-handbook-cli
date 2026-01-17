---
title: PH Spec Contract — ph/releases/delivered/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: Container for delivered release version directories (`vX.Y.Z/`), produced by `ph release close`.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `vX.Y.Z/plan.md` body
  - `vX.Y.Z/changelog.md` body
  - `vX.Y.Z/**` post-delivery notes (if any)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none; delivered releases are treated as immutable output of `ph release close`)
- Overwrite rules:
  - The CLI MUST NOT overwrite any delivered release directory contents without explicit `--force`.
- Mutability:
  - CLI-managed: directory moves on close; `changelog.md` generation.
  - Human-edited: post-delivery notes may be appended, but MUST NOT break required schemas.

## Creation
- Created/updated by:
  - `ph init` (creates `delivered/`)
  - `ph release close` (moves `current/` into `delivered/<version>/`)
- Non-destructive: MUST refuse to overwrite an existing `delivered/<version>/` without an explicit force flag (if/when added).

## Required Files and Directories
- Required directory structure:
  - `vX.Y.Z/` (semantic version directory; one per delivered release)
- Each delivered version directory MUST contain:
  - `plan.md`
  - `progress.md`
  - `features.yaml`
  - `changelog.md`

## Schemas
- (TBD; file formats, required keys, constraints)

## Invariants
- In `plan.md` front matter, `status` MUST be `delivered`.

## Validation Rules
- (TBD; what `ph check` / `ph check-all` should enforce here)

## Examples Mapping
- (TBD; example fixtures that demonstrate this contract)
