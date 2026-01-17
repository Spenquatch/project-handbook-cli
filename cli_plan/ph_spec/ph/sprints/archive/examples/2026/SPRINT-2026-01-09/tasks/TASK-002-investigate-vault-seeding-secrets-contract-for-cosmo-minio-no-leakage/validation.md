---
title: Investigate: Vault seeding + secrets contract for Cosmo/MinIO (no leakage) - Validation Guide
type: validation
date: 2026-01-09
task_id: TASK-002
tags: [validation]
links: []
---

# Validation Guide: Investigate: Vault seeding + secrets contract for Cosmo/MinIO (no leakage)

## Automated Validation
```bash
pnpm -C project-handbook make -- validate
pnpm -C project-handbook make -- sprint-status
```

## Manual Validation (pass/fail)
1. DR completeness:
   - `project-handbook/decision-register/DR-0004-vault-secrets-contract-cosmo-minio.md` has no “Pending research…” placeholders.
   - Exactly two options exist (A and B), and the DR ends with an approval request.
2. Feature implementation doc updated (execution-ready contract):
   - `project-handbook/features/v2_registry-cosmo-minio-required/implementation/IMPLEMENTATION.md` lists:
     - KV paths + keys (names only),
     - `/secrets/*.env` outputs,
     - bootstrap + templates file paths to change,
     - a “no secrets printed” checklist.
3. Evidence present and referenced:
   - `project-handbook/status/evidence/TASK-002/index.md` exists and links to evidence files.
   - Evidence naming + redaction follows: `project-handbook/status/evidence/TASK-005/README.md`

Minimum evidence files (per `project-handbook/status/evidence/TASK-005/README.md`):
- `project-handbook/status/evidence/TASK-002/index.md`
- `project-handbook/status/evidence/TASK-002/v2-vault-kv-layout.txt`
- `project-handbook/status/evidence/TASK-002/v2-vault-bootstrap-no-leakage-snippets.txt`

## Sign-off
- [x] All validation steps completed
- [x] Evidence documented above
- [x] Ready to mark task as "done"
