---
id: ADR-CLI-0006
title: Define ADR Conventions + `ph adr add` Contract Surface (BL-0001)
type: adr
status: accepted
date: 2026-02-07
tags: [cli, adr, validation, contract]
links:
  - ./CLI_CONTRACT.md
  - ./ADR-CLI-0004-ph-root-layout.md
---

# Context

The Project Handbook uses Architectural Decision Records (ADRs) under `PH_ROOT/adr/`.

For ADRs to be:

- discoverable (predictable filenames),
- diffable (stable structure),
- validateable (deterministic rules and actionable errors),

we need a strict, documented convention and a single CLI entrypoint (`ph adr add`) that generates compliant ADRs by default.

Separately, `ph validate` needs strict ADR checks for `adr/*.md` as part of the v1 CLI contract (BL-0001).

# Decision

## Scope

This ADR defines conventions for **handbook ADR content** under `PH_ROOT/adr/` and the `ph adr add` contract surface.

It does not change the naming of internal planning ADRs under `cli_plan/v1_cli/ADR-CLI-*.md`.

## ADR location

- ADR markdown files live under `PH_ROOT/adr/` (repo root content tree).

## Strict ADR conventions (errors)

`ph validate` MUST treat the following as **errors** for each ADR markdown file under `PH_ROOT/adr/`:

1. Filename MUST match: `NNNN-<slug>.md`
   - `NNNN`: 4 digits (`0000`–`9999`)
   - `<slug>`: lowercase kebab-case
2. YAML front matter `id` MUST exist and MUST equal `ADR-NNNN` where `NNNN` matches the filename numeric prefix.
3. The ADR body MUST include the required H1 headings (exact spelling, H1 only):
   - `# Context`
   - `# Decision`
   - `# Consequences`
   - `# Acceptance Criteria`
4. ADR ids MUST be unique across `PH_ROOT/adr/*.md` (no duplicate `id: ADR-NNNN` across multiple files).
5. If YAML front matter `status: superseded`, then `superseded_by: ADR-NNNN` MUST be present and MUST reference an existing ADR under `PH_ROOT/adr/`.

## Recommended ADR convention (warning)

`ph validate` SHOULD treat the following as a **warning**:

- missing `# Rollout` (exact spelling, H1 only)

## `ph adr add` contract surface

`ph adr add` MUST generate ADR files that comply with the strict conventions above and is specified as authoritative in:

- `cli_plan/v1_cli/CLI_CONTRACT.md` (section: `ph adr`)

Key guarantees:

- Target path MUST be `adr/NNNN-<slug>.md` derived deterministically from `--id` and `--title`.
- Generated YAML front matter MUST include at least `id`, `title`, `type`, `status`, `date`.
- If generated front matter includes `status: superseded`, it MUST also include `superseded_by: ADR-NNNN` and the referenced ADR MUST exist under `PH_ROOT/adr/`.
- Generated file body MUST include the required H1 headings listed above.
- Generated file body MUST include `# Rollout` (recommended; missing triggers a warning during validation).
- By default, the command MUST be non-destructive and refuse to overwrite an existing ADR file.

### Internal-only escape hatch: `--force` (hidden)

`ph adr add` MUST support an internal-only `--force` escape hatch that:

- MUST NOT appear in CLI help output,
- is non-destructive (never modifies existing ADR content),
- allows idempotent success when the target ADR file already exists.

This option may be documented only in internal docs/contracts (not in CLI help text / README).

## Actionable validation output (required)

ADR validation errors and warnings MUST be actionable:

- include the ADR file path,
- include expected vs found values (where applicable),
- for heading checks:
  - include `missing: [...]` (in required order), and
  - include `found_h1: [...]` (in document order).

These requirements are normative for the v1 CLI contract.

# Consequences

## Positive

- ADRs become uniform and tool-friendly (creation, indexing, linting).
- Validation failures become quick to remediate (actionable expected/found + missing lists).

## Negative / tradeoffs

- Existing non-compliant ADRs must be renamed/edited to satisfy strict conventions.
- Strictness may initially feel “picky”, but it prevents long-term drift.

# Acceptance Criteria

- `cli_plan/v1_cli/CLI_CONTRACT.md` specifies `ph adr add` behavior and ADR validation rules without contradiction.
- The contract and this ADR both document that `--force` exists but is hidden from help output and is non-destructive.
- ADR validation requirements clearly distinguish errors vs warnings and require actionable outputs.

# Rollout

- Ensure `ph validate` includes the strict ADR checks for `adr/*.md`.
- Ensure `ph adr add` generates compliant ADRs and hides `--force` from help output.
