---
title: PH Spec Contract — releases/delivered/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/releases/delivered/`
- Summary: Reserved container for delivered-release artifacts. **In the current legacy automation**, `make release-close` marks a release as delivered *in place* under `releases/vX.Y.Z/` and does not move directories into `releases/delivered/`.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - Any files placed here manually (rare; treat as content if present).
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none)
- Overwrite rules:
  - The CLI MUST NOT overwrite any delivered release directory contents without explicit `--force`.
- Mutability:
  - CLI-managed: directory moves on close; `changelog.md` generation.
  - Human-edited: post-delivery notes may be appended, but MUST NOT break required schemas.

## Creation
- Created/updated by:
  - `pnpm make -- release-plan` ensures `releases/delivered/` exists (even if unused).
- Non-destructive: tooling must not delete or rewrite files placed here.

## Required Files and Directories
- Required: `releases/delivered/` directory exists (may be empty).

## Schemas
- No required schema in the current legacy system (directory is unused by default).

## Invariants
- Delivered releases are represented by `releases/vX.Y.Z/plan.md` having `status: delivered` plus `delivered_*` metadata (see `releases/current/contract.md`).

## Validation Rules
- `ph validate` SHOULD enforce:
  - `releases/delivered/` exists (warning only if missing; legacy automation will recreate it).

## Examples Mapping
- Delivered releases in the reference handbook repo live under `releases/vX.Y.Z/` (not under `releases/delivered/`).
