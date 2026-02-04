---
title: PH Spec Contract — status/daily/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/status/daily/`
- Summary: Daily status updates written as dated Markdown files under `daily/YYYY/MM/DD.md` (month partition, filename is the day number).

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `**/*.md` (one dated daily status file per day, if used)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none)
- Overwrite rules:
  - The CLI MUST NOT overwrite an existing daily status file without explicit `--force`.

## Creation
- Created/updated by:
  - `ph daily generate` (creates today’s daily status file; weekend-aware by default)
  - `ph daily generate --force` (creates today’s daily status file even on weekends)
  - `ph daily check --verbose` (read-only; warns if daily is missing/stale)
  - `pnpm make -- daily` (creates today’s daily status file; weekend-aware by default)
  - `pnpm make -- daily-force` (creates today’s daily status file even on weekends)
  - `pnpm make -- daily-check` (read-only; warns if daily is missing/stale)
- Non-destructive:
  - The CLI MUST NOT overwrite an existing daily status file without explicit `--force`.

## Required Files and Directories
- None. This directory MAY be empty.

## Schemas
- Daily status files MUST follow this path pattern:
  - `YYYY/MM/DD.md` (where `DD.md` is the day-of-month, zero-padded)
- Each daily status file MUST be Markdown with YAML front matter containing at least:
  - `title: <string>`
  - `type: status-daily`
  - `date: YYYY-MM-DD` (MUST match the path)
  - `sprint: SPRINT-...` (the current sprint id)
  - `tags: [status, daily, ...]`
- YAML front matter MAY include additional keys; unknown keys MUST be preserved.

## Invariants
- There MUST be at most one daily status file per date (`date` is unique).
- If a daily status file exists at `YYYY/MM/DD.md`, its front matter `date` MUST equal `YYYY-MM-DD`.

## Validation Rules
- `ph validate` SHOULD enforce (best-effort):
  - daily files match the `YYYY/MM/DD.md` path pattern
  - required front matter keys exist (`type`, `date`, `sprint`)
  - `date` front matter matches the path

## Examples Mapping
- `examples/2026/01/03.md` demonstrates a daily status entry with the required front matter keys and a typical section layout.
