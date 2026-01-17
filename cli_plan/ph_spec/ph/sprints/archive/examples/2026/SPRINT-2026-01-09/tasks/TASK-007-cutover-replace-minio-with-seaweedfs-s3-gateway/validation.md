---
title: Cutover: Replace MinIO with SeaweedFS S3 gateway - Validation Guide
type: validation
date: 2026-01-09
task_id: TASK-007
tags: [validation]
links: []
---

# Validation Guide: Cutover: Replace MinIO with SeaweedFS S3 gateway

## Automated Validation
```bash
pnpm -C project-handbook make -- validate
pnpm -C project-handbook make -- sprint-status
```

## Manual Validation (copy/paste; store evidence)

### 0) Evidence folder (per-run)
```bash
EVID_ROOT="project-handbook/status/evidence/TASK-007"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-seaweedfs-cutover"
EVID_DIR="$EVID_ROOT/$RUN_ID"
mkdir -p "$EVID_DIR"
```

Evidence you must produce (minimum):
- `project-handbook/status/evidence/TASK-007/<run-id>/v2-ps.txt`
- `project-handbook/status/evidence/TASK-007/<run-id>/vault-bootstrap.txt`
- `project-handbook/status/evidence/TASK-007/<run-id>/artifact-bucket-init-run1.txt`
- `project-handbook/status/evidence/TASK-007/<run-id>/artifact-bucket-init-run2.txt`
- `project-handbook/status/evidence/TASK-007/<run-id>/v2-smoke-infra.txt`
- `project-handbook/status/evidence/TASK-007/<run-id>/rg-minio-after.txt`
- `project-handbook/status/evidence/TASK-007/<run-id>/leak-scan.txt`
- `project-handbook/status/evidence/TASK-007/<run-id>/handbook-validate.txt`

### 1) Bring up v2 (required)
```bash
make -C v2 v2-down || true
KEYCLOAK_ADMIN=admin KEYCLOAK_ADMIN_PASSWORD=dev-not-admin make -C v2 v2-up | tee "$EVID_DIR/v2-up.txt"
docker compose -p tribuence-v2 -f v2/infra/compose/docker-compose.v2.yml ps | tee "$EVID_DIR/v2-ps.txt"
```

Pass criteria:
- `seaweedfs` is running and has no host `ports:`.
- MinIO may still be present at this stage if you haven’t removed it yet.

### 2) Vault bootstrap (no leakage)
```bash
NEXT_PUBLIC_REQUIRE_AUTH=true \
V2_VAULT_FETCH_KEYCLOAK_CLIENT_SECRET=true \
V2_VAULT_MINT_ANYLLM_API_KEY=true \
  bash v2/scripts/vault/bootstrap-v2.sh | tee "$EVID_DIR/vault-bootstrap.txt"
```

Pass criteria:
- Script exits 0 and prints no secret values.

### 3) Bucket init (idempotent; against SeaweedFS endpoint)
```bash
docker compose -p tribuence-v2 -f v2/infra/compose/docker-compose.v2.yml run --rm artifact-bucket-init \
  | tee "$EVID_DIR/artifact-bucket-init-run1.txt"
docker compose -p tribuence-v2 -f v2/infra/compose/docker-compose.v2.yml run --rm artifact-bucket-init \
  | tee "$EVID_DIR/artifact-bucket-init-run2.txt"
```

Pass criteria:
- Both runs exit 0 and are non-destructive.

### 4) Smoke (must include artifact write/read probe)
```bash
V2_SMOKE_MODE=infra make -C v2 v2-smoke | tee "$EVID_DIR/v2-smoke-infra.txt"
```

Pass criteria:
- “Cosmo artifact write/read” probe passes against SeaweedFS.
- Forbidden host checks still pass (Traefik returns 404 for `cosmo.local` and `minio.local`).

### 5) Remove MinIO and prove it’s gone
```bash
rg -n "minio:9000|minio\\b" v2/infra/compose/docker-compose.v2.yml v2/scripts v2/infra/vault/templates -S \
  | tee "$EVID_DIR/rg-minio-after.txt" || true
```

Pass criteria:
- After your compose changes, `rg-minio-after.txt` shows no remaining runtime references to the `minio` service (except historical comments if any).

### 6) Evidence leak scan (must be clean)
```bash
rg -n "http://[^\\s<>]+:[^\\s<>]+@seaweedfs:8333|AWS_SECRET_ACCESS_KEY=|S3_SECRET_ACCESS_KEY=" "$EVID_DIR" -S \
  | tee "$EVID_DIR/leak-scan.txt" || true
```

Pass criteria:
- `leak-scan.txt` is empty (or contains only clearly-redacted placeholders).

### 7) Handbook validation (store report)
```bash
pnpm -C project-handbook make -- validate | tee "$EVID_DIR/handbook-validate.txt"
```

Pass criteria:
- Command exits 0 and `project-handbook/status/validation.json` is updated.

## Sign-off
- [ ] All validation steps completed
- [ ] Evidence captured under `project-handbook/status/evidence/TASK-007/<run-id>/`
- [ ] Ready to mark task as "done"
