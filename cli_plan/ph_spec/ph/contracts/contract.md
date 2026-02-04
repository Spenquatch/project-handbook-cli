---
title: PH Spec Contract — contracts/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/contracts/`
- Summary: Project-owned contract documents (Markdown/JSON) that define stable interfaces, inventories, and invariants (e.g. API endpoint contracts) referenced by ADRs, tasks, and validation evidence.

## Ownership
- Owner: Project (human-directed).
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `**/*.md` (contract docs)
  - `**/*.json` (when used as a human-maintained contract artifact)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none)
- Overwrite rules:
  - The CLI MUST NOT overwrite or rewrite contract artifacts under `contracts/`.

## Creation
- Created/updated by:
  - Humans (or agents directed by humans) author and maintain the contract artifacts; the CLI treats this directory as read-only content.
- Non-destructive:
  - The CLI MUST NOT create, modify, or delete contract artifacts under `contracts/` during normal operation.

## Required Files and Directories
- Required:
  - `contracts/` (directory)
- Optional:
  - Any subdirectories (e.g. `api/`) used to group related contracts.
  - `README.md` files for navigation within subtrees.

## Schemas
- Markdown contracts (`**/*.md`):
  - MAY include YAML front matter.
  - If YAML front matter is present, it MUST be valid YAML.
- JSON contract artifacts (`**/*.json`):
  - MUST be valid JSON.
  - If an `api/api-contracts.json` registry is present, the recommended shape is:
    - `updated_at: YYYY-MM-DD`
    - `contracts: [ { id, service, audience, method, path, owner, status, doc, ... }... ]`

## Invariants
- This directory is project-owned and treated as source-of-truth:
  - Contract artifacts MUST NOT be regenerated from derived state.
  - Contract artifacts MUST NOT be overwritten without explicit operator intent.

## Validation Rules
- `ph validate` SHOULD enforce:
  - `contracts/` exists
  - any `*.json` files present are parseable as JSON (warn if invalid; do not mutate)
- `ph` commands MUST treat contract artifacts as read-only unless a future, explicitly-scoped command is introduced for updating them.

## Examples Mapping
- `examples/inventory.md` demonstrates a human-maintained inventory contract document with front matter and verification notes.
- `examples/api/` demonstrates an API contracts subtree:
  - `examples/api/README.md` (subtree overview)
  - `examples/api/api-contracts.json` (registry manifest)
  - `examples/api/*.md` (endpoint contracts)
