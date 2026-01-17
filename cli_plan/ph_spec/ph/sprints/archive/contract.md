---
title: PH Spec Contract — ph/sprints/archive/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: Archived sprints and their immutable artifacts, plus an `index.json` catalog of archived sprint metadata.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `YYYY/SPRINT-*/plan.md` body
  - `YYYY/SPRINT-*/tasks/**` task docs
  - `YYYY/SPRINT-*/retrospective.md` body
  - `YYYY/SPRINT-*/burndown.md` (may include human commentary)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - `index.json` (catalog of archived sprint metadata)
- Overwrite rules:
  - The CLI MUST NOT overwrite an existing archived sprint directory without explicit `--force`.
- Mutability:
  - CLI-managed: moves into `archive/` and `index.json` updates.
  - Human-edited: post-hoc notes inside archived sprint markdowns (must preserve front matter).

## Creation
- Created/updated by:
  - `ph init` (creates `sprints/archive/`)
  - `ph sprint close` and `ph sprint archive` (move sprint dirs into `archive/`, update `index.json`)
- Non-destructive: MUST refuse to overwrite an existing archived sprint directory.

## Required Files and Directories
- Required file:
  - `index.json`
- Archived sprint directory layout (canonical):
  - `YYYY/SPRINT-<...>/`
    - `plan.md`
    - `tasks/`
    - `retrospective.md`
    - `burndown.md`

## Schemas
- `index.json` MUST be a JSON object with:
  - `sprints`: array of objects containing at least:
    - `sprint` (string; sprint id)
    - `archived_at` (string; RFC3339 timestamp)
    - `path` (string; relative path to archived sprint directory)
    - `start` (string; `YYYY-MM-DD`)
    - `end` (string; `YYYY-MM-DD`)

## Invariants
- `ph sprint close` MUST:
  - create `retrospective.md` in the sprint directory before archiving, and
  - ensure a final `burndown.md` exists in the sprint directory before archiving.
- On archive, `sprints/current` MUST NOT be left pointing at a non-existent sprint directory.

## Validation Rules
- Every sprint referenced by `index.json` MUST exist at the referenced `path`.

## Examples Mapping
- (TBD; example fixtures that demonstrate this contract)
