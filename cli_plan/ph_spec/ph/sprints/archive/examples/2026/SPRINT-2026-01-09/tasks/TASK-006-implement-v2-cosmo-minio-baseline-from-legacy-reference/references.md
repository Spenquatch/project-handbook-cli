---
title: Implement: v2 Cosmo+MinIO baseline (from legacy reference) - References
type: references
date: 2026-01-09
task_id: TASK-006
tags: [references]
links: []
---

# References: Implement: v2 Cosmo+MinIO baseline (from legacy reference)

## Internal References

### Decision Context
- **ADR-0030**: `project-handbook/adr/0030-v2-cosmo-artifact-store-minio-baseline-then-seaweedfs.md`
- **DR-0003** (accepted; pins + inventory): `project-handbook/decision-register/DR-0003-cosmo-minio-baseline-topology.md`
- **FDR-0001** (accepted; Vault contract): `project-handbook/features/v2_registry-cosmo-minio-required/fdr/0001-vault-secrets-contract-cosmo-minio.md`
- **Feature overview**: `project-handbook/features/v2_registry-cosmo-minio-required/overview.md`
- **Feature architecture**: `project-handbook/features/v2_registry-cosmo-minio-required/architecture/ARCHITECTURE.md`
- **Feature implementation**: `project-handbook/features/v2_registry-cosmo-minio-required/implementation/IMPLEMENTATION.md`
- **Feature testing**: `project-handbook/features/v2_registry-cosmo-minio-required/testing/TESTING.md`

### Sprint Context
- **Sprint Plan**: `project-handbook/sprints/current/plan.md`
- **Sprint Tasks**: `project-handbook/sprints/current/tasks/`
- **Daily status**: `project-handbook/status/daily/`

### Evidence Context (do not re-create; reuse for guidance)
- `project-handbook/status/evidence/TASK-001/index.md` (Cosmo/MinIO topology evidence)
- `project-handbook/status/evidence/TASK-002/index.md` (Vault “no leakage” evidence)

### v2 Wiring Touchpoints (expected to change)
- Compose: `v2/infra/compose/docker-compose.v2.yml`
- Vault Agent config: `v2/infra/vault/templates/agent.hcl`
- Vault templates (add new): `v2/infra/vault/templates/`
- Vault bootstrap: `v2/scripts/vault/bootstrap-v2.sh`
- Smoke harness (add probe + isolation checks): `v2/scripts/v2-smoke.sh`
- v2 quickstart (keep in sync): `v2/docs/README.md`

### Legacy Reference (shape only; do not copy secrets)
- Compose inventory: `modular-oss-saas/infra/compose/docker-compose.yml`
- Bootstrap script (includes migrations + seed + bucket init): `modular-oss-saas/scripts/infra/bootstrap-cosmo.sh`
