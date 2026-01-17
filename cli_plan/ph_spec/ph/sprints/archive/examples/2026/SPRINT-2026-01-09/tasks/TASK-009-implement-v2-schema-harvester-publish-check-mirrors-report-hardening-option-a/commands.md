---
title: Implement: v2 schema harvester publish/check + mirrors + report hardening (Option A) - Commands
type: commands
date: 2026-01-10
task_id: TASK-009
tags: [commands]
links: []
---

# Commands: Implement: v2 schema harvester publish/check + mirrors + report hardening (Option A)

## Contract Defaults (copy/paste)
```bash
WGC_VERSION="0.63.0"
COSMO_FEDERATED_GRAPH_NAME="tribuence"
COSMO_FEDERATED_GRAPH_NAMESPACE="dev"
COSMO_API_URL_DEFAULT="http://cosmo-controlplane:3001"

INVENTORY_FILE="v2/infra/compose/graphql/subgraphs.yaml"
MIRRORS_DIR="v2/infra/compose/graphql/subgraphs"
REPORT_FILE="v2/.tmp/harvester/publish-report.json"
```

## Task Status Updates
```bash
ph task status --id TASK-009 --status doing
ph task status --id TASK-009 --status review
ph task status --id TASK-009 --status done
```

## Local dev (v2 stack)
```bash
# Bring up v2 (requires non-default Keycloak admin creds; follow TASK-006 contract)
KEYCLOAK_ADMIN=admin KEYCLOAK_ADMIN_PASSWORD=dev-not-admin make -C v2 v2-up

# Smoke test (router-level)
make -C v2 v2-smoke
```

## Assert Vault-rendered Cosmo CLI env exists (no leakage)
```bash
COMPOSE_FILE="v2/infra/compose/docker-compose.v2.yml"
PROJECT="tribuence-v2"

# IMPORTANT: do not cat env files; only assert existence/non-empty.
# Note: Vault Agent renders into its own mount, but consumers mount the same volume at `/secrets`.
docker compose -p "$PROJECT" -f "$COMPOSE_FILE" exec -T supergraph-sync sh -lc \
  "test -s /secrets/cosmo-cli.env && echo OK:/secrets/cosmo-cli.env"
```

## Validation Commands (handbook)
```bash
ph validate
ph sprint status
```

## Evidence directory
```bash
EVID_ROOT="ph/status/evidence/TASK-009"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-harvester-publish-check"
EVID_DIR="$EVID_ROOT/$RUN_ID"
mkdir -p "$EVID_DIR"
${EDITOR:-vi} "$EVID_DIR/index.md"
```

## Implementation (expected targets; create if missing)
```bash
# Canonical publish/check entrypoint (create in v2/Makefile)
make -C v2 v2-publish
```

## Git Integration (multi-repo)
```bash
git -C v2 status
git -C v2 add -A
git -C v2 commit -m "TASK-009: v2 schema harvester publish/check + hardening" || true

git -C <PH_ROOT> status
git -C <PH_ROOT> add -A
git -C <PH_ROOT> commit -m "TASK-009: update harvester docs/evidence" || true
```

## Notes
- Do not print or capture secret values in evidence (Vault tokens, Cosmo API keys, `.env` dumps).
- When capturing logs, prefer sanitized excerpts and `rg` checks for secret-looking patterns.
