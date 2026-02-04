---
title: PH Spec Contract — releases/vX.Y.Z/ (and releases/current)
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance):
  - Version directory: `PH_ROOT/releases/vX.Y.Z/`
  - Current pointer: `PH_ROOT/releases/current` (symlink to a `vX.Y.Z/` directory)
- Summary: Working set for a single release version directory. The legacy system models “current release” via the `releases/current` symlink.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `plan.md` body
  - `changelog.md` body (if generated on close; humans may edit afterwards)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - `progress.md` (auto-generated summary; safe to regenerate)
  - `features.yaml` (auto-managed feature assignment map; safe to regenerate)
- Overwrite rules:
  - The CLI MUST NOT overwrite `plan.md` body content without explicit `--force`.
- Mutability:
  - Human-edited: `plan.md` body (and most front matter fields, except those updated on close).
  - Automation-managed: `progress.md`, `features.yaml`, and delivery metadata written during close.

## Creation
- Created/updated by:
  - `ph release plan ...` (creates seed files if missing).
  - `ph release plan ... --activate` (also sets `releases/current` to the created version directory).
  - `ph release activate --release vX.Y.Z` (sets `releases/current` to an existing version directory).
  - `ph release clear` (removes `releases/current` pointer).
  - `ph release add-feature --release vX.Y.Z --feature <name> ...` (updates `features.yaml`).
  - `ph release status|show|progress` (updates `progress.md`).
  - `ph release close --version vX.Y.Z` (writes `changelog.md` and updates delivery metadata in `plan.md` front matter).
  - `pnpm make -- release-plan [version=next|vX.Y.Z] ...` (creates seed files if missing).
  - `pnpm make -- release-plan ... activate=true` (also sets `releases/current` to the created version directory).
  - `pnpm make -- release-activate release=vX.Y.Z` (sets `releases/current` to an existing version directory).
  - `pnpm make -- release-clear` (removes `releases/current` pointer).
  - `pnpm make -- release-add-feature release=vX.Y.Z feature=<name> ...` (updates `features.yaml`).
  - `pnpm make -- release-status|release-show|release-progress` (updates `progress.md`).
  - `pnpm make -- release-close version=vX.Y.Z` (writes `changelog.md` and updates delivery metadata in `plan.md` front matter).
- Non-destructive:
  - `plan.md` body is treated as content and must not be overwritten by default.

## Required Files and Directories
- Required files:
  - `plan.md`
  - `features.yaml`
  - `progress.md`
- Optional files (created during `ph release close`; directories are not moved by default):
  - `changelog.md`

## Schemas
- `plan.md` MUST include front matter containing at least:
  - `type: release-plan`
  - `version: vX.Y.Z`
  - `planned_sprints: <integer>`
  - `status: planned|delivered`
  - `date: YYYY-MM-DD`
- `plan.md` MAY include one of these timeline descriptions (legacy currently prefers sprint slots):
  - Sprint slots:
    - `timeline_mode: sprint_slots`
    - `sprint_slots: [<int>...]`
  - Explicit sprints:
    - `timeline_mode: explicit_sprints`
    - `sprint_ids: [SPRINT-..., ...]`
- If `status: delivered`, `plan.md` MUST include:
  - `delivered_sprint: SPRINT-...`
  - `delivered_date: YYYY-MM-DD`
- `progress.md` MUST include front matter containing at least:
  - `type: release-progress`
  - `version: vX.Y.Z`
  - `date: YYYY-MM-DD`
- `changelog.md` (when present) MUST include front matter containing at least:
  - `title: <string>`
  - `type: changelog`
  - `version: vX.Y.Z`
  - `date: YYYY-MM-DD`
- `features.yaml` MUST include at least:
  - `version: vX.Y.Z`
  - `planned_sprints: <integer>`
  - `timeline_mode: sprint_slots` (legacy default)
  - `start_sprint_slot: <int>`
  - `end_sprint_slot: <int>`
  - `features: <map>`
- `features.yaml` `features` map values SHOULD include:
  - `type: regular|epic`
  - `priority: P0|P1|P2|P3|P4`
  - `status: planned|in_progress|done|blocked`
  - `completion: <0..100>`
  - `critical_path: <boolean>`

## Invariants
- The directory name `vX.Y.Z` MUST match:
  - `plan.md` front matter `version`,
  - `progress.md` front matter `version`,
  - `features.yaml` top-level `version`,
  - and `changelog.md` front matter `version` (if present).
- `releases/current` (when present) MUST resolve to an existing `releases/vX.Y.Z/` directory.

## Validation Rules
- `ph validate` SHOULD enforce:
  - required file presence (`plan.md`, `progress.md`, `features.yaml`)
  - `version` fields are consistent across `plan.md`, `progress.md`, `features.yaml` (and `changelog.md` if present)
  - if `timeline_mode: sprint_slots`, slot metadata is consistent (`planned_sprints` equals `(end_sprint_slot - start_sprint_slot + 1)`)

## Examples Mapping
- `releases/v0.6.0/` in the reference handbook repo demonstrates:
  - `plan.md`, `progress.md`, `features.yaml` and (after close) `changelog.md`.
