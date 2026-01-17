---
title: Investigate: Router consumes Cosmo supergraph (pull model + auth + refresh) - References
type: references
date: 2026-01-09
task_id: TASK-003
tags: [references]
links: []
---

# References: Investigate: Router consumes Cosmo supergraph (pull model + auth + refresh)

## Internal References

### Decision Context
- **Decision**: `DR-0005`
- **Feature**: [Feature overview](../../../features/v2_schema-publishing-and-composition/overview.md)
- **Architecture**: [Feature architecture](../../../features/v2_schema-publishing-and-composition/architecture/ARCHITECTURE.md)
- **Decision Register Entry**: `project-handbook/decision-register/DR-0005-router-supergraph-consumption-from-cosmo.md`
- **ADRs**:
  - `project-handbook/adr/0015-tribuence-mini-v2-cosmo-minio-and-schema-publishing.md`
  - `project-handbook/adr/0021-v2-schema-harvester-service.md`
- **Evidence conventions (from TASK-005)**: `project-handbook/status/evidence/TASK-005/README.md`

### v2 Reference (read-only)
- `v2/infra/compose/docker-compose.v2.yml` (Router container + mounts)
- `v2/infra/compose/graphql/router.v2.yaml`
- `v2/infra/compose/graphql/supergraph-local.graphql` (do not copy into evidence; stats only)
- `v2/infra/vault/templates/router.env.tpl`

### Sprint Context
- **Sprint Plan**: [Current sprint](../../plan.md)
- **Sprint Tasks**: [All sprint tasks](../)

## Notes
External docs required to decide auth/refresh (record URLs in evidence):
- Apollo Router docs for supergraph sources and hot reload / polling (if available)
- Cosmo API/docs for supergraph artifact retrieval and auth model
