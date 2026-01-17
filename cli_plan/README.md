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
- Make targets and scope variants (`hb-*`)
- Hook behavior (history + auto validation)
- Destructive safety semantics (reset/migration)

### `v1_cli/`
Authoritative CLI design:
- ADR for the `ph` CLI migration
- CLI contract (command tree, hints, hooks, skip rules, scope rules)

## Parity rule

`v1_cli` MUST preserve the intent and ergonomics of `v0_make`, while eliminating Make-specific sources of nondeterminism (especially `cwd` sensitivity).
