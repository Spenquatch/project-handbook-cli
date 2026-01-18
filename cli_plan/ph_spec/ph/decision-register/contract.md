---
title: PH Spec Contract — ph/decision-register/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: Cross-cutting Decision Register (DR) entries that span multiple features or change shared conventions; feature-scoped DRs live under `ph/features/<feature>/decision-register/`.

## Ownership
- Owner: Project (human-directed).
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `README.md`
  - `DR-*.md` (decision register entries)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none)
- Overwrite rules:
  - The CLI MUST NOT modify decision register entries after creation.

## Creation
- Created/updated by:
  - `ph init` (creates `ph/decision-register/` directory only).
  - Humans create/edit DR Markdown files directly (no dedicated `ph decision ...` commands in v1).
  - DR entries are typically created during `session=research-discovery` tasks and later referenced/promoted into ADRs or feature decision records (FDRs).
- Non-destructive:
  - The CLI MUST NOT overwrite decision register entries without explicit `--force` (and v1 provides no default update command for DRs).

## Required Files and Directories
- Required files: (none)
- Optional files:
  - `README.md` (index/routing rules for cross-cutting vs feature-scoped DRs)
  - `DR-XXXX-<slug>.md` (one decision per file)

## Schemas
- All Markdown files in this directory MUST include YAML front matter (global `ph/` rule).
- `README.md`:
  - MUST include YAML front matter with at least:
    - `title: <string>`
    - `type: process`
    - `date: YYYY-MM-DD`
  - MAY include:
    - `tags: [<tag>, ...]`
    - `links: [<relative path>, ...]`
- `DR-XXXX-<slug>.md` decision entries:
  - Filename rules:
    - `XXXX` MUST be a 4-digit zero-padded number (e.g. `DR-0003`).
  - Front matter MUST include at least:
    - `title: DR-XXXX — <Decision Title>` (MUST include the same `DR-XXXX` as the filename)
    - `type: decision-register`
    - `date: YYYY-MM-DD`
  - Front matter MAY include:
    - `tags: [decision-register, ...]`
    - `links: [<relative path>, ...]`
  - Body SHOULD follow the standard DR structure:
    - Problem/Context
    - Option A (pros/cons/implications/risks/unlocks/quick wins)
    - Option B (same)
    - Recommendation + rationale
    - Follow-up tasks (explicit)

## Invariants
- One decision per file: each `DR-*.md` file represents exactly one DR.
- Filename/title alignment: `DR-XXXX` in the filename MUST match the `DR-XXXX` in the front matter `title`.

## Validation Rules
- `ph validate` SHOULD enforce:
  - front matter exists for all `*.md` files (global rule)
  - for any file matching `DR-*.md`:
    - `type: decision-register`
    - `title` includes the matching `DR-XXXX` prefix
- `ph` commands MUST treat DR files as content artifacts and MUST NOT rewrite their bodies unless explicitly requested.

## Examples Mapping
- `examples/README.md` demonstrates:
  - index/routing rules between cross-cutting and feature-scoped DRs,
  - the required copy/paste DR template shape.
- `examples/DR-0003-cosmo-minio-baseline-topology.md` demonstrates a completed DR entry with required front matter and a full Option A/Option B tradeoff record.
