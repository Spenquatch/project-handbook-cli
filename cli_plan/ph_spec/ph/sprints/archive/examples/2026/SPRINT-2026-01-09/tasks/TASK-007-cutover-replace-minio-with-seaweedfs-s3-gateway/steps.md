---
title: Cutover: Replace MinIO with SeaweedFS S3 gateway - Implementation Steps
type: implementation
date: 2026-01-09
task_id: TASK-007
tags: [implementation]
links: []
---

# Implementation Steps: Cutover: Replace MinIO with SeaweedFS S3 gateway

## Overview
Cut over the Cosmo artifact store from MinIO to **SeaweedFS S3 gateway** while keeping the integration store-agnostic and measurable.

This task assumes:
- the MinIO baseline is already implemented and validated in `TASK-006`,
- a deterministic “Cosmo artifact write/read” probe exists (and passed against MinIO), and
- the cutover is gated on that probe passing against SeaweedFS.

## Prerequisites
- `TASK-006` is `done`.
- You know the pinned SeaweedFS image and S3 port:
  - image: `chrislusf/seaweedfs:4.05`
  - S3 endpoint port: `8333`
- Evidence will be captured under `project-handbook/status/evidence/TASK-007/` (use a per-run subfolder).

## Step 1 — Preflight: confirm baseline invariants
1. Re-read the decisions that bound this task:
   - `project-handbook/adr/0030-v2-cosmo-artifact-store-minio-baseline-then-seaweedfs.md`
   - `project-handbook/decision-register/DR-0003-cosmo-minio-baseline-topology.md`
2. Confirm these are true before modifying anything:
   - MinIO baseline stack is green (`TASK-006` validation evidence exists).
   - The “Cosmo artifact write/read” probe exists and passes against MinIO.
   - Bucket init uses a generic S3 client (not `minio/mc`).
   - `/secrets/artifacts.env` exists and is the single source of truth for artifact store config.

If any of these are false, stop and complete `TASK-006` first.

## Step 2 — Add SeaweedFS S3 gateway to v2 compose (internal-only)
Edit `v2/infra/compose/docker-compose.v2.yml` to add:
- `seaweedfs` using `chrislusf/seaweedfs:4.05`
- command: `server -s3 -dir=/data` (single-node; includes S3 gateway)
- env vars (names only; values sourced from Vault-rendered env):
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
- wiring:
  - attach to `tribuence-v2-net`
  - `expose: ['8333']`
  - no Traefik labels/routers
  - no host `ports:`
  - persistent volume mounted at `/data`

## Step 3 — Switch the artifact-store endpoint from MinIO to SeaweedFS
Update the centralized artifact-store config so the only behavioral change is:
- endpoint: `http://seaweedfs:8333`

Concretely:
- Update `/secrets/artifacts.env` so `S3_ENDPOINT_URL=http://seaweedfs:8333`.
- Ensure both `artifact-bucket-init` and the “Cosmo artifact write/read” smoke probe read `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_FORCE_PATH_STYLE`, `S3_REGION`, and `COSMO_S3_BUCKET` from the same `/secrets/artifacts.env`.

## Step 4 — Validate the cutover (probe must pass against SeaweedFS)
1. Bring up v2 and re-run Vault bootstrap (see `commands.md`).
2. Run `artifact-bucket-init` twice (idempotence) against SeaweedFS.
3. Run `V2_SMOKE_MODE=infra make -C v2 v2-smoke` and ensure:
   - forbidden host checks still pass (`cosmo.local`, `minio.local` remain 404 via Traefik),
   - the artifact write/read probe passes.

## Step 5 — Remove MinIO from default v2 compose
After the probe passes against SeaweedFS:
1. Remove `minio` from `v2/infra/compose/docker-compose.v2.yml` (and remove its volume if not used elsewhere).
2. Ensure no service still references `minio:9000` (search the repo to confirm).
3. Re-run v2 bring-up + infra smoke to confirm the stack is green without MinIO.

## Step 6 — Documentation and ADR hygiene
1. Update any v2 docs that mention MinIO as the artifact store (e.g., `v2/docs/README.md`) to reflect “SeaweedFS (S3)”.
2. ADR hygiene (required by acceptance):
   - Update `project-handbook/adr/0015-tribuence-mini-v2-cosmo-minio-and-schema-publishing.md` to reflect that ADR-0030 supersedes the “MinIO required” wording (either by setting `status: superseded` with a link to ADR-0030, or by adding an explicit note that the artifact store is now SeaweedFS S3 per ADR-0030).
3. Run `pnpm -C project-handbook make -- validate`.

## Notes
- Do not proceed to “remove MinIO” until the artifact probe passes against SeaweedFS.
- Evidence must not contain secrets/tokens/cookies; scan evidence before sharing.
