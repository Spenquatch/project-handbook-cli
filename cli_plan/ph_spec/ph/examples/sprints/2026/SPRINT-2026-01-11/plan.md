---
title: Sprint Plan - SPRINT-2026-01-11
type: sprint-plan
date: 2026-01-11
sprint: SPRINT-2026-01-11
mode: bounded
tags: [sprint, planning]
release: v0.5.0
---

# Sprint Plan: SPRINT-2026-01-11

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
1. [ ] **Primary:** close out v0.5.0 release artifacts and ensure the handbook “current” surfaces are coherent for hand-off (release close + status).
2. [ ] **Secondary:** convert top next-step work into execution-ready, decision-backed discovery tasks (module registry + context control-plane).
3. [ ] **Integration:** make v2.1 module registry discovery explicitly compatible with v3 roadmap constraints (checklist + decision routing).

## Boundaries (Lanes)
Define lanes to maximize parallel execution and minimize cross-lane coupling.

| Lane | Scope | Success Output |
|------|-------|----------------|
| `handbook/release` | Release close-out + next release planning | v0.5.0 closed; v0.5.1 planned; reporting clean |
| `module-registry/origin` | Artifact origin + publish pipeline (Option A) | Proxy origin route + publish/smoke scripts implemented and validated |
| `module-registry/runtime` | Next.js runtime loading strategy | Runtime loader (Option A browser verify) + panel integration + E2E failure-mode gates implemented and validated |
| `context/control-plane` | Context snapshot + wrapper consumption contract | Contract + migrations + snapshot query + smoke probe implemented and validated |
| `integration/v3-alignment` | v3 compatibility constraints | Cross-cutting DR created during research task + checklist embedded in feature docs |

## Integration Tasks
- `integration/v3-alignment` depends on `module-registry/*` discovery outputs and `context/control-plane` contract so the checklist is grounded in concrete loader + schema choices.
- `module-registry/runtime` tasks depend on the Context snapshot query (`TASK-035`) so UI can resolve module selection without env/querystring guessing.

## Committed Tasks (this sprint)
| Task | Session | Lane | Decision | Depends on | Output |
|------|---------|------|----------|------------|--------|
| [TASK-024](./tasks/TASK-024-handbook-close-release-v0-5-0/README.md) | `task-execution` | `handbook/release` | ADR-0012 | `FIRST_TASK` | v0.5.0 release closed + status surfaces updated |
| [TASK-025](./tasks/TASK-025-handbook-plan-v0-5-1-release-assign-initial-features/README.md) | `task-execution` | `handbook/release` | ADR-0012 | TASK-024 | v0.5.1 planned + initial features assigned |
| [TASK-026](./tasks/TASK-026-investigate-ui-module-artifact-origin-publish-pipeline-s3-integrity/README.md) | `research-discovery` | `module-registry/origin` | DR-0001 | TASK-025 | feature-local DR + execution-ready origin/publish contract |
| [TASK-027](./tasks/TASK-027-investigate-next-js-runtime-module-loading-allowlist-sha256/README.md) | `research-discovery` | `module-registry/runtime` | DR-0002 | TASK-025 | feature-local DR + execution-ready loader contract |
| [TASK-029](./tasks/TASK-029-investigate-context-control-plane-schema-migration-wrapper-consumption-contract/README.md) | `research-discovery` | `context/control-plane` | DR-0001 | TASK-025 | feature-local DR + execution-ready snapshot/consumption contract |
| [TASK-028](./tasks/TASK-028-investigate-module-registry-alignment-with-v3-roadmap/README.md) | `research-discovery` | `integration/v3-alignment` | DR-0007 | TASK-026, TASK-027, TASK-029 | cross-cutting DR + v3 alignment checklist + constraints |
| [TASK-030](./tasks/TASK-030-implement-ui-module-origin-proxy-route-option-a/README.md) | `task-execution` | `module-registry/origin` | FDR-v2_1_ui-module-registry-discovery-0001 | TASK-027 | Next.js proxy origin route (allowlist + immutable caching) + evidence |
| [TASK-031](./tasks/TASK-031-implement-ui-module-publish-pipeline-s3-upload-smoke-check/README.md) | `task-execution` | `module-registry/origin` | FDR-v2_1_ui-module-registry-discovery-0001 | TASK-030 | Publish script (append-only) + smoke script (S3 + proxy route) + evidence |
| [TASK-032](./tasks/TASK-032-contract-context-control-plane-snapshot-graphql-contract-v1/README.md) | `task-execution` | `context/control-plane` | FDR-v2_context-control-plane-schema-0001 | TASK-029 | Context subgraph v1 snapshot contract + wrapper consumption rules + evidence |
| [TASK-033](./tasks/TASK-033-contract-context-control-plane-db-schema-v1-tables-constraints/README.md) | `task-execution` | `context/control-plane` | FDR-v2_context-control-plane-schema-0001 | TASK-029 | Context DB schema v1 contract (tables + constraints) + evidence |
| [TASK-034](./tasks/TASK-034-implement-context-db-migrations-for-control-plane-tables-v1/README.md) | `task-execution` | `context/control-plane` | FDR-v2_context-control-plane-schema-0001 | TASK-033 | Context DB migrations for v1 control-plane tables + evidence |
| [TASK-035](./tasks/TASK-035-implement-context-snapshot-query-types-empty-safe/README.md) | `task-execution` | `context/control-plane` | FDR-v2_context-control-plane-schema-0001 | TASK-032, TASK-034 | Context snapshot query + v1 types (empty-safe) + SDL snapshot + evidence |
| [TASK-036](./tasks/TASK-036-validate-v2-smoke-probe-for-control-plane-snapshot-query/README.md) | `task-execution` | `context/control-plane` | FDR-v2_context-control-plane-schema-0001 | TASK-035 | v2 smoke probe validates snapshot shape + failure modes + evidence |
| [TASK-037](./tasks/TASK-037-implement-ui-module-runtime-loader-option-a-browser-verify-mode-flag/README.md) | `task-execution` | `module-registry/runtime` | FDR-v2_1_ui-module-registry-discovery-0002 | TASK-030 | UI module runtime loader (browser-verify + mode flag) + unit tests + evidence |
| [TASK-038](./tasks/TASK-038-implement-ui-module-panel-integration-deterministic-fallback-states/README.md) | `task-execution` | `module-registry/runtime` | FDR-v2_1_ui-module-registry-discovery-0002 | TASK-035, TASK-037 | UI module panel integration + deterministic fallback UX + evidence |
| [TASK-039](./tasks/TASK-039-validate-playwright-e2e-for-module-load-failure-modes/README.md) | `task-execution` | `module-registry/runtime` | FDR-v2_1_ui-module-registry-discovery-0002 | TASK-031, TASK-038 | Playwright E2E: module load + deterministic failure modes + evidence |
| [TASK-040](./tasks/TASK-040-contract-v3-ready-ui-module-manifest-metadata-fields-v1/README.md) | `task-execution` | `context/control-plane` | ADR-0033 | TASK-032, TASK-033 | Contract: v3-ready UI module manifest metadata fields (v1) + evidence |
| [TASK-041](./tasks/TASK-041-contract-v3-overlay-descriptors-precedence-in-context-snapshot-v1/README.md) | `task-execution` | `context/control-plane` | ADR-0033 | TASK-032, TASK-033 | Contract: v3 overlay descriptors + precedence in Context snapshot (v1) + evidence |

## Execution Order (no ambiguity)
1. `TASK-024` (close v0.5.0)
2. `TASK-025` (plan v0.5.1 and assign initial features)
3. Parallel discovery (can run concurrently):
   - `TASK-026` (feature DR-0001)
   - `TASK-027` (feature DR-0002)
   - `TASK-029` (feature DR-0001)
4. `TASK-028` (cross-cutting DR-0007) after `TASK-026` + `TASK-027` + `TASK-029` to integrate and finalize alignment constraints.
5. `TASK-030` (origin proxy route) after `TASK-027` (can proceed in parallel with `TASK-028`).
6. `TASK-031` (publish + smoke scripts) after `TASK-030`.
7. Context control-plane contract + implementation (can run in parallel with module runtime work once deps are met):
   - `TASK-032` + `TASK-033` after `TASK-029` (contract surfaces)
   - `TASK-034` after `TASK-033` (DB migrations)
   - `TASK-035` after `TASK-032` + `TASK-034` (snapshot query + types)
   - `TASK-036` after `TASK-035` (smoke probe gate)
8. Module runtime integration:
   - `TASK-037` after `TASK-030`
   - `TASK-038` after `TASK-035` + `TASK-037`
   - `TASK-039` after `TASK-031` + `TASK-038`
9. v3 alignment follow-on contracts:
   - `TASK-040` + `TASK-041` after `TASK-032` + `TASK-033`

## Task Creation Guide
```bash
ph task create --title "Task Name" --feature feature-name --decision ADR-XXX --points 3 --lane "handbook/automation"
```

## Telemetry (Points)
- Story points are tracked for throughput/velocity trends, not for limiting sprint scope.

## Dependencies & Risks
- Dependencies:
  - Do not pre-create DR content during sprint planning; DRs are created/completed within the `session=research-discovery` tasks.
  - Context snapshot query is a cross-feature dependency for UI + wrappers (ADR-0027).
- Risks:
  - Over-constraining v2.1 with v3 assumptions; mitigate by phrasing constraints as minimal invariants and keeping v3 details as examples only.
  - Loader/origin decisions that inadvertently require exposing an executable origin to browsers; mitigate by preferring proxy-based delivery and strict integrity checks.
  - Publish/smoke scripts may assume local Docker + Traefik hostnames; mitigate by using `curl --resolve` and composing AWS calls through the existing `cosmo-artifact-probe` helper container.
  - Context migrations are applied on every service boot (no migration ledger); mitigate by requiring strict idempotency and capturing restart evidence in `TASK-034` validation.
  - Overlay precedence ambiguity can cause nondeterministic UI; mitigate by codifying precedence semantics + ordering guarantees in `TASK-041` and requiring evidence captures + review.

## Success Criteria
- [ ] Lanes are explicit and independently executable
- [ ] Integration task is explicit and dependency-linked
- [ ] Sprint has a valid dependency graph (includes exactly one `FIRST_TASK`)
- [ ] All committed tasks are execution-ready (no placeholders; validation/evidence steps are explicit)

## Pre-Execution Audit Gate (passed)
Date: 2026-01-12

- Audit scope: `TASK-040` + `TASK-041` (context/control-plane lane).
- Sessions and dependencies match `task.yaml` and the sprint execution order (`TASK-040`/`TASK-041` after `TASK-032`/`TASK-033`).
- In-scope execution docs are unambiguous: additive-only contract changes, empty-safe surfaces, deterministic ordering semantics, and evidence paths are explicit.
- Feature status pages document cross-task dependencies for `TASK-040` and `TASK-041`.
- `ph validate --quick` is clean (see `status/validation.json`).

## Pre-Execution Audit Gate (third-party feedback incorporated)
Date: 2026-01-12

- `TASK-035` updated to DB-back `uiModuleManifests` (required for `TASK-038`/`TASK-039` harness).
- `TASK-030`/`TASK-037` updated with explicit sprint harness allowlist expectations + `version` validation rule.
- `ph/contracts/tribuence-mini-v2/vault-secrets.md` updated to include `/secrets/artifacts.env` contract.
- Stale “pending operator approval” wording removed from the executed Cosmo/MinIO registry feature docs.
