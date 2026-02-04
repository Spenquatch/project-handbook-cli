---
title: PH Spec Contract — backlog/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/backlog/`
- Summary: Primary backlog container for active backlog items (bugs, wildcards, work-items) plus a derived `index.json` catalog; also contains an `archive/` subtree for immutable historical records.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `bugs/**/README.md`
  - `bugs/**/triage.md` (optional)
  - `work-items/**/README.md`
  - `wildcards/**/README.md`
  - `archive/**/README.md` (archived items; treated as immutable content)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - `index.json` (catalog of backlog items and metadata)
- Overwrite rules:
  - The CLI MAY regenerate `index.json`.
  - The CLI MUST NOT overwrite any `README.md` content (or `triage.md`) without explicit `--force`.

## Creation
- Created/updated by:
  - `pnpm make -- backlog-add ...` (creates a new item directory under `backlog/<bugs|wildcards|work-items>/<ID>/` and updates `index.json`).
  - `pnpm make -- backlog-list ...` / `pnpm make -- backlog-stats` (reads `index.json`; may rebuild it from filesystem if missing/stale).
  - `pnpm make -- backlog-triage issue=<ID>` (may create `triage.md` for P0s; updates `index.json`).
  - `pnpm make -- backlog-assign issue=<ID> [sprint=current|next|SPRINT-...]` (records `sprint:` in the item front matter; updates `index.json`).
  - Items are archived by moving item directories into `archive/` (manual or future CLI command).
- Non-destructive:
  - The CLI MUST treat markdown content (`README.md`, `triage.md`) as project-owned source-of-truth and refuse to overwrite without explicit flags.

## Required Files and Directories
- Required directories:
  - `bugs/`
  - `wildcards/`
  - `work-items/`
  - `archive/`
- Required files:
  - `index.json`

## Schemas
- `index.json` MUST be valid JSON with this top-level shape:
  - `last_updated: <RFC3339 timestamp | null>`
  - `total_items: <integer>`
  - `by_severity: { "P0": [<id>...], "P1": [...], "P2": [...], "P3": [...], "P4": [...] }`
  - `by_category: { "bugs": [<id>...], "wildcards": [<id>...], "work-items": [<id>...] }`
  - `items: [ <item>... ]`
- Each `items[]` entry MUST include (at minimum):
  - `id: <string>` (directory name, e.g. `BUG-P2-20260101-120000`)
  - `path: <string>` (path relative to `PH_ROOT`, e.g. `backlog/bugs/<id>`)
  - `type: bugs|wildcards|work-items` (from `README.md` front matter)
  - `severity: P0|P1|P2|P3|P4` (from `README.md` front matter)
  - `status: <string>` (from `README.md` front matter; commonly `open`)
  - `created: YYYY-MM-DD` (from `README.md` front matter)
  - `owner: <string>` (from `README.md` front matter)
  - `title: <string>` (from `README.md` front matter)
  - `has_triage: <boolean>` (true iff `<item_dir>/triage.md` exists)
- `items[]` SHOULD include (legacy):
  - `input_type: <string>` (original intake classification; preserved in front matter)
  - `sprint: <string>` (when assigned via `backlog-assign`; may be absent)
- `items[]` MAY include additional keys copied from `README.md` front matter; unknown keys MUST be preserved.
- `index.json` MUST catalog only non-archive items under:
  - `bugs/`
  - `wildcards/`
  - `work-items/`
- `archive/**` items MUST NOT appear in `index.json` (they are immutable records and are handled by archive contracts).

## Invariants
- `backlog/` MUST contain only:
  - `index.json`
  - `bugs/`
  - `wildcards/`
  - `work-items/`
  - `archive/`
- All IDs listed in `by_category` MUST appear exactly once in `items[]`.
- All IDs listed in `by_severity` MUST appear in `items[]` and MUST match the corresponding `items[].severity`.

## Validation Rules
- `ph validate` SHOULD enforce:
  - required directories exist
  - `index.json` exists and is valid JSON with the required top-level keys
  - `by_category` and `by_severity` are consistent with `items[]` (no missing/unknown IDs)
  - each item directory under `bugs/`, `wildcards/`, `work-items/` satisfies its category contract:
    - `backlog/bugs/contract.md`
    - `backlog/wildcards/contract.md`
    - `backlog/work-items/contract.md`
  - `archive/` exists and satisfies `backlog/archive/contract.md`

## Examples Mapping
- `examples/bugs/EXAMPLE-BUG-P0-20250922-1144/` demonstrates a bug item directory (README + optional triage).
- `examples/wildcards/WILD-P2-20260103-2109/` demonstrates a wildcard item directory (README).
- `examples/work-items/WORK-P2-20260106-213751/` demonstrates a work-item directory (README).
