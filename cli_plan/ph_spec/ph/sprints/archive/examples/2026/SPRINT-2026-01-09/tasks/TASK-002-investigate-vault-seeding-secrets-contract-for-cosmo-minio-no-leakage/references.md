---
title: Investigate: Vault seeding + secrets contract for Cosmo/MinIO (no leakage) - References
type: references
date: 2026-01-09
task_id: TASK-002
tags: [references]
links: []
---

# References: Investigate: Vault seeding + secrets contract for Cosmo/MinIO (no leakage)

## Internal References

### Decision Context
- **Decision**: `DR-0004`
- **Feature**: [Feature overview](../../../features/v2_registry-cosmo-minio-required/overview.md)
- **Architecture**: [Feature architecture](../../../features/v2_registry-cosmo-minio-required/architecture/ARCHITECTURE.md)
- **Decision Register Entry**: `project-handbook/decision-register/DR-0004-vault-secrets-contract-cosmo-minio.md`
- **ADR**: `project-handbook/adr/0015-tribuence-mini-v2-cosmo-minio-and-schema-publishing.md`
- **Evidence conventions (from TASK-005)**: `project-handbook/status/evidence/TASK-005/README.md`

### v2 Reference (read-only)
- `v2/scripts/vault/bootstrap-v2.sh`
- `v2/infra/vault/templates/`
- `v2/infra/compose/docker-compose.v2.yml` (how `/secrets` volumes are mounted per service)

### Sprint Context
- **Sprint Plan**: [Current sprint](../../plan.md)
- **Sprint Tasks**: [All sprint tasks](../)

## Notes
External docs that may be required (record URLs in evidence):
- HashiCorp Vault KV v2 docs (paths + templating)
- Cosmo auth/token docs
- MinIO auth docs
