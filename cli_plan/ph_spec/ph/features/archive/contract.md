---
title: PH Spec Contract — features/implemented/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/features/implemented/`
- Summary: Archived feature directories (completed or paused work), preserved as an immutable record after being moved out of the active `features/` tree.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `*/**/*.md` (archived feature docs; treated as immutable content)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none)
- Overwrite rules:
  - Tooling MAY move entire feature directories into/out of `features/implemented/`, but MUST refuse to overwrite an existing destination directory unless `--force`/`force=true` is provided.

## Creation
- Created/updated by:
  - `ph feature archive --name <name> [--force]` moves `features/<name>/` into `features/implemented/<name>/`.
  - `pnpm make -- feature-archive name=<name> [force=true]` moves `features/<name>/` into `features/implemented/<name>/`.
- Non-destructive:
  - Archiving MUST refuse to overwrite an existing destination directory unless `--force` is provided.
  - The CLI MUST NOT rewrite archived feature markdown bodies (treat as read-only content).

## Required Files and Directories
- Required:
  - `features/implemented/` (directory)
- Optional:
  - One directory per archived feature: `<feature_name>/`
  - Any files within each archived feature directory that were present at archive time (preserved as-is).

## Schemas
- There is no archive-specific schema; archived feature directories preserve the same artifacts as active features (see `ph/features/contract.md`).
- Content is typically Markdown with YAML front matter; unknown keys and bodies MUST be preserved.

## Invariants
- Archived feature directories MUST be treated as immutable content:
  - If a feature is present under `features/implemented/<name>/`, tooling MUST NOT modify files within it.
- Name collision avoidance:
  - An archived feature name SHOULD NOT simultaneously exist as an active feature directory under `ph/features/<name>/` (validation MAY warn).

## Validation Rules
- `ph validate` SHOULD enforce:
  - `features/implemented/` exists
  - archived feature entries are directories (not files)
- `ph feature` commands MUST NOT treat archived features as candidates for `list/status/update-status` unless explicitly requested by a future flag (default scope is active features).

## Examples Mapping
- No `features/implemented/` fixtures are currently provided in `examples/`; archived features are created by moving an existing active feature directory via `make feature-archive`.
