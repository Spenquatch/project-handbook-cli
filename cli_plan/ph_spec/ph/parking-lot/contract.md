---
title: PH Spec Contract — parking-lot/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/parking-lot/`
- Summary: A categorized parking lot for ideas/requests that are not yet promoted into the roadmap/backlog.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `features/**/README.md`
  - `technical-debt/**/README.md`
  - `research/**/README.md`
  - `external-requests/**/README.md`
  - `archive/**/README.md` (archived items; treated as immutable content)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - `index.json` (catalog of parking-lot items and metadata)
- Overwrite rules:
  - The CLI MAY regenerate `index.json`.
  - The CLI MUST NOT overwrite any `README.md` content without explicit `--force`.

## Creation
- Created/updated by:
  - `ph parking add --type <category> --title "..." [--desc "..."] [--owner @handle] [--tags "a,b"]` (creates new item directories and updates `index.json`).
  - `ph parking list ...` / `ph parking review` (reads `index.json`; may rebuild it from filesystem if missing/stale).
  - `ph parking promote --item <ID> [--target now|next|later]` (records promotion metadata; does not remove the item by default).
  - `pnpm make -- parking-add type=<category> title="..." [desc="..."] [owner=@handle] [tags="a,b"]` (creates new item directories and updates `index.json`).
  - `pnpm make -- parking-list ...` / `pnpm make -- parking-review` (reads `index.json`; may rebuild it from filesystem if missing/stale).
  - `pnpm make -- parking-promote item=<ID> [target=now|next|later]` (records promotion metadata; does not remove the item by default).
  - Items are archived by moving item directories into `archive/` (manual or future CLI command).
- Non-destructive:
  - The CLI MUST treat markdown content (`README.md`) as project-owned source-of-truth and refuse to overwrite without explicit flags.

## Required Files and Directories
- Required file:
  - `index.json`
- Required directory:
  - `archive/`
- Category directories (`features/`, `technical-debt/`, `research/`, `external-requests/`) are **created on demand** and MAY be absent when empty.
- Allowed categories (authoritative): `features`, `technical-debt`, `research`, `external-requests`

## Schemas
- `index.json` MUST be valid JSON with this top-level shape:
  - `last_updated: <RFC3339 timestamp | null>`
  - `total_items: <integer>`
  - `by_category: { "features": [<id>...], "technical-debt": [...], "research": [...], "external-requests": [...] }`
  - `items: [ <item>... ]`
- Each `items[]` entry MUST include (at minimum):
  - `id: <string>` (directory name, e.g. `FEAT-20260111-social-login`)
  - `path: <string>` (path relative to `PH_ROOT`, e.g. `parking-lot/features/<id>`)
  - `type: features|technical-debt|research|external-requests` (from `README.md` front matter)
  - `status: parking-lot` (from `README.md` front matter)
  - `created: YYYY-MM-DD` (from `README.md` front matter)
  - `owner: <string>` (from `README.md` front matter)
  - `title: <string>` (from `README.md` front matter)
  - `tags: [<string>...]` (from `README.md` front matter; may be empty)
  - `description: <string>` (legacy; often the first paragraph after front matter)
- `items[]` MAY include additional keys copied from `README.md` front matter; unknown keys MUST be preserved.
- `index.json` MUST catalog only non-archive items under:
  - `features/`
  - `technical-debt/`
  - `research/`
  - `external-requests/`
- `archive/**` items MUST NOT appear in `index.json` (they are immutable records and are handled by archive contracts).
- Parking-lot item `README.md` MUST include YAML front matter with at least:
  - `title: <string>`
  - `type: features|technical-debt|research|external-requests` (MUST match the category directory)
  - `status: parking-lot`
  - `created: YYYY-MM-DD`
  - `owner: <string>` (e.g. `unassigned` or `@handle`)
  - `tags: [<string>, ...]` (may be empty)
- YAML front matter MAY include additional keys; unknown keys MUST be preserved as content.

## Invariants
- `parking-lot/` MUST contain only:
  - `index.json`
  - category directories (created on demand)
  - `archive/`
- All IDs listed in `by_category` MUST appear exactly once in `items[]`.
- All `items[].path` values MUST be under `parking-lot/` and MUST NOT point into `parking-lot/archive/`.

## Validation Rules
- `allowed_categories` MUST match `process/checks/validation_rules.json` (`parking_lot.allowed_categories`).
- `ph validate` SHOULD enforce:
  - `index.json` exists and is valid JSON with the required top-level keys
  - `by_category` is consistent with `items[]` (no missing/unknown IDs)
  - each item directory under `features/`, `technical-debt/`, `research/`, `external-requests/` satisfies its category contract:
    - `parking-lot/features/contract.md`
    - `parking-lot/technical-debt/contract.md`
    - `parking-lot/research/contract.md`
    - `parking-lot/external-requests/contract.md`
  - `archive/` exists and satisfies `parking-lot/archive/contract.md`

## Examples Mapping
- `examples/index.json` demonstrates the `index.json` catalog shape (empty bootstrap case).
