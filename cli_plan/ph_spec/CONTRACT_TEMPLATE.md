# Contract

## Directory Purpose
- Path: (directory containing this `contract.md`)
- Summary: (TBD)

## Ownership
- Owner: Project (human-directed) | CLI | Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - (TBD; list concrete filenames/patterns)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (TBD; list concrete filenames/patterns)
- Overwrite rules:
  - The CLI MUST treat content artifacts as project-owned source-of-truth even if they were created/edited by AI agents using `ph`.
  - The CLI MUST NOT overwrite content artifacts unless the operator passes an explicit `--force` (or runs a dedicated update command for that artifact).
  - The CLI MAY regenerate derived/internal artifacts, but MUST NOT silently delete project-owned content.

## Creation
- Created/updated by: (TBD; `ph ...` commands)
- Non-destructive: MUST NOT overwrite user-owned files without explicit flags

## Required Files and Directories
- (TBD)

## Schemas
- (TBD; file formats, required keys, constraints)

## Invariants
- (TBD)

## Validation Rules
- (TBD; what `ph check` / `ph check-all` should enforce here)

## Examples Mapping
- (TBD; example fixtures that demonstrate this contract)
