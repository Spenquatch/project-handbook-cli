---
title: Cutover: Replace MinIO with SeaweedFS S3 gateway - References
type: references
date: 2026-01-09
task_id: TASK-007
tags: [references]
links: []
---

# References: Cutover: Replace MinIO with SeaweedFS S3 gateway

## Internal References

### Decision Context
- **ADR-0030**: `ph/adr/0030-v2-cosmo-artifact-store-minio-baseline-then-seaweedfs.md`
- **ADR-0015** (superseded/adjusted by this cutover): `ph/adr/0015-tribuence-mini-v2-cosmo-minio-and-schema-publishing.md`
- **DR-0003** (accepted; SeaweedFS pin): `ph/decision-register/DR-0003-cosmo-minio-baseline-topology.md`
- **FDR-0001** (accepted; Vault contract): `ph/features/v2_registry-cosmo-minio-required/fdr/0001-vault-secrets-contract-cosmo-minio.md`
- **Feature overview**: `ph/features/v2_registry-cosmo-minio-required/overview.md`
- **Feature architecture**: `ph/features/v2_registry-cosmo-minio-required/architecture/ARCHITECTURE.md`

### Sprint Context
- **Sprint Plan**: `ph/sprints/current/plan.md`
- **Sprint Tasks**: `ph/sprints/current/tasks/`
- **Daily status**: `ph/status/daily/`

### Evidence Context (do not re-create; reuse for guidance)
- `ph/status/evidence/TASK-001/seaweedfs-readme-snippets.txt` (SeaweedFS S3 gateway quickstart snippets)
- `ph/status/evidence/TASK-001/index.md` (topology evidence)
- `ph/status/evidence/TASK-006/` (baseline evidence; confirm probe exists/passed)

### v2 Wiring Touchpoints (expected to change)
- Compose: `v2/infra/compose/docker-compose.v2.yml`
- Vault Agent config: `v2/infra/vault/templates/agent.hcl`
- Vault templates: `v2/infra/vault/templates/`
- Bucket init helper: `artifact-bucket-init` service (in compose)
- Smoke harness: `v2/scripts/v2-smoke.sh`
- v2 quickstart: `v2/docs/README.md`
