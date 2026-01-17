---
title: Implement: Router supergraph sync from Cosmo (Option B) - Commands
type: commands
date: 2026-01-10
task_id: TASK-008
tags: [commands]
links: []
---

# Commands: Implement: Router supergraph sync from Cosmo (Option B)

## Contract Defaults (copy/paste)
```bash
# Runtime artifact contract (in-container paths)
RUNTIME_SUPERGRAPH_DIR="/dist/graphql-runtime"
RUNTIME_SUPERGRAPH_PATH="$RUNTIME_SUPERGRAPH_DIR/supergraph.graphql"
RUNTIME_SUPERGRAPH_VOLUME="router-supergraph-runtime-v2"

# Cosmo fetch contract (matches legacy reference graphRef: tribuence@dev)
WGC_VERSION="0.63.0"
COSMO_FEDERATED_GRAPH_NAME="tribuence"
COSMO_FEDERATED_GRAPH_NAMESPACE="dev"
ROVER_VERSION="0.37.0"
ROVER_FEDERATION_VERSION="2.6.0"

# Cosmo controlplane URL for in-network containers (TASK-006 baseline)
COSMO_API_URL_DEFAULT="http://cosmo-controlplane:3001"

# Supergraph sync loop defaults
SUPERGRAPH_SYNC_POLL_INTERVAL_SECONDS_DEFAULT="30"
```

## Task Status Updates
```bash
pnpm -C project-handbook make -- task-status id=TASK-008 status=doing
pnpm -C project-handbook make -- task-status id=TASK-008 status=review
pnpm -C project-handbook make -- task-status id=TASK-008 status=done
```

## Validation Commands
```bash
pnpm -C project-handbook make -- validate
pnpm -C project-handbook make -- sprint-status
```

## Evidence Directory (required; do not overwrite existing files)
```bash
EVID_ROOT="project-handbook/status/evidence/TASK-008"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-router-supergraph-sync"
EVID_DIR="$EVID_ROOT/$RUN_ID"
mkdir -p "$EVID_DIR"
${EDITOR:-vi} "$EVID_DIR/index.md"
```

## Implementation: locate current Router wiring (snippets only)
```bash
rg -n "apollo-router|supergraph|APOLLO_ROUTER_SUPERGRAPH_PATH|APOLLO_ROUTER_HOT_RELOAD" \
  v2/infra/compose/docker-compose.v2.yml \
  v2/infra/compose/graphql/router.v2.yaml \
  v2/infra/vault/templates/router.env.tpl \
  v2/scripts/vault/bootstrap-v2.sh \
  -S | tee "$EVID_DIR/rg-router-supergraph-wiring.txt"
```

## Supergraph Sync: CLI fetch command (for debug/evidence only)
```bash
# NOTE: This runs on the host for documentation/debugging only.
# In implementation, supergraph-sync generates an Apollo Router-compatible supergraph by:
# 1) fetching an Apollo-compatible rover config via wgc, then
# 2) running rover supergraph compose (ELV2 license must be accepted non-interactively).
npx -y "wgc@${WGC_VERSION}" federated-graph fetch --help | tee "$EVID_DIR/wgc-fedgraph-fetch-help.txt"
npx -y "@apollo/rover@${ROVER_VERSION}" supergraph compose --help | tee "$EVID_DIR/rover-supergraph-compose-help.txt"
```

## Bring up v2 and validate refresh behavior
```bash
make -C v2 v2-down || true

# Required: provide non-default Keycloak admin creds (see project-handbook/AGENT.md)
KEYCLOAK_ADMIN=admin KEYCLOAK_ADMIN_PASSWORD=dev-not-admin make -C v2 v2-up | tee "$EVID_DIR/v2-up.txt"

docker compose -p tribuence-v2 -f v2/infra/compose/docker-compose.v2.yml ps | tee "$EVID_DIR/v2-ps.txt"

# Infra smoke (must include runtime supergraph assertions)
V2_SMOKE_MODE=infra make -C v2 v2-smoke | tee "$EVID_DIR/v2-smoke-infra.txt"
```

## Runtime Supergraph Assertions (evidence)
```bash
COMPOSE_FILE="v2/infra/compose/docker-compose.v2.yml"
PROJECT="tribuence-v2"

# 1) Router sees the runtime supergraph file and it is non-empty
docker compose -p "$PROJECT" -f "$COMPOSE_FILE" exec -T apollo-router sh -lc \
  "ls -la \"$RUNTIME_SUPERGRAPH_DIR\" && wc -c \"$RUNTIME_SUPERGRAPH_PATH\"" \
  | tee "$EVID_DIR/runtime-supergraph-router-stats.txt"

# 2) Capture supergraph-sync logs (must not include secret values)
docker compose -p "$PROJECT" -f "$COMPOSE_FILE" logs --tail=200 supergraph-sync \
  | tee "$EVID_DIR/supergraph-sync-logs.txt"
```

## Forced Refresh (same content, new inode) + Health Stability
```bash
COMPOSE_FILE="v2/infra/compose/docker-compose.v2.yml"
PROJECT="tribuence-v2"

# Force an atomic replace of the runtime supergraph file WITHOUT changing contents.
# This triggers Router --hot-reload watchers without requiring a real publish event.
docker compose -p "$PROJECT" -f "$COMPOSE_FILE" exec -T supergraph-sync sh -lc "
  set -eu
  SRC=\"$RUNTIME_SUPERGRAPH_PATH\"
  TMP=\"$RUNTIME_SUPERGRAPH_DIR/.force-refresh.$(date +%s).graphql\"
  cp \"$SRC\" \"$TMP\"
  mv \"$TMP\" \"$SRC\"
"

# Router should remain healthy after the forced refresh.
docker compose -p "$PROJECT" -f "$COMPOSE_FILE" logs --tail=200 apollo-router \
  | tee "$EVID_DIR/apollo-router-logs-after-refresh.txt"
V2_SMOKE_MODE=infra make -C v2 v2-smoke | tee "$EVID_DIR/v2-smoke-after-refresh.txt"
```

## Evidence Secret/Token Scan (must not show secret values)
```bash
# This is a coarse check to catch accidental auth/token prints in evidence files.
rg -n "Bearer\\s+|Authorization:|eyJ[A-Za-z0-9_-]+\\.eyJ|COSMO_API_KEY=|S3_SECRET_ACCESS_KEY=|MINIO_SECRET_KEY=" \
  "$EVID_DIR" -S > "$EVID_DIR/token-scan-hits.txt" || true
wc -l "$EVID_DIR/token-scan-hits.txt" | tee "$EVID_DIR/token-scan-hits-count.txt"
```

## Handbook Validation (required)
```bash
pnpm -C project-handbook make -- validate | tee "$EVID_DIR/handbook-validate.txt"
pnpm -C project-handbook make -- sprint-status | tee "$EVID_DIR/sprint-status.txt"
```

## Git (project-handbook + v2)
```bash
# project-handbook changes (task docs + any handbook updates)
git -C project-handbook status
git -C project-handbook commit -am "TASK-008: router supergraph sync task docs"

# v2 changes (implementation)
git -C v2 status
git -C v2 commit -am "TASK-008: Router consumes Cosmo supergraph via runtime artifact"
```
