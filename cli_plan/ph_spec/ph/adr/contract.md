---
title: PH Spec Contract — adr/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/adr/`
- Summary: Human-authored Architecture Decision Records (ADRs) captured as individual Markdown files with required front matter.

## Ownership
- Owner: Project (human-directed).
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `*.md` ADR files (one decision per file).
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none)
- Overwrite rules:
  - The CLI MUST NOT modify existing ADR files.
  - The CLI MAY scaffold a new ADR file, but MUST refuse if the target path already exists unless `--force` is provided.

## Creation
- Created/updated by:
  - Humans create/edit ADR Markdown files directly.
  - The CLI MAY scaffold a new ADR file via `ph adr add`.
- Non-destructive:
  - The CLI MUST NOT overwrite or modify existing ADR files.
  - If `ph adr add` targets an existing ADR path, it MUST fail unless `--force` is provided.
  - With `--force`, `ph adr add` MUST succeed without modifying the existing file (idempotent “already exists” success).

## Required Files and Directories
- Required files: (none)
- Allowed files:
  - `NNNN-<slug>.md` where:
    - `NNNN` is a 4-digit zero-padded number (e.g. `0007`), and
    - `<slug>` is lowercase kebab-case (required).

## Schemas
- ADR markdown files MUST include YAML front matter with at least:
  - `id: ADR-NNNN` (MUST match the filename numeric prefix)
  - `title: <string>`
  - `type: adr`
  - `status: draft|accepted|rejected|superseded`
  - `date: YYYY-MM-DD`
- Optional front matter fields (recommended):
  - `tags: [<tag>, ...]`
  - `links: [<relative path>, ...]`
  - `supersedes: ADR-NNNN | null`
  - `superseded_by: ADR-NNNN | null`

## Invariants
- One decision per file: each ADR file represents exactly one ADR (`id` is unique within the repo).
- Filename/id alignment: if the filename begins with `NNNN-`, the front matter `id` MUST be `ADR-NNNN`.
- Supersession consistency:
  - If `status: superseded`, `superseded_by` MUST be set to an ADR id.
  - If `superseded_by` is set, the referenced ADR file SHOULD exist under `adr/`.

## Validation Rules
- `ph validate` MUST enforce:
  - front matter exists (global rule)
  - ADR filename matches `NNNN-<slug>.md` and `id: ADR-NNNN` matches the filename numeric prefix
  - `type: adr`
  - `status` is one of `draft|accepted|rejected|superseded`
  - Required H1 headings exist (exact spelling, H1 only):
    - `# Context`
    - `# Decision`
    - `# Consequences`
    - `# Acceptance Criteria`
  - Recommended H1 heading (warning if missing):
    - `# Rollout`
- If `superseded_by` is set, validation SHOULD confirm the referenced ADR exists.

## Examples Mapping
- `examples/0007-tribuence-mini-v2-supergraph-context.md` demonstrates:
  - required front matter keys and allowed values,
  - link conventions via repo-relative `links:` entries,
  - typical ADR section structure (`Context`, `Decision`, `Consequences`, etc.).
