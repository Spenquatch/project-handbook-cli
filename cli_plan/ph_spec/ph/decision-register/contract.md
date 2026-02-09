---
title: PH Spec Contract — decision-register/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/decision-register/`
- Summary: Cross-cutting Decision Register (DR) entries that span multiple features or change shared conventions; feature-scoped DRs live under `features/<feature>/decision-register/`.

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
  - Humans create/edit DR Markdown files directly.
  - The CLI MAY scaffold a new DR entry via `ph dr add` (non-destructive; creation only).
  - DR entries are typically created during `session=research-discovery` tasks and later referenced/promoted into ADRs (cross-cutting) or Feature Decision Records (FDRs; feature-scoped).
- Non-destructive:
  - The CLI MUST NOT overwrite decision register entries without explicit `--force`.
  - The CLI MUST NOT modify DR files after creation (creation-only scaffolding).

## Command surface

### `ph dr add --id DR-#### --title <t> [--feature <name>] [--date YYYY-MM-DD]`

Behavior:
- Scaffold a new DR markdown file and print its path.
- If `--feature` is omitted, the DR MUST be created under `decision-register/`.
- If `--feature <name>` is provided, the DR MUST be created under `features/<name>/decision-register/`.
- Filename MUST be `DR-####-<slug>.md` where `<slug>` is derived deterministically from `--title` as lowercase kebab-case.
- Front matter MUST include at least:
  - `title: DR-#### — <t>`
  - `type: decision-register`
  - `date: YYYY-MM-DD`

Guardrails:
- `--id` MUST be exactly `DR-NNNN` where `NNNN` is 4 digits.
- The CLI MUST refuse to create the DR if the target file already exists (non-destructive).

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
- Workflow invariant (BL-0005):
  - DR ids (`DR-####`) are the only allowed `decision:` values for `session: research-discovery` tasks.

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
