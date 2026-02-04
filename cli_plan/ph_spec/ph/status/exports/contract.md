---
title: PH Spec Contract — status/exports/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/status/exports/`
- Summary: CLI-generated export bundles (typically tarballs) intended for sharing handbook artifacts (plans, docs, reports) outside the repo while keeping contents deterministic and reviewable.

## Ownership
- Owner: CLI.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - (none)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - `*.tar.gz` (export bundle)
  - `*.tar.gz.sha256`
  - `*.manifest.txt`
  - `*.paths.txt`
  - `*.README.txt`
- Overwrite rules:
  - The CLI MAY regenerate exports, but SHOULD avoid collisions by choosing deterministic, unique names; it MUST NOT overwrite an existing export file unless `--force` is provided.

## Creation
- Created/updated by:
  - Directory may be created manually or by future tooling (it is not required by the legacy Make automation).
  - Export tooling/automation (future `ph export ...` commands; or external scripts) MAY create bundles in this directory.
- Non-destructive:
  - The CLI MUST NOT overwrite an existing export file unless `--force` is provided.

## Required Files and Directories
- None. This directory MAY be empty.

## Schemas
- Export bundles SHOULD be written as a group of files sharing a common base name:
  - `<base>.tar.gz` (the bundle)
  - `<base>.tar.gz.sha256` (checksum for the tarball)
  - `<base>.paths.txt` (newline-delimited list of repo-relative paths included)
  - `<base>.manifest.txt` (human-readable manifest describing what was included)
  - `<base>.README.txt` (human-readable purpose + extraction instructions)
- `<base>.tar.gz.sha256` MUST contain a single line in the format:
  - `<64-hex>  ph/status/exports/<base>.tar.gz`
- `<base>.paths.txt` MUST be newline-delimited, repo-relative paths (no leading `/`).
- `<base>.manifest.txt` SHOULD be a stable, human-readable description and SHOULD include the exact path list (or reference `<base>.paths.txt`).
- Export tooling MUST NOT include secrets in bundles; by default, evidence directories (e.g. `ph/status/evidence/`) SHOULD be excluded.

## Invariants
- Export bundle companion files MUST share the same base name as the tarball.
- If a `<base>.tar.gz.sha256` file exists, it MUST correspond to an existing `<base>.tar.gz` file in the same directory.

## Validation Rules
- `ph validate` SHOULD treat exports as best-effort:
  - it MAY verify that `*.tar.gz.sha256` files follow the required line format
  - it MAY warn if a checksum exists without a corresponding tarball (or vice versa)

## Examples Mapping
- `examples/SPRINT-2026-01-11-doc-review.tar.gz` demonstrates a documentation review export bundle.
- `examples/SPRINT-2026-01-11-doc-review.tar.gz.sha256` demonstrates the checksum file format.
- `examples/SPRINT-2026-01-11-doc-review.paths.txt` demonstrates a bundle path list.
- `examples/SPRINT-2026-01-11-doc-review.manifest.txt` demonstrates a human-readable manifest.
- `examples/SPRINT-2026-01-11-doc-review.README.txt` demonstrates a bundle README.
