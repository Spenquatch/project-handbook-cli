---
title: PH Spec Contract — status/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/status/`
- Summary: Status surfaces for the handbook instance: a generated “current” snapshot, a human-readable summary, validation output, plus subtrees for daily updates, evidence bundles, and export bundles.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `README.md`
  - `evidence/**` (evidence bundles; human-curated)
  - `daily/**` (daily status docs; human-edited unless explicitly generated)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - `current.json` (current status snapshot)
  - `current_summary.md` (current status summary)
  - `validation.json` (latest validation report)
- Overwrite rules:
  - The CLI MAY regenerate `current.json`, `current_summary.md`, and `validation.json`.
  - The CLI MUST NOT overwrite evidence or daily status docs without explicit `--force`.

## Creation
- Created/updated by:
  - `pnpm make -- status` (writes `current.json` and `current_summary.md`)
  - `pnpm make -- validate` / `pnpm make -- validate-quick` (writes `validation.json`)
  - `pnpm make -- daily` / `pnpm make -- daily-force` (writes daily status entries under `daily/` per the daily contract)
  - Humans/agents (evidence bundles, exports, and README edits)
- Non-destructive:
  - The CLI MUST NOT overwrite user-owned files under `status/` (including `README.md`) without explicit `--force`.

## Required Files and Directories
- Required files:
  - `README.md`
- Required directories:
  - `daily/` (see `status/daily/contract.md`)
  - `evidence/` (see `status/evidence/contract.md`)
  - `exports/` (see `status/exports/contract.md`)
- Optional derived files (created on-demand by `ph`):
  - `current.json`
  - `current_summary.md`
  - `validation.json`

## Schemas
- `README.md` MUST be Markdown with YAML front matter containing at least:
  - `title: <string>`
  - `type: process`
  - `date: YYYY-MM-DD`
- `current.json` MUST be a JSON object containing at least:
  - `generated_at` (string; RFC3339 timestamp)
- `validation.json` MUST be a JSON object containing at least:
  - `issues` (array)
    - each issue MUST include:
      - `path` (string)
      - `code` (string)
      - `severity` (`error|warning`)
    - each issue MAY include:
      - `message` (string)
- `current_summary.md` MUST be Markdown intended for humans.
  - It MAY omit YAML front matter (it is explicitly exempted from front-matter enforcement by v1 validation).
  - It SHOULD be overwritten on each `ph status` run.

## Invariants
- `current.json`, `current_summary.md`, and `validation.json` are derived/internal artifacts:
  - the CLI MAY regenerate them at any time
  - humans SHOULD treat them as ephemeral outputs (use git history if you want to persist)
- `daily/`, `evidence/`, and `exports/` are content subtrees owned by their respective contracts.

## Validation Rules
- `ph validate` SHOULD enforce:
  - `README.md` exists and has valid YAML front matter
  - if `current.json` exists, it parses as JSON and contains `generated_at`
  - if `validation.json` exists, it parses as JSON and contains `issues` (array)
  - `current_summary.md` is exempt from front-matter enforcement

## Examples Mapping
- `examples/README.md` demonstrates the status directory README shape.
- `examples/current.json` demonstrates a `current.json` snapshot payload (the CLI MAY add additional fields beyond the minimum contract).
- `examples/validation.json` demonstrates the `validation.json` top-level shape.
- `examples/current_summary.md.example` demonstrates a human-readable summary output (the runtime filename is `current_summary.md`).
