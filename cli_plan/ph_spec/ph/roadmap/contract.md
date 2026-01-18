---
title: PH Spec Contract — ph/roadmap/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: Roadmap container for a single canonical “Now / Next / Later” roadmap document consumed by `ph roadmap *`.

## Ownership
- Owner: Project (human-directed).
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `*.md` (roadmap docs such as `now-next-later.md`)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none)
- Overwrite rules:
  - The CLI MUST NOT overwrite roadmap docs without explicit `--force`.

## Creation
- Created/updated by:
  - `ph init` (creates `ph/roadmap/` and seeds `now-next-later.md` if missing).
  - `ph roadmap create` (creates `roadmap/now-next-later.md` if missing).
  - Humans edit roadmap content directly; `ph roadmap show`/`validate` are read-only.
- Non-destructive:
  - The CLI MUST NOT overwrite `now-next-later.md` without explicit `--force`.

## Required Files and Directories
- Required files:
  - `now-next-later.md`

## Schemas
- `now-next-later.md` MUST be Markdown with YAML front matter containing at least:
  - `title: <string>`
  - `type: roadmap`
  - `date: YYYY-MM-DD`
- `now-next-later.md` body MUST include these headings (exact text):
  - `# Now / Next / Later Roadmap`
  - `## Now`
  - `## Next`
  - `## Later`
- YAML front matter MAY include additional keys; unknown keys MUST be preserved.

## Invariants
- There is exactly one canonical roadmap file for v1:
  - `ph/roadmap/now-next-later.md`

## Validation Rules
- `ph roadmap validate` MUST enforce:
  - `roadmap/now-next-later.md` exists
  - required headings exist (`Now`/`Next`/`Later`)
  - markdown links that resolve to `PH_ROOT/**` exist on disk (relative links)
- `ph validate` SHOULD enforce the same file presence and required-heading rules (links may be validated via `ph roadmap validate`).

## Examples Mapping
- `examples/now-next-later.md` demonstrates the required roadmap front matter and required headings.
