---
title: PH Spec Contract — ph/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: Project handbook content root (`PH_CONTENT_ROOT = PH_ROOT/ph`) containing human-authored planning/execution docs (ADR, backlog, features, sprints, status, etc.) and no CLI-owned internals.

## Ownership
- Owner: Shared.
- Definitions:
  - Content artifacts: project-owned, human-directed files under `ph/**` (typically Markdown/YAML). They may be authored/edited by humans *or* AI agents, often via `ph` command inputs.
  - Derived/internal artifacts: machine-managed files under `ph/**` (indexes, catalogs, exports, reports) that are explicitly declared safe to regenerate by the contract for that directory.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - Default: everything under `ph/**` unless a directory contract explicitly lists it as derived/internal.
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - MUST be explicitly listed (by filename) in the directory contract that owns them.
- Default policy:
  - Everything under `ph/**` is treated as content unless a directory contract explicitly lists it as an internal artifact.
  - A directory contract MUST list internal artifacts by concrete filename(s) (not only by extension) when regeneration is allowed.
- Overwrite rules:
  - The CLI MUST NOT overwrite content artifacts without explicit `--force`.
  - The CLI MAY regenerate internal artifacts, but MUST NOT delete or mutate content artifacts as a side effect.

## Creation
- Created/updated by:
  - `ph init` (creates the `ph/**` content tree alongside `.ph/**` internals; non-destructive).
  - Most `ph` subcommands read/write content under this tree (see subdirectory contracts).
- Non-destructive:
  - `ph init` MUST NOT overwrite existing content files.
  - `ph` commands that edit content artifacts MUST require an explicit `--force` (or a dedicated update command) before overwriting project-owned files.

## Required Files and Directories
- Required directories under `ph/`:
  - `adr/`
  - `backlog/`
  - `contracts/`
  - `decision-register/`
  - `features/`
  - `parking-lot/`
  - `releases/`
  - `roadmap/`
  - `sprints/`
  - `status/`
- Optional files:
  - `README.md` (project-owned overview; ignored by the CLI)

## Schemas
- There is no root-level schema for `ph/`.
- Content schemas are owned by subdirectories; most primary artifacts are Markdown/YAML governed by the relevant directory contract.

## Invariants
- The project content root MUST be a directory at `PH_ROOT/ph`.
- CLI internals MUST NOT live under `ph/`:
  - `.ph/` is a sibling of `ph/` at `PH_ROOT/.ph` and MUST NOT appear under `ph/**`.

## Validation Rules
- `ph validate` SHOULD enforce:
  - required top-level directories exist under `ph/`
  - each required subdirectory satisfies its contract:
    - `ph/adr/contract.md`
    - `ph/backlog/contract.md`
    - `ph/contracts/contract.md`
    - `ph/decision-register/contract.md`
    - `ph/features/contract.md`
    - `ph/parking-lot/contract.md`
    - `ph/releases/contract.md`
    - `ph/roadmap/contract.md`
    - `ph/sprints/contract.md`
    - `ph/status/contract.md`
  - unknown top-level entries under `ph/` SHOULD be reported as warnings (to catch typos) but MUST NOT break normal operation.

## Examples Mapping
- `examples/adr/0007-tribuence-mini-v2-supergraph-context.md` demonstrates an ADR content artifact.
- `examples/backlog/bugs/EXAMPLE-BUG-P0-20250922-1144/` demonstrates a bug backlog item directory (`README.md` + optional `triage.md`).
- `examples/features/v2_launch/` demonstrates feature docs (`overview.md`, `risks.md`, `status.md`, `changelog.md`).
- `examples/roadmap/now-next-later.md` demonstrates a roadmap seed document.
- `examples/sprints/2026/SPRINT-2026-01-11/plan.md` demonstrates a sprint plan.
- `examples/status/current_summary.md.example` demonstrates a status summary artifact shape.
