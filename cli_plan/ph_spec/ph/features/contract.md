---
title: PH Spec Contract — ph/features/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: Active feature directories (one directory per feature) containing the project’s feature specs, status, and supporting docs; archived features are moved to `ph/features/archive/`.

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
  - `ph init` (creates `ph/features/` and `ph/features/archive/` directories only).
  - `ph feature create --name <name> ...` (creates a new feature directory and seeds the standard feature doc set).
  - `ph feature status --name <name> --stage <stage>` (updates stage in `status.md`).
  - `ph feature update-status` (MAY recompute feature `status.md` files from sprint/task data; scope-local).
  - `ph feature archive --name <name> [--force]` (moves the feature directory into `ph/features/archive/`).
- Non-destructive:
  - `ph feature create` MUST refuse to overwrite an existing feature directory unless `--force` is provided.
  - `ph feature archive` MUST refuse to overwrite an existing destination directory unless `--force` is provided.
  - Unless explicitly requested (via `--force` or a dedicated update command), the CLI MUST NOT rewrite feature markdown bodies.

## Required Files and Directories
- Required:
  - `ph/features/` (directory)
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
  - `<name>` SHOULD be lowercase snake_case (recommended; treated as an opaque identifier by the filesystem).
  - Feature names MUST NOT start with `handbook-` or `ph-` (reserved prefixes; enforced by `ph feature create`).

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
  - `Stage: <stage>` (stage is an opaque string token; recommended values include `draft`, `proposed`, `approved`, `in-progress`, `done`)
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
- Active features live under `ph/features/<name>/`; archived features live under `ph/features/archive/<name>/` (see `ph/features/archive/contract.md`).
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
