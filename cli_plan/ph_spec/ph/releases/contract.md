---
title: PH Spec Contract — releases/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/releases/`
- Summary: Release lifecycle root containing versioned release directories (`vX.Y.Z/`) plus an optional `current` pointer used by `make release-status|show|progress`.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `vX.Y.Z/plan.md` body
  - `vX.Y.Z/changelog.md` body (if generated on close)
  - `delivered/**` (optional; not currently used by the legacy automation)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - `vX.Y.Z/progress.md` (auto-generated summary)
  - `vX.Y.Z/features.yaml` (auto-managed feature assignment map)
- Overwrite rules:
  - The CLI MUST NOT overwrite human-authored release content (notably `plan.md` bodies) without explicit `--force`.
- Mutability:
  - Human-edited: release planning content (`plan.md` body).
  - Automation-managed: `progress.md` updates and `features.yaml` updates; close generates `changelog.md` and marks delivery metadata in `plan.md` front matter.

## Creation
- Created/updated by:
  - `pnpm make -- release-plan [version=next|vX.Y.Z] [bump=patch|minor|major] [sprints=N] [sprint_ids=...] [activate=true]` (creates `releases/vX.Y.Z/` and seed files).
  - `pnpm make -- release-activate release=vX.Y.Z` (creates/updates `releases/current` pointer).
  - `pnpm make -- release-clear` (removes `releases/current` pointer).
  - `pnpm make -- release-status` / `release-show` / `release-progress` (reads current; updates `progress.md`).
  - `pnpm make -- release-add-feature release=vX.Y.Z feature=<name> [epic=true] [critical=true]` (updates `features.yaml`).
  - `pnpm make -- release-close version=vX.Y.Z` (generates `changelog.md` and marks release delivered in `plan.md`; does **not** move directories).
- Non-destructive: commands MUST refuse destructive overwrites unless explicitly forced.

## Required Files and Directories
- Required directories:
  - `delivered/` (may be empty; reserved for future/legacy experiments)
- Optional files:
  - `CHANGELOG.md` (project changelog; not required by v1 `ph release *` commands)
  - `current` (symlink pointer to a `vX.Y.Z/` directory; optional)
  - `vX.Y.Z/` directories (one per release)

## Schemas
- This directory has no root-level schema beyond subdirectory contracts.
- If `CHANGELOG.md` exists:
  - It MUST be Markdown with YAML front matter including at least:
    - `title: <string>`
    - `type: changelog`
    - `date: YYYY-MM-DD`
  - Additional keys are allowed; unknown keys MUST be preserved.

## Invariants
- `releases/current` (when present) MUST resolve to an existing `releases/vX.Y.Z/` directory.
- Release directories use semantic version naming: `releases/vX.Y.Z/`.

## Validation Rules
- `ph validate` SHOULD enforce:
  - `delivered/` exists (even if empty)
  - each `releases/vX.Y.Z/` satisfies `releases/vX.Y.Z/` release-file expectations (see `releases/current/contract.md` for the shared file schema)
  - if `CHANGELOG.md` exists, it has parseable YAML front matter

## Examples Mapping
- `examples/CHANGELOG.md` demonstrates a project changelog artifact.
- `examples/v0.5.1/` demonstrates the active release working-set file shapes (`plan.md`, `progress.md`, `features.yaml`) for a planned release version.
