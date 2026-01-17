---
title: Implement: v2 Cosmo+MinIO baseline (from legacy reference) - Completion Checklist
type: checklist
date: 2026-01-09
task_id: TASK-006
tags: [checklist]
links: []
---

# Completion Checklist: Implement: v2 Cosmo+MinIO baseline (from legacy reference)

## Pre-Work (must be true before starting)
- [ ] `TASK-002` is `done` (Vault contract accepted as `project-handbook/features/v2_registry-cosmo-minio-required/fdr/0001-vault-secrets-contract-cosmo-minio.md`)
- [ ] Read: `project-handbook/adr/0030-v2-cosmo-artifact-store-minio-baseline-then-seaweedfs.md`
- [ ] Read: `project-handbook/decision-register/DR-0003-cosmo-minio-baseline-topology.md`
- [ ] Evidence run folder created: `project-handbook/status/evidence/TASK-006/<run-id>/`

## Implementation (repo changes)
- [ ] `v2/infra/compose/docker-compose.v2.yml` includes Cosmo + MinIO + deps with pinned images and **no Traefik exposure**
- [ ] Default v2 compose has **no host `ports:`** for Cosmo/MinIO services (internal-only)
- [ ] `v2/infra/vault/templates/agent.hcl` renders `/secrets/cosmo.env`, `/secrets/minio.env`, and `/secrets/artifacts.env`
- [ ] `v2/infra/vault/templates/cosmo.env.tpl` and `v2/infra/vault/templates/minio.env.tpl` exist and follow FDR-0001 naming
- [ ] `v2/scripts/vault/bootstrap-v2.sh` seeds `kv/data/tribuence/v2/{cosmo,minio}` per FDR-0001 with “no secrets printed” posture
- [ ] `artifact-bucket-init` uses a generic S3 client (prefer `amazon/aws-cli`), not `minio/mc`, and is idempotent
- [ ] `v2/scripts/v2-smoke.sh` includes:
  - [ ] forbidden host checks for `cosmo.local` and `minio.local` (Traefik must return 404)
  - [ ] “Cosmo artifact write/read” probe (store-agnostic; reused by `TASK-007`)

## Validation Evidence (must be captured)
- [ ] `v2-up` output captured (or `docker compose ps` + key logs) under `project-handbook/status/evidence/TASK-006/<run-id>/`
- [ ] `v2/scripts/vault/bootstrap-v2.sh` output captured and contains **no secret values**
- [ ] `artifact-bucket-init` run twice; both runs succeed; logs captured
- [ ] `V2_SMOKE_MODE=infra make -C v2 v2-smoke` passes; output captured
- [ ] On Apple Silicon, Cosmo containers run `linux/arm64` (no Docker Desktop `AMD64` warnings); v2 uses multi-arch image digests
- [ ] No stray one-shot containers remain after validation (e.g. `cosmo-db-migration-1`, `artifact-bucket-init-1`)
- [ ] Leak scan run over the evidence folder and shows **zero** matches for credential-shaped strings
- [ ] `pnpm -C project-handbook make -- validate` passes; output captured

## Before Marking `review`
- [ ] Feature status/plan docs updated as needed (links remain valid)
- [ ] Task status set to `review`: `pnpm -C project-handbook make -- task-status id=TASK-006 status=review`
