---
title: PH Spec Contract — features/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/features/`
- Summary: Active feature directories (one directory per feature) containing the project’s feature specs, status, and supporting docs; archived features are moved to `features/implemented/` (legacy naming).

## Ownership
- Owner: Project (human-directed).
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `*/**/*.md` (feature docs: overview/status/architecture/implementation/testing/etc.)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none)
- Overwrite rules:
  - The CLI MUST NOT overwrite feature docs under `ph/features/` without explicit `--force`.

## Creation
- Created/updated by:
  - `ph feature create --name <name> [--epic] [--owner @handle] [--stage <stage>]` (creates a new feature directory and seeds the standard feature doc set).
  - `ph feature status --name <name> --stage <stage>` (updates stage in `status.md`).
  - `ph feature update-status` (recomputes feature `status.md` files from sprint/task data).
  - `ph feature summary` (prints an aggregate summary view).
  - `ph feature archive --name <name> [--force]` (moves the feature directory into `features/implemented/`).
  - `pnpm make -- feature-create name=<name> [epic=true] [owner=@handle] [stage=<stage>]` (creates a new feature directory and seeds the standard feature doc set).
  - `pnpm make -- feature-status name=<name> stage=<stage>` (updates stage in `status.md`).
  - `pnpm make -- feature-update-status` (recomputes feature `status.md` files from sprint/task data).
  - `pnpm make -- feature-summary` (prints an aggregate summary view).
  - `pnpm make -- feature-archive name=<name> [force=true]` (moves the feature directory into `features/implemented/`).
- Non-destructive:
  - `ph feature create` MUST refuse to overwrite an existing feature directory unless `--force` is provided.
  - `ph feature archive` MUST refuse to overwrite an existing destination directory unless `--force` is provided.
  - Unless explicitly requested (via `--force` or a dedicated update command), the CLI MUST NOT rewrite feature markdown bodies.

## Required Files and Directories
- Required:
  - `features/` (directory)
  - `features/implemented/` (directory; legacy archive target)
- Required layout for each active feature directory:
  - `<FEATURE_DIR>/overview.md`
  - `<FEATURE_DIR>/status.md`
  - `<FEATURE_DIR>/changelog.md`
- Optional files (recommended):
  - `<FEATURE_DIR>/risks.md` (risk register)
- Optional subdirectories (recommended):
  - `<FEATURE_DIR>/architecture/ARCHITECTURE.md`
  - `<FEATURE_DIR>/implementation/IMPLEMENTATION.md`
  - `<FEATURE_DIR>/testing/TESTING.md`
  - `<FEATURE_DIR>/decision-register/DR-XXXX-<slug>.md` (feature-scoped DR entries)
- Allowed feature directory names:
  - `<name>` is an opaque identifier; in practice kebab-case is common (legacy).

## Schemas
- All Markdown files in feature directories MUST include YAML front matter (global `ph/` rule).
- `overview.md` front matter MUST include at least:
  - `title: <string>`
  - `type: overview`
  - `feature: <feature_name>`
  - `date: YYYY-MM-DD`
- `overview.md` front matter SHOULD include (recommended; used for planning/validation automation):
  - `dependencies: [<ADR-XXXX|feature_name|...>, ...]`
  - `backlog_items: [<BUG-...|WILD-...|WORK-...>, ...]`
  - `parking_lot_origin: <string | null>`
  - `capacity_impact: planned|reactive`
  - `epic: <boolean>`
- `status.md` front matter MUST include at least:
  - `title: <string>`
  - `type: status`
  - `feature: <feature_name>`
  - `date: YYYY-MM-DD`
- `status.md` body MUST include a single stage line:
  - `Stage: <stage>` (recommended values: `proposed`, `approved`, `developing`, `complete`, `live`, `deprecated`)
- `changelog.md` front matter MUST include at least:
  - `title: <string>`
  - `type: changelog`
  - `feature: <feature_name>`
  - `date: YYYY-MM-DD`
- `risks.md` front matter MUST include at least:
  - `title: <string>`
  - `type: risks`
  - `feature: <feature_name>`
  - `date: YYYY-MM-DD`
- Additional YAML keys are allowed; unknown keys MUST be preserved.

## Invariants
- Active features live under `features/<name>/`; archived features live under `features/implemented/<name>/` (see `features/implemented/contract.md`).
- Each active feature directory MUST contain exactly one `overview.md` and one `status.md`.

## Validation Rules
- `ph validate` SHOULD enforce:
  - required files exist for each active feature directory (`overview.md`, `status.md`, `changelog.md`)
  - all feature Markdown files have parseable YAML front matter
  - required front matter keys exist and match the expected `type` per file
  - `status.md` contains a `Stage: ...` line
- Validation SHOULD treat missing optional artifacts (`risks.md`, `architecture/`, `implementation/`, `testing/`, `decision-register/`) as warnings only.

## Examples Mapping
- `examples/v2_launch/` demonstrates an active feature directory with:
  - `overview.md`, `status.md`, `changelog.md`, `risks.md`
  - optional deep-dive docs under `architecture/`, `implementation/`, and `testing/`.
