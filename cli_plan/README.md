---
title: CLI Migration Plan (Versioned)
type: guide
date: 2026-01-13
tags: [handbook, cli, migration, plan]
links:
  - ./v0_make/MAKE_CONTRACT.md
  - ./v1_cli/ADR-CLI-0001-ph-cli-migration.md
  - ./v1_cli/CLI_CONTRACT.md
---

# CLI Migration Plan (Versioned)

This folder is versioned so we can always compare the **current Make-based interface** against the **new CLI interface** during parity work.

## Versions

### `v0_make/`
Authoritative snapshot/contract of the current command surface:
- Make targets (including placeholders/no-ops)
- Hook behavior (history + auto validation)
- Pre-exec gates + release coordination targets

### `v1_cli/`
Authoritative CLI design:
- ADR for the `ph` CLI migration
- CLI contract (command tree, hints, hooks, skip rules)

## Parity rule

`v1_cli` MUST preserve the intent and ergonomics of `v0_make` where applicable, while improving usability by ensuring the CLI can bootstrap a repo (`ph init`) and scaffold required files/directories (so commands don’t assume a pre-existing handbook filesystem).

## Task queues

- `cli_plan/archive/tasks_legacy.json`: historical migration task queue (complete; kept as an audit trail).
- `cli_plan/tasks_v1_parity.json`: strict parity queue (one checkbox per task from `cli_plan/PARITY_CHECKLIST.md`).
- `cli_plan/tasks_v1_next.json`: active incremental v1 task queue (preferred for new work).
