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
- Each delivered version directory MUST satisfy the same base schemas as `ph/releases/current/contract.md` for:
  - `plan.md` (`type: release-plan`)
  - `progress.md` (`type: release-progress`)
  - `features.yaml` (`version: vX.Y.Z`, plus sprint metadata and `features` map)
- Additional delivered-only requirements:
  - In `plan.md` front matter:
    - `status` MUST be `delivered`
    - `delivered_date: YYYY-MM-DD` MUST be present
    - `delivered_sprint: SPRINT-...` MUST be present
  - `changelog.md` MUST include YAML front matter with at least:
    - `title: <string>`
    - `type: changelog`
    - `version: vX.Y.Z`
    - `date: YYYY-MM-DD`
  - YAML/JSON unknown keys MUST be preserved.

## Invariants
- In `plan.md` front matter, `status` MUST be `delivered`.
- Delivered release directories are immutable outputs:
  - the CLI MUST treat delivered release directories as read-only content after creation.

## Validation Rules
- `ph validate` SHOULD enforce:
  - each `vX.Y.Z/` directory contains required files (`plan.md`, `progress.md`, `features.yaml`, `changelog.md`)
  - version consistency across files (`version` matches the enclosing directory name)
  - `plan.md` includes delivered metadata fields and `status: delivered`
  - delivered directories are excluded from any “active/current” computations except for listing/history

## Examples Mapping
- `examples/v0.5.1/` demonstrates a delivered release directory file set (`plan.md`, `progress.md`, `features.yaml`, `changelog.md`).
