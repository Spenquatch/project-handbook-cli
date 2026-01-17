---
title: Cutover: Replace MinIO with SeaweedFS S3 gateway - Commands
type: commands
date: 2026-01-09
task_id: TASK-007
tags: [commands]
links: []
---

# Commands: Cutover: Replace MinIO with SeaweedFS S3 gateway

## Task Status Updates
```bash
pnpm -C project-handbook make -- task-status id=TASK-007 status=doing
pnpm -C project-handbook make -- task-status id=TASK-007 status=review
pnpm -C project-handbook make -- task-status id=TASK-007 status=done
```

## Evidence Directory (required; do not overwrite existing files)
```bash
EVID_ROOT="project-handbook/status/evidence/TASK-007"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-seaweedfs-cutover"
EVID_DIR="$EVID_ROOT/$RUN_ID"
mkdir -p "$EVID_DIR"
${EDITOR:-vi} "$EVID_DIR/index.md"
```

## Read the controlling docs (capture copies if helpful)
```bash
sed -n '1,220p' project-handbook/adr/0030-v2-cosmo-artifact-store-minio-baseline-then-seaweedfs.md | tee "$EVID_DIR/adr-0030.txt"
sed -n '1,220p' project-handbook/adr/0015-tribuence-mini-v2-cosmo-minio-and-schema-publishing.md | tee "$EVID_DIR/adr-0015.txt"
sed -n '1,260p' project-handbook/decision-register/DR-0003-cosmo-minio-baseline-topology.md | tee "$EVID_DIR/dr-0003.txt"
```

## Bring up v2 (service commands; required for validation)
```bash
make -C v2 v2-down || true
KEYCLOAK_ADMIN=admin KEYCLOAK_ADMIN_PASSWORD=dev-not-admin make -C v2 v2-up | tee "$EVID_DIR/v2-up.txt"
docker compose -p tribuence-v2 -f v2/infra/compose/docker-compose.v2.yml ps | tee "$EVID_DIR/v2-ps.txt"
```

## Vault bootstrap (must not print secret values)
```bash
NEXT_PUBLIC_REQUIRE_AUTH=true \
V2_VAULT_FETCH_KEYCLOAK_CLIENT_SECRET=true \
V2_VAULT_MINT_ANYLLM_API_KEY=true \
  bash v2/scripts/vault/bootstrap-v2.sh | tee "$EVID_DIR/vault-bootstrap.txt"
```

## Bucket init (idempotent; run twice)
```bash
docker compose -p tribuence-v2 -f v2/infra/compose/docker-compose.v2.yml run --rm artifact-bucket-init \
  | tee "$EVID_DIR/artifact-bucket-init-run1.txt"
docker compose -p tribuence-v2 -f v2/infra/compose/docker-compose.v2.yml run --rm artifact-bucket-init \
  | tee "$EVID_DIR/artifact-bucket-init-run2.txt"
```

## Smoke (infra mode must include artifact write/read probe)
```bash
V2_SMOKE_MODE=infra make -C v2 v2-smoke | tee "$EVID_DIR/v2-smoke-infra.txt"
```

## Confirm MinIO is removed (after cutover)
```bash
rg -n "minio:9000|minio\\b" v2/infra/compose/docker-compose.v2.yml v2/scripts v2/infra/vault/templates -S \
  | tee "$EVID_DIR/rg-minio-after.txt" || true
```

## Evidence leak scan (must be clean)
```bash
rg -n "http://[^\\s<>]+:[^\\s<>]+@seaweedfs:8333|AWS_SECRET_ACCESS_KEY=|S3_SECRET_ACCESS_KEY=" "$EVID_DIR" -S \
  | tee "$EVID_DIR/leak-scan.txt" || true
```

## Handbook validation (required)
```bash
pnpm -C project-handbook make -- validate | tee "$EVID_DIR/handbook-validate.txt"
pnpm -C project-handbook make -- sprint-status | tee "$EVID_DIR/sprint-status.txt"
```

## Notes
- Do not proceed to remove MinIO until the artifact probe passes against SeaweedFS.
- Evidence must not contain secrets/tokens/cookies; scan before sharing.
