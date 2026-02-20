---
title: PH Spec Contract — ph/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/`
- Summary: Project handbook **instance root** containing human-authored planning/execution docs (ADR, backlog, features, sprints, status, etc.). The v1 CLI (`ph`) adopts the **Make-era repo-root layout**; legacy automation used `pnpm make -- <target>`.

## Ownership
- Owner: Shared.
- Definitions:
  - Content artifacts: project-owned, human-directed files under `PH_ROOT/**` (typically Markdown/YAML). They may be authored/edited by humans *or* AI agents, often via `make`/`ph` command inputs.
  - Derived/internal artifacts: machine-managed files under `PH_ROOT/**` (indexes, catalogs, exports, reports) that are explicitly declared safe to regenerate by the contract for that directory.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - Default: everything under `PH_ROOT/**` unless a directory contract explicitly lists it as derived/internal.
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - MUST be explicitly listed (by filename) in the directory contract that owns them.
- Default policy:
  - Everything under `PH_ROOT/**` is treated as content unless a directory contract explicitly lists it as an internal artifact.
  - A directory contract MUST list internal artifacts by concrete filename(s) (not only by extension) when regeneration is allowed.
- Overwrite rules:
  - Automation MUST NOT overwrite content artifacts without explicit operator intent (or a `--force` mode where supported).
  - The CLI MAY regenerate internal artifacts, but MUST NOT delete or mutate content artifacts as a side effect.

## Creation
- Created/updated by:
  - `ph init`: bootstraps a new instance repo by scaffolding the canonical directory tree and required process assets (non-destructive).
  - `ph <domain> ...`: domain commands scaffold new content and regenerate internal artifacts they own.
  - `pnpm make -- <target>` (legacy): writes/updates derived artifacts and scaffolds new content per domain (`task-create`, `backlog-add`, `parking-add`, etc.).
  - Humans/agents: create/edit most Markdown content directly.
- Non-destructive:
  - Generators MUST refuse to overwrite existing content files by default (unless the command explicitly supports a `--force` mode).

## Required Files and Directories
- Required marker file:
  - `.project-handbook/config.json` (defines `PH_ROOT`; used by `ph` root detection)
- Common entrypoint doc (required for `ph onboarding`):
  - `ONBOARDING.md`
- Required directories under `PH_ROOT/`:
  - `adr/`
  - `assets/` (optional contents; directory SHOULD exist)
  - `backlog/`
  - `contracts/`
  - `decision-register/`
  - `docs/` (optional; validation rules typically skip `docs/**`)
  - `features/`
  - `parking-lot/`
  - `process/` (automation + validation rules + session templates)
  - `releases/`
  - `roadmap/`
  - `sprints/`
  - `status/`
  - `tools/` (optional)
- Optional internal directory:
  - `.project-handbook/` (automation-owned; history + system-scope data root)
- Optional files:
  - `README.md` (project-owned overview; ignored by the CLI)

## Schemas
- There is no root-level schema for `PH_ROOT/`.
- Content schemas are owned by subdirectories; most primary artifacts are Markdown/YAML governed by the relevant directory contract.

## Invariants
- The handbook instance root MUST be a directory at `PH_ROOT/`.
- Automation-owned internals MUST live under `.project-handbook/` (not alongside the primary content trees):
  - `.project-handbook/history.log` (append-only command history)
  - `.project-handbook/**` SHOULD NOT be used for content artifacts; it is reserved for automation internals.

## Validation Rules
- `ph validate` SHOULD enforce:
  - required top-level directories exist under `PH_ROOT/`
  - each required subdirectory satisfies its contract:
    - `adr/contract.md`
    - `backlog/contract.md`
    - `contracts/contract.md`
    - `decision-register/contract.md`
    - `features/contract.md`
    - `parking-lot/contract.md`
    - `releases/contract.md`
    - `roadmap/contract.md`
    - `sprints/contract.md`
    - `status/contract.md`
  - unknown top-level entries under `PH_ROOT/` SHOULD be reported as warnings (to catch typos) but MUST NOT break normal operation.

## Examples Mapping
- `examples/adr/0007-tribuence-mini-v2-supergraph-context.md` demonstrates an ADR content artifact.
- `examples/backlog/bugs/EXAMPLE-BUG-P0-20250922-1144/` demonstrates a bug backlog item directory (`README.md` + optional `triage.md`).
- `examples/features/v2_launch/` demonstrates feature docs (`overview.md`, `risks.md`, `status.md`, `changelog.md`).
- `examples/roadmap/now-next-later.md` demonstrates a roadmap seed document.
- `examples/sprints/2026/SPRINT-2026-01-11/plan.md` demonstrates a sprint plan.
- `examples/status/current_summary.md.example` demonstrates a status summary artifact shape.
