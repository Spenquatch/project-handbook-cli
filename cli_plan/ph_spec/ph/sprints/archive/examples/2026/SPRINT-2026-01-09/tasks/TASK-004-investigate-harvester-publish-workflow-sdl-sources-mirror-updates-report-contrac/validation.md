---
title: Investigate: Harvester publish workflow (SDL sources, mirror updates, report contract) + codegen wiring - Validation Guide
type: validation
date: 2026-01-09
task_id: TASK-004
tags: [validation]
links: []
---

# Validation Guide: Investigate: Harvester publish workflow (SDL sources, mirror updates, report contract) + codegen wiring

## Automated Validation
```bash
ph validate
ph sprint status
```

## Manual Validation (pass/fail)
1. DR completeness:
   - `ph/decision-register/DR-0006-harvester-publish-and-codegen-workflow.md` has no “Pending research…” placeholders.
   - Exactly two options exist (A and B), and the DR ends with an approval request.
2. Feature implementation docs updated (execution-ready):
   - `ph/features/v2_schema-harvester-service/implementation/IMPLEMENTATION.md` defines publish/check sequencing, mirror updates, and report contract.
   - `ph/features/v2_codegen-from-registry/implementation/IMPLEMENTATION.md` defines canonical codegen wiring + CI ordering.
3. Evidence present and referenced:
   - `ph/status/evidence/TASK-004/index.md` exists and links to evidence files.
   - Evidence naming + redaction follows: `ph/status/evidence/TASK-005/README.md`

Minimum evidence files (per `ph/status/evidence/TASK-005/README.md`):
- `ph/status/evidence/TASK-004/index.md`
- `ph/status/evidence/TASK-004/subgraphs-yaml.txt`
- `ph/status/evidence/TASK-004/v2-smoke-schema-hooks.txt`
- `ph/status/evidence/TASK-004/rg-codegen.txt`

## Sign-off
- [ ] All validation steps completed
- [ ] Evidence documented above
- [ ] Ready to mark task as "done"
