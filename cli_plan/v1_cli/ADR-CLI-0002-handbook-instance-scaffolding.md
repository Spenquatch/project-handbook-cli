---
id: ADR-CLI-0002
title: Scaffold a Full Handbook Instance Filesystem via `ph`
type: adr
status: superseded
date: 2026-01-15
tags: [handbook, cli, scaffolding, templates, init]
links:
  - ./ADR-CLI-0001-ph-cli-migration.md
  - ./ADR-CLI-0004-ph-root-layout.md
  - ./CLI_CONTRACT.md
  - ../AI_AGENT_START_HERE.md
---

# Note (historical)

This ADR is **superseded** and kept for context only. Do not implement new behavior from this document:

- use `cli_plan/v1_cli/ADR-CLI-0004-ph-root-layout.md` and `cli_plan/v1_cli/CLI_CONTRACT.md` as the sources of truth

# Context

`ph` currently assumes a handbook instance repo already exists with a known filesystem layout (e.g. `features/`, `sprints/`, `process/`, etc). Some commands scaffold *parts* of the structure (feature/task/sprint creation), and `ph init` now creates the minimum boot assets so `ph doctor` succeeds in a fresh directory.

## Update (2026-01-15)

This ADR assumes a “handbook instance repo” layout at repo root. The accepted v1 direction is now defined in `cli_plan/v1_cli/ADR-CLI-0004-ph-root-layout.md` (root marker `.project-handbook/config.json`, internals under `.project-handbook/**`). Treat this ADR as historical background on “full scaffolding” only.

However, creating a *new* handbook instance repo from scratch still requires external steps (copying/cloning an existing instance), and it is easy to end up with a “half-initialized” directory that passes root detection but lacks expected content/templates and conventions.

# Decision drivers

- **Deterministic and offline-capable**: must not depend on network or remote templates at runtime.
- **Safe-by-default**: must not overwrite existing user files; prefer explicit flags for destructive actions.
- **Reproducible**: given the same `ph` version, the scaffold output should be stable.
- **Upgradeable**: support evolving the scaffold over time without breaking existing repos.
- **Separation of concerns**:
  - “Handbook instance” is user-owned content and planning.
  - “CLI-owned” internal state should be clearly segregated and hidden from day-to-day docs.

# Proposal

## Command surface

Introduce a dedicated scaffolding command family (name TBD):

- `ph scaffold full` (preferred) OR `ph init --full`
  - Creates the full recommended filesystem skeleton for a handbook instance repo.
  - Writes only missing files/directories by default.
  - Optional strict mode to ensure required directories exist (fail if missing instead of creating).

Additionally:

- `ph scaffold upgrade` (future)
  - Applies non-destructive upgrades to scaffolded files, guided by a versioned scaffold manifest.

## Template source

Embed the scaffold template inside the installed CLI package so it is:

- versioned together with `ph`,
- available offline,
- testable deterministically.

The template should include:

- directory skeleton (content under `PH_ROOT/**`, internals under `PH_ROOT/.project-handbook/**`),
- minimal seed files that encode conventions (READMEs, example ADRs, `.gitkeep` where appropriate),
- JSON/YAML defaults required by `ph`.

## Root marker and internal state location

Removed. v1 layout is defined by `cli_plan/v1_cli/ADR-CLI-0004-ph-root-layout.md` (marker `.project-handbook/config.json`, internals under `.project-handbook/**`).

## Documentation placement

### Handbook instance repo docs

Keep handbook docs where humans expect them:

- `README.md`, `docs/`, `process/`, `adr/`, etc.

This repo is the “handbook”, so the filesystem should remain human-readable and conventional.

### CLI repo docs

Keep CLI documentation in the CLI repo (MkDocs) and treat it as product docs:

- `project-handbook-cli/docs/**` (or MkDocs-configured docs dir)

Avoid relocating the handbook instance repo’s entire documentation under a new `ph/` directory unless there is a strong, user-facing reason and a migration plan, because it would be a breaking change to links and mental model.
Historical note: an earlier v1 design proposed `ph/**` for content to isolate internals under `.ph/**`, but this approach is superseded by ADR-CLI-0004.

# Options considered

## Option A (recommended): `ph scaffold full` with embedded templates

Pros:
- offline/deterministic,
- testable end-to-end,
- minimal external dependencies.

Cons:
- template updates require `ph` release/versioning discipline,
- must define upgrade semantics to avoid drift.

## Option B: scaffold from a remote template repo

Pros:
- easy to update template content without shipping a new `ph`.

Cons:
- network dependency, non-deterministic, more failure modes.

## Option C: only keep minimal `ph init` and rely on cloning a “starter repo”

Pros:
- simplest CLI implementation.

Cons:
- most error-prone in practice; requires external knowledge and manual steps.

# Migration plan

1. Add `ph scaffold full` (or `ph init --full`) as an *additive* capability.
2. Do not overwrite existing user-authored content without an explicit `--force`.

# Open questions

- Naming: `ph scaffold` vs `ph init --full`.
- Upgrade model: how to update template files without overwriting user modifications (manifest + checksums?).
- Exact scope of “full filesystem” (which directories are required vs optional).
