---
title: PH Spec Contract — ph/releases/current/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: Working set for the active (in-progress) release.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `plan.md` body
  - `changelog.md` body (if created)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - `progress.md`
  - `features.yaml`
- Overwrite rules:
  - The CLI MUST NOT overwrite `plan.md` body content without explicit `--force`.
- Mutability:
  - Human-edited: `plan.md` body (and most front matter fields, except those updated on close).
  - CLI-managed: `progress.md`, `features.yaml`, and delivery metadata written during `ph release close`.

## Creation
- Created/updated by:
  - `ph release plan` (creates seed files if missing)
  - `ph release add-feature` (updates `features.yaml`)
  - `ph release close` (ensures `changelog.md`, updates `plan.md` front matter, then moves the directory)
- Non-destructive: MUST NOT overwrite user-owned content in `plan.md` body.
  - Version derivation (for `ph release plan --version next`): the computed `vX.Y.Z` MUST be persisted in `plan.md` front matter (`version: vX.Y.Z`).

## Required Files and Directories
- Required files:
  - `plan.md`
  - `progress.md`
  - `features.yaml`
- Optional files (created during `ph release close` before the directory is moved to `delivered/`):
  - `changelog.md`

## Schemas
- `plan.md` MUST include front matter containing at least:
  - `type: release-plan`
  - `version: vX.Y.Z`
  - `status: planned|in_progress|delivered`
- `progress.md` MUST include front matter containing at least:
  - `type: release-progress`
  - `version: vX.Y.Z`
- `features.yaml` MUST include at least:
  - `version: vX.Y.Z`

## Invariants
- `plan.md` `version` MUST match the release version used by `ph release close --version ...`.
- `ph release close --version vX.Y.Z` MUST:
  - refuse if `delivered/vX.Y.Z/` already exists, and
  - move the entire `current/` directory into `delivered/vX.Y.Z/` as a single operation when supported by the filesystem.

## Validation Rules
- `ph check-all` SHOULD fail if any required file is missing or if `version` fields are inconsistent across `plan.md`, `progress.md`, and `features.yaml`.

## Examples Mapping
- (TBD; example fixtures that demonstrate this contract)
