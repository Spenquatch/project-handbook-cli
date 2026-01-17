---
title: Implement: v2 Cosmo+MinIO baseline (from legacy reference) - Implementation Steps
type: implementation
date: 2026-01-09
task_id: TASK-006
tags: [implementation]
links: []
---

# Implementation Steps: Implement: v2 Cosmo+MinIO baseline (from legacy reference)

## Overview
Implement the **MinIO baseline** for Cosmo artifact storage in the default v2 stack (internal-only), following:
- `project-handbook/adr/0030-v2-cosmo-artifact-store-minio-baseline-then-seaweedfs.md`
- `project-handbook/decision-register/DR-0003-cosmo-minio-baseline-topology.md`
- `project-handbook/features/v2_registry-cosmo-minio-required/fdr/0001-vault-secrets-contract-cosmo-minio.md`

## Prerequisites
- `TASK-002` is `done` (secrets contract accepted; referenced as FDR-0001).
- Local Docker works; you can run `make -C v2 v2-up` (Keycloak admin creds required; see `project-handbook/AGENT.md`).
- You will store evidence under `project-handbook/status/evidence/TASK-006/` (create a per-run subfolder to avoid clobbering existing files).

## Step 1 — Preflight: lock the contracts and pins
1. Read the controlling docs:
   - `project-handbook/adr/0030-v2-cosmo-artifact-store-minio-baseline-then-seaweedfs.md`
   - `project-handbook/decision-register/DR-0003-cosmo-minio-baseline-topology.md`
   - `project-handbook/features/v2_registry-cosmo-minio-required/architecture/ARCHITECTURE.md`
   - `project-handbook/features/v2_registry-cosmo-minio-required/implementation/IMPLEMENTATION.md`
   - `project-handbook/features/v2_registry-cosmo-minio-required/fdr/0001-vault-secrets-contract-cosmo-minio.md`
2. Confirm the version pins you will use match DR-0003/feature docs (Cosmo bundle tag, MinIO tag, deps tags).
3. Confirm the posture rules you must enforce:
   - no Traefik routers/labels for Cosmo/MinIO
   - no host `ports:` bindings for Cosmo/MinIO in the default compose

Evidence to capture:
- your per-run evidence index (see `validation.md`) listing which files prove each acceptance gate.

## Step 2 — Compose wiring (v2 default stack; internal-only)
Edit `v2/infra/compose/docker-compose.v2.yml` to add:
- **Artifact store**:
  - `minio` (pinned image per DR-0003), on `tribuence-v2-net`, no `ports:`
  - persistent volume for MinIO data
- **Cosmo dependencies** (internal-only):
  - `cosmo-clickhouse` (pinned)
  - `cosmo-redis` (pinned)
  - `cosmo-nats` (pinned)
  - `cosmo-keycloak` (pinned Cosmo Keycloak image) + realm import wiring as needed
- **Cosmo services** (pinned Cosmo bundle tag):
  - `cosmo-controlplane`, `cosmo-cdn`, `cosmo-studio`
- **One-shot helpers** (internal-only, no Traefik):
  - `cosmo-postgres-bootstrap` (creates Cosmo DB(s)/roles in shared v2 Postgres)
  - `cosmo-db-migration` and `cosmo-clickhouse-migration` (run Cosmo migrations)
  - `artifact-bucket-init` (idempotent bucket creator using `amazon/aws-cli`)
  - `cosmo-seed` (one-shot; profile-gated) to provision initial org/api key

Rules while wiring:
- Every new service mounts `vault-secrets-v2:/secrets` and loads env via an env-file wrapper (do not print env).
- Use `expose:` for internal ports; do not add `ports:` for Cosmo/MinIO.
- Do not add any Traefik labels/routers for Cosmo/MinIO.

## Step 3 — Vault Agent templates (render `/secrets/*.env`)
Implement the FDR-0001 contract by adding templates under `v2/infra/vault/templates/` and wiring them in `v2/infra/vault/templates/agent.hcl`:
- Add templates:
  - `v2/infra/vault/templates/minio.env.tpl` → `/secrets/minio.env`
  - `v2/infra/vault/templates/cosmo.env.tpl` → `/secrets/cosmo.env`
  - `v2/infra/vault/templates/artifacts.env.tpl` → `/secrets/artifacts.env` (single source of truth for artifact store endpoint + creds + bucket; consumed by `artifact-bucket-init`, the smoke probe, and referenced by `cosmo.env.tpl`)

Hard rule: templates must not render secrets into logs; do not print template outputs in evidence.

`/secrets/artifacts.env` required keys (names only; do not print values):
- `S3_ENDPOINT_URL` (MinIO baseline: `http://minio:9000`)
- `S3_REGION` (default `auto`)
- `S3_ACCESS_KEY_ID`
- `S3_SECRET_ACCESS_KEY`
- `S3_FORCE_PATH_STYLE` (default `true`)
- `COSMO_S3_BUCKET`

## Step 4 — Vault bootstrap (seed KV without leakage)
Update `v2/scripts/vault/bootstrap-v2.sh` to seed and/or preserve values for:
- `kv/data/tribuence/v2/minio`:
  - `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `COSMO_S3_BUCKET`
- `kv/data/tribuence/v2/cosmo`:
  - keys listed in FDR-0001 (Postgres, ClickHouse, auth, Cosmo Keycloak, seed, plus non-secret config keys)

Requirements:
- Idempotent (re-running does not rotate secrets unexpectedly).
- “No secrets printed” posture from FDR-0001 (never echo values; never dump payload JSON containing secret values).

## Step 5 — Bucket init (store-agnostic; reusable for SeaweedFS)
Implement `artifact-bucket-init` so it can be reused later by swapping only the S3 endpoint:
- Use a pinned `amazon/aws-cli` image.
- Read bucket + endpoint + creds from `/secrets/artifacts.env` (recommended) or from a dedicated env file you define.
- Perform a deterministic write/read probe or bucket existence check without printing secrets.
- Must be idempotent: a second run is a no-op success.

## Step 6 — Smoke probes (include “Cosmo artifact write/read”)
Update `v2/scripts/v2-smoke.sh` so **infra mode** enforces:
1. **No Traefik exposure**:
   - Add forbidden-host checks for `cosmo.local` and `minio.local` (expect 404).
2. **Cosmo artifact write/read probe** (store-agnostic):
   - On `tribuence-v2-net`, run a short-lived S3 client (prefer `amazon/aws-cli`) that:
     - writes a small object into `COSMO_S3_BUCKET`,
     - reads it back,
     - verifies the content matches.

This probe must pass against MinIO now and SeaweedFS later (`TASK-007`) by changing only the endpoint.

## Step 7 — Validate + evidence + docs
1. Run the v2 stack and bootstrap secrets (see `commands.md` for copy/paste).
2. Run `V2_SMOKE_MODE=infra make -C v2 v2-smoke` and capture output.
3. Capture evidence:
   - v2 bring-up logs (or `docker compose ps` + relevant service logs)
   - vault bootstrap output (redaction-safe)
   - smoke output, including the artifact probe
4. Update any operator-facing docs as needed (minimum: keep `project-handbook/features/v2_registry-cosmo-minio-required/*` and `v2/docs/README.md` consistent with the new required baseline).
5. Run `pnpm -C project-handbook make -- validate`.
6. Ensure `checklist.md` is fully satisfied; move task to `review`.

## Notes / Guardrails
- Do not “hand fix” running containers; make wiring changes in compose/templates/scripts and re-run.
- Evidence must not contain secrets/tokens/cookies; scan evidence before sharing.
