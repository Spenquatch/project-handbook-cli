---
title: PH Spec Contract — ph/sprints/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: Active sprint workspaces (by sprint id) plus a `sprints/current` pointer to the currently-open sprint.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `YYYY/SPRINT-*/plan.md` body
  - `YYYY/SPRINT-*/tasks/**` task docs
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - `current` (directory link pointer)
- Overwrite rules:
  - The CLI MUST NOT overwrite an existing sprint directory or its `plan.md` without explicit `--force`.
- Mutability:
  - Human-edited: sprint `plan.md` content and task docs under `tasks/`.
  - CLI-managed: directory scaffolding and `sprints/current` pointer updates.

## Creation
- Created/updated by:
  - `ph init` (creates `sprints/` and `sprints/archive/`)
  - `ph sprint plan` (creates a new sprint directory and seed `plan.md`)
  - `ph sprint open` (updates `sprints/current` pointer)
- Non-destructive: `ph sprint plan` MUST NOT overwrite an existing sprint directory unless `--force` is provided.

## Required Files and Directories
- Required directories:
  - `archive/`
- Required pointer:
  - `current` (MUST behave like a directory link to the current sprint directory)
    - POSIX: symlink
    - Windows: directory junction (preferred) or symlink (if permitted)
    - If neither is possible, `ph sprint plan|open` MUST fail with remediation (see CLI contract).
- Sprint directory layout (canonical):
  - `YYYY/SPRINT-<...>/`
    - `plan.md`
    - `tasks/`

## Schemas
- (TBD; file formats, required keys, constraints)

## Invariants
- `sprints/current` MUST resolve to an existing sprint directory.
- The sprint directory year partition `YYYY/` MUST equal the year segment in the sprint id (`SPRINT-YYYY-...`).
- A sprint directory MUST contain:
  - `plan.md`
  - `tasks/` (may be empty)

## Validation Rules
- `plan.md` MUST include front matter with at least:
  - `type: sprint-plan`
  - `sprint: SPRINT-...` (matching the directory name)
- Task directories under `tasks/` MUST satisfy the task contract (`ph/task/*` in the CLI contract and validation rules).

## Examples Mapping
- (TBD; example fixtures that demonstrate this contract)
