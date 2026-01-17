---
title: Investigate: Context control plane schema migration + wrapper consumption contract - Validation Guide
type: validation
date: 2026-01-11
task_id: TASK-029
tags: [validation]
links: []
---

# Validation Guide: Investigate: Context control plane schema migration + wrapper consumption contract

## Automated Validation
```bash
ph validate
ph sprint status
```

## Pass/Fail Criteria
- `ph/features/v2_context-control-plane-schema/decision-register/DR-0001-context-control-plane-migration-and-consumption-contract.md` exists and ends with an explicit operator approval request (status remains `Proposed`).
- Feature docs are updated to be execution-ready (architecture + implementation reflect the recommended option as “pending approval”).

## Evidence (required)
- `ph/status/evidence/TASK-029/index.md`
- `ph/status/evidence/TASK-029/adr-0027.txt`
- `ph/status/evidence/TASK-029/context-files.txt`
- `ph/status/evidence/TASK-029/context-schema-notes.txt`
- `ph/status/evidence/TASK-029/context-migrations-inventory.txt`

## Sign-off
- [ ] All validation steps completed
- [ ] Evidence documented above
- [ ] Ready to mark task as "done"
