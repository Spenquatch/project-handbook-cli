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
- Optional files:
  - `CHANGELOG.md` (project changelog; not required by v1 `ph release *` commands)

## Schemas
- This directory has no root-level schema beyond subdirectory contracts.
- If `CHANGELOG.md` exists:
  - It MUST be Markdown with YAML front matter including at least:
    - `title: <string>`
    - `type: changelog`
    - `date: YYYY-MM-DD`
  - Additional keys are allowed; unknown keys MUST be preserved.

## Invariants
- `ph/releases/` MUST contain only:
  - `planning/`
  - `current/`
  - `delivered/`
  - `CHANGELOG.md` (optional)
- `current/` MUST be a directory (not a symlink).
- `delivered/` MUST contain only delivered release version directories of the form `vX.Y.Z/` (semantic version).

## Validation Rules
- `ph validate` SHOULD enforce:
  - required directories exist
  - `current/` satisfies `ph/releases/current/contract.md`
  - each `delivered/vX.Y.Z/` satisfies `ph/releases/delivered/contract.md`
  - if `CHANGELOG.md` exists, it has parseable YAML front matter

## Examples Mapping
- `examples/CHANGELOG.md` demonstrates a project changelog artifact.
- `examples/v0.5.1/` demonstrates the active release working-set file shapes (`plan.md`, `progress.md`, `features.yaml`) for a planned release version.
