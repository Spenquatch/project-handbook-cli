---
title: PH Spec Contract — releases/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/releases/`
- Summary: Release lifecycle root containing versioned release directories (`vX.Y.Z/`) plus an optional `current` pointer used by `ph release status|show|progress` (legacy: `make release-status|show|progress`).

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `vX.Y.Z/plan.md` body
  - `vX.Y.Z/changelog.md` body (if generated on close)
  - `delivered/**` (optional; not currently used by the legacy automation)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - `vX.Y.Z/progress.md` (auto-generated summary)
  - `vX.Y.Z/features.yaml` (auto-managed feature assignment map)
- Overwrite rules:
  - The CLI MUST NOT overwrite human-authored release content (notably `plan.md` bodies) without explicit `--force`.
- Mutability:
  - Human-edited: release planning content (`plan.md` body).
  - Automation-managed: `progress.md` updates and `features.yaml` updates; close generates `changelog.md` and marks delivery metadata in `plan.md` front matter.

## Creation
- Created/updated by:
  - `ph release plan [--version next|vX.Y.Z] [--bump patch|minor|major] [--sprints N] [--sprint-ids ...] [--activate]` (creates `releases/vX.Y.Z/` and seed files; activates only with `--activate`).
  - `ph release activate --release vX.Y.Z` (creates/updates `releases/current` pointer).
  - `ph release clear` (removes `releases/current` pointer).
  - `ph release status` / `ph release show` / `ph release progress` (reads current; updates `progress.md`).
  - `ph release add-feature --release vX.Y.Z --feature <name> [--epic] [--critical]` (updates `features.yaml`).
  - `ph release close --version vX.Y.Z` (generates `changelog.md` and marks release delivered in `plan.md`; does **not** move directories).
  - `ph release list` / `ph release suggest` (read-only helpers).
  - `pnpm make -- release-plan [version=next|vX.Y.Z] [bump=patch|minor|major] [sprints=N] [sprint_ids=...] [activate=true]` (creates `releases/vX.Y.Z/` and seed files).
  - `pnpm make -- release-activate release=vX.Y.Z` (creates/updates `releases/current` pointer).
  - `pnpm make -- release-clear` (removes `releases/current` pointer).
  - `pnpm make -- release-status` / `release-show` / `release-progress` (reads current; updates `progress.md`).
  - `pnpm make -- release-add-feature release=vX.Y.Z feature=<name> [epic=true] [critical=true]` (updates `features.yaml`).
  - `pnpm make -- release-close version=vX.Y.Z` (generates `changelog.md` and marks release delivered in `plan.md`; does **not** move directories).
- Non-destructive: commands MUST refuse destructive overwrites unless explicitly forced.

## Required Files and Directories
- Required directories:
  - `delivered/` (may be empty; reserved for future/legacy experiments)
- Optional files:
  - `CHANGELOG.md` (project changelog; not required by v1 `ph release *` commands)
  - `current` (symlink pointer to a `vX.Y.Z/` directory; optional)
  - `vX.Y.Z/` directories (one per release)

## Schemas
- This directory has no root-level schema beyond subdirectory contracts.
- If `CHANGELOG.md` exists:
  - It MUST be Markdown with YAML front matter including at least:
    - `title: <string>`
    - `type: changelog`
    - `date: YYYY-MM-DD`
  - Additional keys are allowed; unknown keys MUST be preserved.

### Release plan slot sections (required; deterministic markers)

Release plans MUST define the goal of each sprint slot and how it enables/moves the release forward. To make validation deterministic, every `releases/vX.Y.Z/plan.md` MUST include one slot section per slot in the release timeline, using these exact headings/markers.

Slot section requirements:
- The release timeline slot count is `planned_sprints` from `releases/vX.Y.Z/plan.md` front matter (see `releases/current/contract.md`).
- The plan MUST include exactly `planned_sprints` slot sections, numbered `1..planned_sprints` (no gaps, no duplicates).
- Each slot section heading MUST match:
  - `^## Slot [1-9][0-9]*: .+`
  - Example: `## Slot 1: Foundation`
- Within each slot section, these subsections MUST appear exactly once and in this order:
  - `### Slot Goal`
  - `### Enablement`
  - `### Scope Boundaries`
  - `### Intended Gates`
- `### Scope Boundaries` MUST contain these exact marker lines (case + punctuation sensitive), each followed by at least one bullet list item:
  - `In scope:`
  - `Out of scope:`
- `### Intended Gates` MUST contain at least one list item that starts with `- Gate:` (case + punctuation sensitive).

### Release gates vs sprint gates (BL-0008; relationship)

When a sprint is aligned to an active release (see `sprints/*/plan.md` front matter `release` + `release_sprint_slot`), the “gates” for that release slot are executed and evidenced as sprint tasks.

Definitions:
- A **sprint gate task** is any task with `task_type: sprint-gate` (and therefore `session: sprint-gate` via the mapping table in the sprint/task contracts).
- A **release gate task** is a sprint gate task additionally marked with legacy metadata:
  - `release_gate: true`
  - `release: current | vX.Y.Z` (non-null; SHOULD match the active release plan the sprint is aligned to)

Deterministic doc rule for release gate tasks (implementable as a string check):
- If `task.yaml` has `release_gate: true`, it MUST also include the literal string: `task_type: sprint-gate`
- If `task.yaml` has `release_gate: true`, its `validation.md` MUST reference the release plan by including one of these literal strings:
  - `releases/current/plan.md`
  - `releases/v` (prefix for a versioned plan path like `releases/v0.8.0/plan.md`)

## Invariants
- `releases/current` (when present) MUST resolve to an existing `releases/vX.Y.Z/` directory.
- Release directories use semantic version naming: `releases/vX.Y.Z/`.

## Validation Rules
- `ph validate` SHOULD enforce:
  - `delivered/` exists (even if empty)
  - each `releases/vX.Y.Z/` satisfies `releases/vX.Y.Z/` release-file expectations (see `releases/current/contract.md` for the shared file schema)
  - if `CHANGELOG.md` exists, it has parseable YAML front matter
  - each `releases/vX.Y.Z/plan.md` includes slot sections as defined above (count + headings/markers), so sprint plans can deterministically align to a slot

## Examples Mapping
- `examples/CHANGELOG.md` demonstrates a project changelog artifact.
- `examples/v0.5.1/` demonstrates the active release working-set file shapes (`plan.md`, `progress.md`, `features.yaml`) for a planned release version.
