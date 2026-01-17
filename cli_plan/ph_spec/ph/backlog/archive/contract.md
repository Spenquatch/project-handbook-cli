---
title: PH Spec Contract — ph/backlog/archive/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: Container for archived backlog items (bugs, wildcards, work-items). Items under `archive/` are treated as immutable historical records.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `bugs/**/README.md`
  - `work-items/**/README.md`
  - `wildcards/**/README.md`
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none)
- Overwrite rules:
  - Backlog archive content is treated as immutable; the CLI MUST NOT edit archived `README.md` bodies.
  - The CLI MAY move entire item directories into/out of `archive/`, but MUST refuse to overwrite an existing destination directory unless `--force` is provided.

## Creation
- Created/updated by:
  - `ph init` (creates directory structure).
  - Backlog items are archived by moving an existing item directory from `ph/backlog/<category>/` to `ph/backlog/archive/<category>/` (manual or future CLI command).
- Non-destructive:
  - Archiving MUST refuse to overwrite an existing destination directory unless `--force` is provided.
  - The CLI MUST NOT rewrite archived markdown bodies.

## Required Files and Directories
- Required directories:
  - `bugs/`
  - `wildcards/`
  - `work-items/`
- No required files at this level.

## Schemas
- No file schemas at this level.
- Item directories under each category MUST satisfy their respective category contract:
  - `ph/backlog/archive/bugs/contract.md`
  - `ph/backlog/archive/wildcards/contract.md`
  - `ph/backlog/archive/work-items/contract.md`

## Invariants
- `ph/backlog/archive/` MUST contain only the category directories listed above.
- Archived item directories MUST live under exactly one category subdirectory (no direct children are allowed under `archive/` besides the category directories).

## Validation Rules
- `ph validate` SHOULD enforce:
  - required category directories exist
  - no unexpected top-level entries exist under `ph/backlog/archive/`
  - each archived item directory satisfies the contract for its category

## Examples Mapping
- No examples at this container level.
- See category-level `examples/` directories for representative archived item fixtures.
