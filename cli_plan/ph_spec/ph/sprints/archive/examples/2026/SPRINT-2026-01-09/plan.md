---
title: Sprint Plan - SPRINT-2026-01-09
type: sprint-plan
date: 2026-01-09
sprint: SPRINT-2026-01-09
mode: bounded
tags: [sprint, planning]
release: v0.5.0
---

# Sprint Plan: SPRINT-2026-01-09

## Release Context
**Release**: v0.5.0
**Features in this release**:
- v2_registry-cosmo-minio-required: regular (Critical Path)
- v2_schema-publishing-and-composition: regular (Critical Path)
- v2_schema-harvester-service: regular (Critical Path)
- v2_codegen-from-registry: regular

## Sprint Model
This sprint uses **bounded planning** (ADR-0013): sprint scope is defined by *work boundaries* and *parallel lanes*, not a fixed calendar window or points cap.

## Sprint Goal
1. [x] **Primary:** produce operator-approvable DRs for the v0.5.0 registry pipeline (Cosmo/MinIO baseline, Vault secrets, Router supergraph consumption, Harvester publish + Codegen wiring) with evidence and execution-ready feature plans.
2. [x] **Secondary:** define a consistent evidence convention so discovery tasks are comparable and easy to review.
3. [x] **Integration:** ensure DR recommendations are internally consistent across features (no contradictory topology/auth/workflow decisions).

## Boundaries (Lanes)
Define lanes to maximize parallel execution and minimize cross-lane coupling.

| Lane | Scope | Success Output |
|------|-------|----------------|
| `registry/kickoff` | Evidence conventions + dependency ordering | Downstream tasks execute without ambiguity |
| `registry/discovery` | Cosmo/MinIO topology + posture decision | DR-0003 complete + feature plan updated |
| `registry/security` | Vault KV + env rendering contract for Cosmo/MinIO | DR-0004 complete + feature plan updated |
| `registry/router` | Router consumes Cosmo supergraph (auth + refresh) | DR-0005 complete + feature plan updated |
| `registry/publish` | Harvester publish/check workflow + codegen wiring | DR-0006 complete + feature plans updated |

## Integration Tasks
- Align decisions across DRs:
  - DR-0003 (topology) must not conflict with DR-0004 (secrets contract).
  - DR-0005 (Router consumption) must align with DR-0006 (harvester responsibilities / artifacts).

## Committed Tasks (this sprint)
| Task | Session | Lane | Decision | Depends on | Output |
|------|---------|------|----------|------------|--------|
| [TASK-005](./tasks/TASK-005-kickoff-v0-5-0-registry-pipeline-discovery-evidence-dirs-next-up-ordering/README.md) | `task-execution` | `registry/kickoff` | ADR-0015 | `FIRST_TASK` | Evidence conventions + “Next up” ordering |
| [TASK-001](./tasks/TASK-001-investigate-cosmo-minio-baseline-wiring-strategy-topology-versions-posture/README.md) | `research-discovery` | `registry/discovery` | DR-0003 | TASK-005 | Topology + posture DR + feature plan |
| [TASK-002](./tasks/TASK-002-investigate-vault-seeding-secrets-contract-for-cosmo-minio-no-leakage/README.md) | `research-discovery` | `registry/security` | DR-0004 | TASK-005 | Secrets contract DR + feature plan |
| [TASK-003](./tasks/TASK-003-investigate-router-consumes-cosmo-supergraph-pull-model-auth-refresh/README.md) | `research-discovery` | `registry/router` | DR-0005 | TASK-005 | Router consumption DR + feature plan |
| [TASK-004](./tasks/TASK-004-investigate-harvester-publish-workflow-sdl-sources-mirror-updates-report-contrac/README.md) | `research-discovery` | `registry/publish` | DR-0006 | TASK-005 | Publish/codegen workflow DR + feature plans |
| [TASK-006](./tasks/TASK-006-implement-v2-cosmo-minio-baseline-from-legacy-reference/README.md) | `task-execution` | `registry/discovery` | ADR-0030 | TASK-002 | v2 Cosmo+MinIO baseline + store-agnostic bucket init + reusable artifact probe |
| [TASK-008](./tasks/TASK-008-implement-router-supergraph-sync-from-cosmo-option-b/README.md) | `task-execution` | `registry/router` | ADR-0031 | TASK-006, TASK-004 | Router consumes Cosmo-produced runtime supergraph via sync artifact + hot-reload + smoke evidence |
| [TASK-007](./tasks/TASK-007-cutover-replace-minio-with-seaweedfs-s3-gateway/README.md) | `task-execution` | `registry/discovery` | ADR-0030 | TASK-006 | SeaweedFS S3 gateway cutover + MinIO removal (probe-gated) |
| [TASK-009](./tasks/TASK-009-implement-v2-schema-harvester-publish-check-mirrors-report-hardening-option-a/README.md) | `task-execution` | `registry/publish` | ADR-0032 | TASK-006 | Harvester publish/check hard gate + atomic mirrors + deterministic sanitized report |
| [TASK-010](./tasks/TASK-010-implement-v2-registry-backed-codegen-wiring-cosmo-fetch-drift-gate-ci-ordering/README.md) | `task-execution` | `registry/publish` | ADR-0032 | TASK-009, TASK-006 | Codegen from Cosmo + drift gate + explicit ordering (publish → codegen → typecheck) |

## Execution Order (no ambiguity)
This sprint is lane-parallel, but the DR recommendations must be consistent. Execute in this order:
1. `TASK-005` (kickoff): lock evidence conventions and confirm “Next up” ordering.
2. `TASK-001` (DR-0003 draft): establish the Cosmo/MinIO service inventory + posture options.
3. `TASK-002` (DR-0004): may start after `TASK-005`, but do not finalize the recommendation until `DR-0003`’s inventory is drafted (secrets must match services).
4. `TASK-004` (DR-0006): define publish/check workflow + any artifact contracts.
5. `TASK-003` (DR-0005): finalize Router recommendation after `DR-0006` is explicit if Router consumes a local artifact (Option B).
6. `TASK-006` (ADR-0030): implement the Cosmo+MinIO baseline + bucket init + reusable artifact probe (requires `TASK-002`).
7. `TASK-008` (ADR-0031): implement Router runtime supergraph sync (Cosmo → file artifact) and hot reload (requires `TASK-006` + `TASK-004`).
8. `TASK-007` (ADR-0030): cut over MinIO → SeaweedFS, gated on the same artifact probe passing.
9. `TASK-009` (ADR-0032): implement harvester publish/check gate + atomic mirrors + deterministic sanitized report (requires `TASK-006`).
10. `TASK-010` (ADR-0032): implement codegen from Cosmo + drift gate + ordering (requires `TASK-009` + `TASK-006`).

Integration checkpoint (required):
- Before moving any of `TASK-001`..`TASK-004` to `review`, confirm cross-DR consistency: topology ↔ secrets ↔ publish artifacts ↔ Router consumption.
- Before moving `TASK-009` or `TASK-010` to `review`, confirm cross-task consistency with `TASK-008`: shared `/secrets/cosmo-cli.env` contract, pinned `wgc` version, and “no secret leakage” evidence scans.

## Task Creation Guide
```bash
ph task create --title "Task Name" --feature feature-name --decision ADR-XXX --points 3 --lane "ops/automation"
```

## Telemetry (Points)
- Story points are tracked for throughput/velocity trends, not for limiting sprint scope.

## Dependencies & Risks
- External dependencies:
  - Upstream Cosmo + MinIO versioning / image tags (must be pinned; capture URLs as evidence).
  - Cosmo auth model and APIs for publish/check and supergraph retrieval.
- Cross-lane dependencies (integration risk):
  - Decisions DR-0003..DR-0006 must align (topology ↔ secrets ↔ artifacts ↔ consumption).
- Execution risk:
  - Router runtime supergraph sync adds a moving part; mitigate with atomic writes + last-known-good preservation and explicit “no secret leakage” evidence (`TASK-008`).
  - SeaweedFS S3 parity differences vs MinIO; mitigate by gating cutover on an explicit artifact write/read probe and keeping a rollback path until green.
- Unknowns / validation gaps:
  - “Internal-only posture” enforcement (no Traefik exposure, no host binds for Cosmo/artifact store) must be verifiable via smoke probes in `TASK-006` and `TASK-007`.

## Success Criteria
- [x] Lanes are explicit and independently executable
- [x] All committed tasks are linked above and have execution-ready docs
- [x] Downstream discovery tasks produce approval-ready DRs with evidence and follow-up plans

## Pre-Execution Audit Gate
Status: PASSED (audited: `TASK-006`, `TASK-007`, `TASK-008`, `TASK-009`, `TASK-010`)  
Re-audit (2026-01-10): `TASK-009`, `TASK-010` documentation hardened (no ambiguity language); handbook validation clean.  
Notes:
- `TASK-006`: requires `/secrets/artifacts.env` as the single source of truth for artifact-store config (`S3_ENDPOINT_URL` + creds + bucket), used by bucket-init + smoke probe.
- `TASK-007`: cutover is performed by switching `S3_ENDPOINT_URL` to `http://seaweedfs:8333`, then removing MinIO after the probe is green.
- `TASK-008`: runtime supergraph contract is explicit (`/dist/graphql-runtime/supergraph.graphql`) and Cosmo CLI creds are scoped to `supergraph-sync` via `/secrets/cosmo-cli.env` (Router never mounts Cosmo creds).
- `TASK-009`: harvester publish/check is the hard gate; mirrors update only after full success via atomic rename; deterministic sanitized report at `v2/.tmp/harvester/publish-report.json` with evidence under `ph/status/evidence/TASK-009/<run-id>/`.
- `TASK-010`: codegen fetches schema inputs from Cosmo into `v2/.tmp/codegen/supergraph.graphql` (atomic) and enforces drift + ordering with evidence under `ph/status/evidence/TASK-010/<run-id>/`.

Validation: `ph validate`  
Report: `status/validation.json`
