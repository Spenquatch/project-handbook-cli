---
title: Investigate: Router consumes Cosmo supergraph (pull model + auth + refresh) - Validation Guide
type: validation
date: 2026-01-09
task_id: TASK-003
tags: [validation]
links: []
---

# Validation Guide: Investigate: Router consumes Cosmo supergraph (pull model + auth + refresh)

## Automated Validation
```bash
ph validate
ph sprint status
```

## Manual Validation (pass/fail)
1. DR completeness:
   - `ph/decision-register/DR-0005-router-supergraph-consumption-from-cosmo.md` has no “Pending research…” placeholders.
   - Exactly two options exist (A and B), and the DR ends with an approval request.
2. Feature implementation doc updated (execution-ready plan):
   - `ph/features/v2_schema-publishing-and-composition/implementation/IMPLEMENTATION.md` includes auth material requirements, refresh model, and exact v2 file paths to change.
3. Evidence present and referenced:
   - `ph/status/evidence/TASK-003/index.md` exists and links to evidence files.
   - Evidence naming + redaction follows: `ph/status/evidence/TASK-005/README.md`

Minimum evidence files (per `ph/status/evidence/TASK-005/README.md`):
- `ph/status/evidence/TASK-003/index.md`
- `ph/status/evidence/TASK-003/router-supergraph-wiring.txt`
- `ph/status/evidence/TASK-003/supergraph-local-stats.txt`

## Sign-off
- [x] All validation steps completed
- [x] Evidence documented above
- [x] Ready to mark task as "done"
