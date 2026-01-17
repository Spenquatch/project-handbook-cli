---
title: Implement: Router supergraph sync from Cosmo (Option B) - References
type: references
date: 2026-01-10
task_id: TASK-008
tags: [references]
links: []
---

# References: Implement: Router supergraph sync from Cosmo (Option B)

## Internal References

### Decision Context
- **Decision**: [ADR-0031](../../../../../adr/0031-v2-router-supergraph-delivery-cosmo-sync-artifact.md)
- **Discovery (accepted)**: [DR-0005](../../../../../decision-register/DR-0005-router-supergraph-consumption-from-cosmo.md)
- **Secrets contract (accepted)**: [DR-0004](../../../../../decision-register/DR-0004-vault-secrets-contract-cosmo-minio.md)
- **Publish workflow contract (dependency)**: [DR-0006](../../../../../decision-register/DR-0006-harvester-publish-and-codegen-workflow.md)
- **Feature**: [Feature overview](../../../../../features/v2_schema-publishing-and-composition/overview.md)
- **Architecture**: [Feature architecture](../../../../../features/v2_schema-publishing-and-composition/architecture/ARCHITECTURE.md)
- **Implementation plan**: [Feature implementation](../../../../../features/v2_schema-publishing-and-composition/implementation/IMPLEMENTATION.md)

### Sprint Context
- **Sprint Plan**: [Current sprint](../../plan.md)
- **Sprint Tasks**: [All sprint tasks](../)
- **Daily Progress**: [Daily status](../../../../../status/daily/)

### Evidence / Prior Work
- `ph/status/evidence/TASK-003/` — Apollo Router `--hot-reload` behavior + Cosmo CLI `fetch-schema` evidence (no secrets).

### Reference-Only (Legacy)
- `modular-oss-saas/infra/compose/docker-compose.yml` — legacy Cosmo controlplane port (`3001`) and baseline wiring shape.
- `modular-oss-saas/docs/configuration.md` — legacy `COSMO_GRAPH_REF=tribuence@dev` reference value.

## Notes
Add concrete links here only when you discover resources during the task (no placeholders).
