---
id: ADR-CLI-0004
title: Adopt Repo-Root Handbook Layout + `project_handbook.config.json` Marker
type: adr
status: accepted
date: 2026-02-04
tags: [cli, layout, scaffolding, config, marker]
links:
  - ./ADR-CLI-0001-ph-cli-migration.md
  - ./ADR-CLI-0003-ph-project-layout.md
  - ./CLI_CONTRACT.md
  - ../v0_make/MAKE_CONTRACT.md
  - ../AI_AGENT_START_HERE.md
---

# Context

We are migrating from a Make-target-driven interface (invoked as `pnpm make -- <target>`) to an installed `ph` CLI.

The most mature “real-world” handbook implementation is the legacy repo at:

- `/Users/spensermcconnell/__Active_Code/oss-saas/project-handbook`

That repo’s on-disk handbook layout is **repo-root content trees** (`adr/`, `sprints/`, `features/`, etc.) with automation internals under `.project-handbook/`.

The earlier v1 design proposed a layout suitable for embedding the handbook into arbitrary projects (`.ph/**` internals + `ph/**` content). In practice, the migration work failed once because commands implicitly assumed the handbook filesystem already existed, and the generator/linking logic drifted.

# Decision

For v1, we adopt the **repo-root handbook layout** as the canonical contract:

- Root marker: `PH_ROOT/project_handbook.config.json`
- Content root: `PH_ROOT/**` (e.g. `PH_ROOT/sprints/`, `PH_ROOT/features/`, `PH_ROOT/status/`, etc.)
- Internals: `PH_ROOT/.project-handbook/**` (append-only history log, optional caches)

Additionally:

- `ph init` MUST be able to bootstrap a fresh directory by creating the expected directory tree and required seed files (non-destructive; idempotent; never overwrite without an explicit force mode).
- Domain commands (`ph sprint plan`, `ph task create`, `ph release plan`, etc.) MUST also be robust when directories are missing, and create any missing parent directories they own.

# Consequences

- Any docs/specs mentioning `.ph/config.json` or a `ph/**` content subtree are historical and must not be treated as sources of truth for v1 behavior.
- The authoritative behavior lives in:
  - `cli_plan/v1_cli/CLI_CONTRACT.md`
  - `cli_plan/ph_spec/` (directory contracts under repo-root layout)
  - `cli_plan/v0_make/MAKE_CONTRACT.md` (reference behavior)
