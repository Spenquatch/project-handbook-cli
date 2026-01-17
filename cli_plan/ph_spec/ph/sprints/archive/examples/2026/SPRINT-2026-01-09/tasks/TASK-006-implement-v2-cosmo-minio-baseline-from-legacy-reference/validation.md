---
title: Implement: v2 Cosmo+MinIO baseline (from legacy reference) - Validation Guide
type: validation
date: 2026-01-09
task_id: TASK-006
tags: [validation]
links: []
---

# Validation Guide: Implement: v2 Cosmo+MinIO baseline (from legacy reference)

## Automated Validation
```bash
pnpm -C project-handbook make -- validate
pnpm -C project-handbook make -- sprint-status
```

## Manual Validation (copy/paste; store evidence)

### 0) Evidence folder (per-run)
```bash
EVID_ROOT="project-handbook/status/evidence/TASK-006"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-cosmo-minio-baseline"
EVID_DIR="$EVID_ROOT/$RUN_ID"
mkdir -p "$EVID_DIR"
```

Evidence you must produce (minimum):
- `project-handbook/status/evidence/TASK-006/<run-id>/v2-ps.txt`
- `project-handbook/status/evidence/TASK-006/<run-id>/vault-bootstrap.txt`
- `project-handbook/status/evidence/TASK-006/<run-id>/artifact-bucket-init-run1.txt`
- `project-handbook/status/evidence/TASK-006/<run-id>/artifact-bucket-init-run2.txt`
- `project-handbook/status/evidence/TASK-006/<run-id>/v2-smoke-infra.txt`
- `project-handbook/status/evidence/TASK-006/<run-id>/v2-ps-post-infra.txt`
- `project-handbook/status/evidence/TASK-006/<run-id>/leak-scan.txt`
- `project-handbook/status/evidence/TASK-006/<run-id>/handbook-validate.txt`

### 1) Bring up v2 (required)
```bash
make -C v2 v2-down || true
KEYCLOAK_ADMIN=admin KEYCLOAK_ADMIN_PASSWORD=dev-not-admin make -C v2 v2-up 2>&1 | tee "$EVID_DIR/v2-up.txt"
docker compose -p tribuence-v2 -f v2/infra/compose/docker-compose.v2.yml ps | tee "$EVID_DIR/v2-ps.txt"
```

Pass criteria:
- `docker compose ... ps` shows Cosmo + MinIO + deps running (or expected one-shot jobs completed successfully).
- No Cosmo/MinIO services expose host `ports:` in the `ps` output.
- No one-shot Cosmo init containers remain after validation (e.g. `cosmo-db-migration-1`, `artifact-bucket-init-1`).

### 2) Vault bootstrap (no leakage)
```bash
KEYCLOAK_ADMIN=admin KEYCLOAK_ADMIN_PASSWORD=dev-not-admin \
NEXT_PUBLIC_REQUIRE_AUTH=true \
V2_VAULT_FETCH_KEYCLOAK_CLIENT_SECRET=true \
V2_VAULT_MINT_ANYLLM_API_KEY=true \
  bash v2/scripts/vault/bootstrap-v2.sh 2>&1 | tee "$EVID_DIR/vault-bootstrap.txt"
```

Pass criteria:
- Script exits 0.
- Output contains no secret values (only safe “value not printed” messaging).

### 3) Bucket init (idempotent; store-agnostic)
```bash
docker compose -p tribuence-v2 -f v2/infra/compose/docker-compose.v2.yml --profile cosmo-init run --rm artifact-bucket-init \
  | tee "$EVID_DIR/artifact-bucket-init-run1.txt"

docker compose -p tribuence-v2 -f v2/infra/compose/docker-compose.v2.yml --profile cosmo-init run --rm artifact-bucket-init \
  | tee "$EVID_DIR/artifact-bucket-init-run2.txt"
```

Pass criteria:
- Both runs exit 0.
- Second run performs no destructive action and still succeeds.

### 4) Smoke (must include artifact write/read probe)
```bash
V2_SMOKE_MODE=infra make -C v2 v2-smoke | tee "$EVID_DIR/v2-smoke-infra.txt"
```

Pass criteria:
- Output includes passing checks for:
  - forbidden host: `cosmo.local` (404)
  - forbidden host: `minio.local` (404)
  - “Cosmo artifact write/read” probe passes

### 4b) Container hygiene (no stray one-shots)
```bash
docker compose -p tribuence-v2 -f v2/infra/compose/docker-compose.v2.yml ps -a | tee "$EVID_DIR/v2-ps-post-infra.txt"
```

Pass criteria:
- `ps -a` output does not include exited/created one-shot containers (they should have been run with `docker compose run --rm`).

### 5) Evidence leak scan (must be clean)
```bash
rg -n "http://[^\\s]+:[^\\s]+@minio:9000|AWS_SECRET_ACCESS_KEY=|MINIO_SECRET_KEY=|S3_SECRET_ACCESS_KEY=" "$EVID_DIR" -S \
  | tee "$EVID_DIR/leak-scan.txt" || true
```

Pass criteria:
- `leak-scan.txt` is empty (or contains only clearly-redacted placeholders).

### 6) Handbook validation (store report)
```bash
pnpm -C project-handbook make -- validate | tee "$EVID_DIR/handbook-validate.txt"
```

Pass criteria:
- Command exits 0 and `project-handbook/status/validation.json` is updated.

## Sign-off
- [ ] All validation steps completed
- [ ] Evidence captured under `project-handbook/status/evidence/TASK-006/<run-id>/`
- [ ] Ready to mark task as "done"

## Reviewer Decision (2026-01-11)

Decision: **APPROVE**

Reproduced evidence (review run):
- Evidence folder: `project-handbook/status/evidence/TASK-006/20260111T002840Z-reviewer/`
- Commands executed (high-level):
  - `make -C v2 v2-down || true`
  - `TRAEFIK_ENTRYPOINT_HTTP=8080 TRAEFIK_ENTRYPOINT_HTTPS=8443 KEYCLOAK_ADMIN=admin KEYCLOAK_ADMIN_PASSWORD=dev-not-admin make -C v2 v2-up`
  - `V2_VAULT_FETCH_KEYCLOAK_CLIENT_SECRET=true V2_VAULT_MINT_ANYLLM_API_KEY=true bash v2/scripts/vault/bootstrap-v2.sh`
  - `docker compose ... --profile cosmo-init run --rm artifact-bucket-init` (twice)
  - `V2_SMOKE_MODE=infra V2_SMOKE_ROUTER_URL=http://router.local:8080/ make -C v2 v2-smoke`
  - `pnpm -C project-handbook make -- validate`

Notes (review-blocking fixes applied during review):
- `v2/infra/vault/templates/cosmo.env.tpl` now also renders FDR-named env vars (`COSMO_AUTH_*`, `COSMO_SEED_*`) alongside existing Cosmo runtime env names.
- `v2/scripts/vault/bootstrap-v2.sh` now retries Keycloak `kcadm` auth briefly to avoid flaking when Keycloak is still starting.
