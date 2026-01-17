---
title: Investigate: Cosmo+MinIO baseline wiring strategy (topology, versions, posture) - Validation Guide
type: validation
date: 2026-01-09
task_id: TASK-001
tags: [validation]
links: []
---

# Validation Guide: Investigate: Cosmo+MinIO baseline wiring strategy (topology, versions, posture)

## Automated Validation
```bash
ph validate
ph sprint status
```

## Manual Validation (pass/fail)
1. DR completeness:
   - `ph/decision-register/DR-0003-cosmo-minio-baseline-topology.md` has no “Pending research…” placeholders.
   - Exactly two options exist (A and B), and the DR ends with an approval request.
2. Feature docs updated (execution-ready, pending approval):
   - `ph/features/v2_registry-cosmo-minio-required/architecture/ARCHITECTURE.md` includes a pinned inventory and explicit exposure posture.
   - `ph/features/v2_registry-cosmo-minio-required/implementation/IMPLEMENTATION.md` lists the exact v2 file paths that will be changed during implementation and the smoke probes that will prove the posture.
3. Evidence present and referenced:
   - `ph/status/evidence/TASK-001/index.md` exists and links to the evidence files.
   - Evidence naming + redaction follows: `ph/status/evidence/TASK-005/README.md`

Minimum evidence files (per `ph/status/evidence/TASK-005/README.md`):
- `ph/status/evidence/TASK-001/index.md`
- `ph/status/evidence/TASK-001/v2-compose-head.txt`
- `ph/status/evidence/TASK-001/v2-vault-kv-layout.txt`
- `ph/status/evidence/TASK-001/rg-cosmo-minio.txt`

## Sign-off
- [ ] All validation steps completed
- [ ] Evidence documented above
- [ ] Ready to mark task as "done"
