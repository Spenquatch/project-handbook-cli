---
id: ADR-CLI-0003
title: Adopt `.ph/` Internals + `ph/` Content Layout (No System Scope)
type: adr
status: proposed
date: 2026-01-15
tags: [cli, layout, scaffolding, config, marker]
links:
  - ./ADR-CLI-0001-ph-cli-migration.md
  - ./ADR-CLI-0002-handbook-instance-scaffolding.md
  - ./CLI_CONTRACT.md
  - ../AI_AGENT_START_HERE.md
---

# Context

The v1 `ph` CLI is intended to be used inside *any* project repository (not only inside the legacy `project-handbook` repo). The handbook content (`adr/`, `sprints/`, etc) should therefore live as a *subtree* of a project, while CLI-owned runtime/config/state should be isolated and hidden.

# Decision

## Filesystem layout

Within a user project repository:

- `ph/**` is the **project’s handbook content** (human-authored and reviewed).
- `.ph/**` is **CLI-owned internal state and config** (machine-authored, safe to regenerate/upgrade).

Example:

- `my-project/`
  - `.ph/`
    - `config.json` (root marker)
    - `process/**` (CLI-required configs/templates)
    - `status/**` (machine outputs: validation JSON, caches, snapshots)
  - `ph/`
    - `adr/**`
    - `backlog/**`
    - `features/**`
    - `releases/**` (see `current/`, `planning/`, `delivered/`)
    - `roadmap/**`
    - `sprints/**`
    - `status/**` (human outputs: daily markdown, status pages)

## Root marker

The root marker becomes:

- `.ph/config.json`

Rationale:
- The marker lives with CLI-owned state (and doesn’t “pollute” the project root).
- It is unambiguous and works in any repository layout.
- It makes “handbook content” (`ph/**`) movable without changing root identity.

## No system scope

Remove `--scope system` and all “system scope” behavior from the v1 contract.

Rationale:
- In typical usage, `ph` operates inside a user’s project repo; “system scope” as “handbook’s own meta-handbook” does not generalize well.
- If a future global/user configuration is needed, it should be a separate concept (e.g. per-user config under `~/.config/ph/**`) and not conflated with per-project scope.

# Options considered

## Option A (chosen): marker at `.ph/config.json`

Pros:
- Hidden internals are clearly separated from content.
- Root detection is stable and consistent with “internals live in `.ph/`”.

Cons:
- The marker is less “discoverable” from a bare directory listing (mitigated by `ph doctor` guidance and docs).

## Option B: marker at `ph/.internals/config.json`

Pros:
- Everything (content + internals) is under one visible top-level directory (`ph/`).

Cons:
- Internals become easy to accidentally edit, move, or delete while working on content.
- It muddies the separation between “human content” and “machine state”.
- Hidden semantics are lost unless `.internals/` is consistently ignored and treated as special.

# Migration notes

- This ADR is a breaking layout change from the earlier “handbook instance repo root contains marker and content” model.
- We intentionally do **not** define a first-class migration command in v1; users can either:
  - start fresh with `ph init` inside their project repo, or
  - manually move existing handbook content under `ph/` and create `.ph/config.json`.

# Consequences

- Contract paths must be updated to distinguish:
  - internal paths rooted at `.ph/**` (config/state), and
  - content paths rooted at `ph/**` (handbook content).
- `ph init` (and future scaffolding) should create both trees.

# Scaffold spec (created by `ph init`)

`ph init` MUST be able to run inside any project repo and create the expected `ph/**` content tree plus the required `.ph/**` internals (non-destructive; never overwrite user changes).

## Content tree (`ph/**`)

Directories to create if missing:

- `ph/adr/`
- `ph/backlog/`
  - `ph/backlog/bugs/`
  - `ph/backlog/wildcards/`
  - `ph/backlog/work-items/`
  - `ph/backlog/archive/`
    - `ph/backlog/archive/bugs/`
    - `ph/backlog/archive/wildcards/`
    - `ph/backlog/archive/work-items/`
- `ph/contracts/`
- `ph/decision-register/`
- `ph/features/`
  - `ph/features/archive/`
- `ph/parking-lot/`
  - `ph/parking-lot/features/`
  - `ph/parking-lot/technical-debt/`
  - `ph/parking-lot/research/`
  - `ph/parking-lot/external-requests/`
  - `ph/parking-lot/archive/`
    - `ph/parking-lot/archive/features/`
    - `ph/parking-lot/archive/technical-debt/`
    - `ph/parking-lot/archive/research/`
    - `ph/parking-lot/archive/external-requests/`
- `ph/releases/`
  - `ph/releases/planning/`
  - `ph/releases/current/`
  - `ph/releases/delivered/`
- `ph/roadmap/`
- `ph/sprints/`
  - `ph/sprints/archive/`
- `ph/status/`
  - `ph/status/daily/`
  - `ph/status/evidence/`
  - `ph/status/exports/`

Seed files to create if missing:

- `ph/roadmap/now-next-later.md` (used by `ph roadmap show|create|validate`)
  - Must include valid front matter and these headings:
    - `# Now / Next / Later Roadmap`
    - `## Now`
    - `## Next`
    - `## Later`

Release note:
- Completed release version directories are expected under `ph/releases/delivered/<vX.Y.Z>/`.
- Active release work is expected under `ph/releases/current/` (directory, not a symlink).

## Internals (`.ph/**`)

Directories to create if missing:

- `.ph/`
- `.ph/process/`
  - `.ph/process/checks/`
  - `.ph/process/automation/`
  - `.ph/process/sessions/`
    - `.ph/process/sessions/templates/`
- `.ph/status/`

Seed files to create if missing:

- `.ph/config.json` (root marker)
- `.ph/process/checks/validation_rules.json`
- `.ph/process/automation/reset_spec.json`

## Git ignore behavior

By default, `ph init` SHOULD update the project’s `.gitignore` so CLI-owned internals are not accidentally committed.

- Default behavior: add `.ph/` to `PH_ROOT/.gitignore` (idempotent)
- Opt-out: `ph init --no-gitignore`
- Explicit opt-in: `ph init --gitignore` (same behavior as default)

Note:
- We intentionally do **not** ignore `ph/` by default; it is the project’s handbook content and should remain versionable in the project repo.
