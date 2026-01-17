---
title: Investigate: Context control plane schema migration + wrapper consumption contract - Commands
type: commands
date: 2026-01-11
task_id: TASK-029
tags: [commands]
links: []
---

# Commands: Investigate: Context control plane schema migration + wrapper consumption contract

## Task Status
```bash
ph task status --id TASK-029 --status doing
ph task status --id TASK-029 --status review
ph task status --id TASK-029 --status done
```

## Evidence Directory (required)
```bash
EVID_DIR="ph/status/evidence/TASK-029"
mkdir -p "$EVID_DIR"
${EDITOR:-vi} "$EVID_DIR/index.md"
```

## Read Context (capture as evidence)
```bash
set -euo pipefail

sed -n '1,260p' ph/adr/0027-v2-context-control-plane-schema.md | tee "$EVID_DIR/adr-0027.txt"
DR_PATH="ph/features/v2_context-control-plane-schema/decision-register/DR-0001-context-control-plane-migration-and-consumption-contract.md"
${EDITOR:-vi} "$DR_PATH"
```

## Inventory current Context surfaces (repo inspection only)
```bash
find v2/services/context -maxdepth 3 -type f -print | tee "$EVID_DIR/context-files.txt"
rg -n 'type Query|schema\\s*\\{|Workspace|capability|manifest|status|link|job|run' v2/services/context -S | tee "$EVID_DIR/context-schema-notes.txt" || true
find v2/services/context -maxdepth 5 -type f \( -name '*migrat*' -o -name '*.sql' \) -print | tee "$EVID_DIR/context-migrations-inventory.txt" || true
```

## Handbook Validation
```bash
ph validate
```
