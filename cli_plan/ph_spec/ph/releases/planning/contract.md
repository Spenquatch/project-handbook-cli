---
title: PH Spec Contract — releases/planning/ (reserved)
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/releases/planning/` (optional; may be absent)
- Summary: Optional staging area for draft/next release planning artifacts. The legacy automation does not read/write here.

## Ownership
- Owner: Project (human-authored).
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `**/*` (all files in this subtree)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none)
- Mutability: Human-edited only (v1 `ph release *` commands do not read/write here).
- Overwrite rules:
  - The CLI MUST NOT overwrite any files here.

## Creation
- Created by: manual (optional; not required by `pnpm make` targets).
- Non-destructive: CLI MUST NOT overwrite any files here.

## Required Files and Directories
- No required files for v1.

## Schemas
- There is no required schema for this directory in v1; it is an operator-managed staging area.
- If Markdown files are present:
  - They MUST include YAML front matter (global `ph/` rule).
  - A recommended shape for release summary docs is:
    - `title: <string>`
    - `type: release`
    - `version: vX.Y.Z`
    - `date: YYYY-MM-DD`
    - `tags: [release, ...]`
    - `links: [<relative path>, ...]`

## Invariants
- This directory MUST NOT be required for legacy command execution:
  - `make release-*` commands operate on `releases/vX.Y.Z/` and `releases/current`.

## Validation Rules
- `ph validate` SHOULD:
  - treat this directory as optional,
  - verify any `*.md` files present have parseable YAML front matter,
  - avoid enforcing additional structure (it is an operator-managed staging area).

## Examples Mapping
- `examples/EXAMPLE-v0.1.0.md` demonstrates a lightweight release summary document stored in the planning area.
