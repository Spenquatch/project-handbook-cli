---
title: PH Spec Contract — ph/releases/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: Release lifecycle root containing `planning/`, `current/`, and `delivered/` release artifacts.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `planning/**` (draft planning docs; optional for v1)
  - `current/plan.md` body
  - `delivered/vX.Y.Z/**` post-delivery notes (if any)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - `current/progress.md`
  - `current/features.yaml`
- Overwrite rules:
  - The CLI MUST NOT overwrite human-authored release content (notably `plan.md` bodies) without explicit `--force`.
- Mutability:
  - Human-edited: release planning content (`plan.md` body).
  - CLI-managed: file creation, `progress.md` updates, and delivered moves under `delivered/`.

## Creation
- Created/updated by:
  - `ph init` (creates directories)
  - `ph release plan` (creates/updates the active release working set under `current/`)
  - `ph release close --version vX.Y.Z` (moves `current/` → `delivered/vX.Y.Z/`)
- Non-destructive: commands MUST refuse destructive overwrites unless explicitly forced.

## Required Files and Directories
- Required directories:
  - `planning/`
  - `current/`
  - `delivered/`

## Schemas
- (TBD; file formats, required keys, constraints)

## Invariants
- `current/` MUST be a directory (not a symlink).
- `delivered/` MUST contain only delivered release version directories of the form `vX.Y.Z/` (semantic version).

## Validation Rules
- If `current/` exists, it MUST satisfy `ph/releases/current/contract.md`.
- Any `delivered/vX.Y.Z/` MUST satisfy `ph/releases/delivered/contract.md`.

## Examples Mapping
- (TBD; example fixtures that demonstrate this contract)
