---
title: PH Spec Contract — backlog/archive/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/backlog/archive/`
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
  - Backlog items are archived by moving an existing item directory from `backlog/<category>/` to `backlog/archive/<category>/` (manual or via task tooling).
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
  - `backlog/archive/bugs/contract.md`
  - `backlog/archive/wildcards/contract.md`
  - `backlog/archive/work-items/contract.md`

## Invariants
- `backlog/archive/` MUST contain only the category directories listed above.
- Archived item directories MUST live under exactly one category subdirectory (no direct children are allowed under `archive/` besides the category directories).

## Validation Rules
- `ph validate` SHOULD enforce:
  - required category directories exist
  - no unexpected top-level entries exist under `backlog/archive/`
  - each archived item directory satisfies the contract for its category

## Examples Mapping
- No examples at this container level.
- See category-level `examples/` directories for representative archived item fixtures.
