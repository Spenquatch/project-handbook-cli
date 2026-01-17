---
title: Investigate: Harvester publish workflow (SDL sources, mirror updates, report contract) + codegen wiring - References
type: references
date: 2026-01-09
task_id: TASK-004
tags: [references]
links: []
---

# References: Investigate: Harvester publish workflow (SDL sources, mirror updates, report contract) + codegen wiring

## Internal References

### Decision Context
- **Decision**: `DR-0006`
- **Feature**: [Feature overview](../../../../../features/v2_schema-harvester-service/overview.md)
- **Architecture**: [Feature architecture](../../../../../features/v2_schema-harvester-service/architecture/ARCHITECTURE.md)
- **Also impacts**: [v2_codegen-from-registry](../../../../../features/v2_codegen-from-registry/overview.md)
- **Decision Register Entry**: `project-handbook/decision-register/DR-0006-harvester-publish-and-codegen-workflow.md`
- **ADRs**:
  - `project-handbook/adr/0021-v2-schema-harvester-service.md`
  - `project-handbook/adr/0019-v2-codegen-from-registry.md`
- **Evidence conventions (from TASK-005)**: `project-handbook/status/evidence/TASK-005/README.md`

### v2 Reference (read-only)
- `v2/infra/compose/graphql/subgraphs.yaml`
- `v2/infra/compose/graphql/subgraphs/*/schema.graphql`
- `v2/scripts/v2-smoke.sh`

### Sprint Context
- **Sprint Plan**: [Current sprint](../../plan.md)
- **Sprint Tasks**: [All sprint tasks](../)

## Notes
External docs required to decide workflow details (record URLs in evidence):
- Cosmo publish/check APIs and auth model
- Apollo Router compatibility constraints (if harvester produces an artifact Router consumes)
