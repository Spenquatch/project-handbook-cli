---
title: Cutover: Replace MinIO with SeaweedFS S3 gateway - Completion Checklist
type: checklist
date: 2026-01-09
task_id: TASK-007
tags: [checklist]
links: []
---

# Completion Checklist: Cutover: Replace MinIO with SeaweedFS S3 gateway

## Pre-Work (must be true before starting)
- [ ] `TASK-006` is `done` and its artifact write/read probe passed against MinIO
- [ ] Read: `project-handbook/adr/0030-v2-cosmo-artifact-store-minio-baseline-then-seaweedfs.md`
- [ ] Read: `project-handbook/decision-register/DR-0003-cosmo-minio-baseline-topology.md` (SeaweedFS image + S3 port)
- [ ] Evidence run folder created: `project-handbook/status/evidence/TASK-007/<run-id>/`
- [ ] `/secrets/artifacts.env` exists (created in `TASK-006`) and is the single source of truth for artifact store config

## Cutover Implementation
- [ ] `v2/infra/compose/docker-compose.v2.yml` includes `seaweedfs` (pinned image) and **no host `ports:`**
- [ ] SeaweedFS S3 gateway runs internal-only on `tribuence-v2-net` (no Traefik routers/labels)
- [ ] Artifact-store endpoint is switched by setting `S3_ENDPOINT_URL=http://seaweedfs:8333` in `/secrets/artifacts.env` (no leakage)
- [ ] `COSMO_S3_BUCKET` remains present (same bucket name used by the artifact probe)
- [ ] “Cosmo artifact write/read” smoke probe passes against SeaweedFS
- [ ] MinIO is removed from the default v2 compose after successful cutover

## Validation Evidence (must be captured)
- [ ] v2 bring-up evidence captured under `project-handbook/status/evidence/TASK-007/<run-id>/`
- [ ] Vault bootstrap output captured and contains **no secret values**
- [ ] `artifact-bucket-init` run twice against SeaweedFS; both runs succeed; logs captured
- [ ] `V2_SMOKE_MODE=infra make -C v2 v2-smoke` passes; output captured
- [ ] Evidence leak scan run over the evidence folder and is clean
- [ ] `pnpm -C project-handbook make -- validate` passes; output captured

## Documentation Hygiene (required)
- [ ] `v2/docs/README.md` updated if it mentions MinIO as the artifact store
- [ ] ADR hygiene addressed:
  - [ ] `project-handbook/adr/0015-tribuence-mini-v2-cosmo-minio-and-schema-publishing.md` explicitly superseded/adjusted to reflect ADR-0030 cutover

## Before Marking `review`
- [ ] Task status set to `review`: `pnpm -C project-handbook make -- task-status id=TASK-007 status=review`
