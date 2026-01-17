---
title: Implement: v2 Cosmo+MinIO baseline (from legacy reference) - Commands
type: commands
date: 2026-01-09
task_id: TASK-006
tags: [commands]
links: []
---

# Commands: Implement: v2 Cosmo+MinIO baseline (from legacy reference)

## Task Status Updates
```bash
pnpm -C project-handbook make -- task-status id=TASK-006 status=doing
pnpm -C project-handbook make -- task-status id=TASK-006 status=review
pnpm -C project-handbook make -- task-status id=TASK-006 status=done
```

## Evidence Directory (required; do not overwrite existing files)
```bash
EVID_ROOT="project-handbook/status/evidence/TASK-006"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-cosmo-minio-baseline"
EVID_DIR="$EVID_ROOT/$RUN_ID"
mkdir -p "$EVID_DIR"
${EDITOR:-vi} "$EVID_DIR/index.md"
```

## Read the controlling docs (capture copies if helpful)
```bash
sed -n '1,220p' project-handbook/adr/0030-v2-cosmo-artifact-store-minio-baseline-then-seaweedfs.md | tee "$EVID_DIR/adr-0030.txt"
sed -n '1,260p' project-handbook/decision-register/DR-0003-cosmo-minio-baseline-topology.md | tee "$EVID_DIR/dr-0003.txt"
sed -n '1,260p' project-handbook/features/v2_registry-cosmo-minio-required/fdr/0001-vault-secrets-contract-cosmo-minio.md | tee "$EVID_DIR/fdr-0001.txt"
```

## Bring up v2 (service commands; required for validation)
```bash
make -C v2 v2-down || true

# Required: provide non-default Keycloak admin creds (see project-handbook/AGENT.md)
KEYCLOAK_ADMIN=admin KEYCLOAK_ADMIN_PASSWORD=dev-not-admin make -C v2 v2-up 2>&1 | tee "$EVID_DIR/v2-up.txt"

docker compose -p tribuence-v2 -f v2/infra/compose/docker-compose.v2.yml ps | tee "$EVID_DIR/v2-ps.txt"
```

## Container hygiene (no stray one-shots)
```bash
# Removes any stale one-shot containers that may have been created by a prior `docker compose --profile cosmo-init up`.
make -C v2 v2-clean-cosmo-init || true
```

## Seed/render Vault secrets (must not print secret values)
```bash
KEYCLOAK_ADMIN=admin KEYCLOAK_ADMIN_PASSWORD=dev-not-admin \
NEXT_PUBLIC_REQUIRE_AUTH=true \
V2_VAULT_FETCH_KEYCLOAK_CLIENT_SECRET=true \
V2_VAULT_MINT_ANYLLM_API_KEY=true \
  bash v2/scripts/vault/bootstrap-v2.sh 2>&1 | tee "$EVID_DIR/vault-bootstrap.txt"
```

## Bucket init (must be idempotent; run twice)
```bash
docker compose -p tribuence-v2 -f v2/infra/compose/docker-compose.v2.yml --profile cosmo-init run --rm artifact-bucket-init \
  | tee "$EVID_DIR/artifact-bucket-init-run1.txt"

docker compose -p tribuence-v2 -f v2/infra/compose/docker-compose.v2.yml --profile cosmo-init run --rm artifact-bucket-init \
  | tee "$EVID_DIR/artifact-bucket-init-run2.txt"
```

## Smoke (infra mode must include artifact write/read probe)
```bash
V2_SMOKE_MODE=infra make -C v2 v2-smoke | tee "$EVID_DIR/v2-smoke-infra.txt"
```

## Post-infra container snapshot (should not include exited one-shots)
```bash
docker compose -p tribuence-v2 -f v2/infra/compose/docker-compose.v2.yml ps -a | tee "$EVID_DIR/v2-ps-post-infra.txt"
```

## Isolation (host access should fail; Traefik hostnames should be 404)
```bash
# Traefik negative host checks (expect 404)
curl -sS -o /dev/null -w '%{http_code}\n' --resolve cosmo.local:80:127.0.0.1 http://cosmo.local/ | tee "$EVID_DIR/traefik-cosmo-local.txt"
curl -sS -o /dev/null -w '%{http_code}\n' --resolve minio.local:80:127.0.0.1 http://minio.local/ | tee "$EVID_DIR/traefik-minio-local.txt"

# Host port checks (expect connection refused/timeouts; adjust if you changed Traefik ports)
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:9000/ || true
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3001/ || true
```

## Logs (curate; do not capture secrets)
```bash
docker compose -p tribuence-v2 -f v2/infra/compose/docker-compose.v2.yml logs --tail=200 \
  minio cosmo-controlplane cosmo-cdn cosmo-keycloak | tee "$EVID_DIR/cosmo-minio-logs-tail.txt"
```

## Evidence leak scan (should have zero hits)
```bash
rg -n "http://[^\\s]+:[^\\s]+@minio:9000|AWS_SECRET_ACCESS_KEY=|MINIO_SECRET_KEY=|S3_SECRET_ACCESS_KEY=" "$EVID_DIR" -S \
  | tee "$EVID_DIR/leak-scan.txt" || true
```

## Handbook validation (required)
```bash
pnpm -C project-handbook make -- validate | tee "$EVID_DIR/handbook-validate.txt"
pnpm -C project-handbook make -- sprint-status | tee "$EVID_DIR/sprint-status.txt"
```

## Notes
- Evidence must not contain secrets/tokens/cookies; scan before sharing.
- Prefer changing wiring in code/docs, not “hand fixing” running containers.
