---
title: Implement: v2 registry-backed codegen wiring (Cosmo fetch + drift gate + CI ordering) - Commands
type: commands
date: 2026-01-10
task_id: TASK-010
tags: [commands]
links: []
---

# Commands: Implement: v2 registry-backed codegen wiring (Cosmo fetch + drift gate + CI ordering)

## Contract Defaults (copy/paste)
```bash
WGC_VERSION="0.63.0"
COSMO_FEDERATED_GRAPH_NAME="tribuence"
COSMO_FEDERATED_GRAPH_NAMESPACE="dev"
COSMO_API_URL_DEFAULT="http://cosmo-controlplane:3001"

FETCHED_SCHEMA_FILE="v2/.tmp/codegen/supergraph.graphql"
GENERATED_DIR="v2/apps/tribuence-mini/src/generated"
```

## Task Status Updates
```bash
ph task status --id TASK-010 --status doing
ph task status --id TASK-010 --status review
ph task status --id TASK-010 --status done
```

## Validation Commands (handbook)
```bash
ph validate
ph sprint status
```

## Evidence directory
```bash
EVID_ROOT="ph/status/evidence/TASK-010"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-codegen-from-cosmo"
EVID_DIR="$EVID_ROOT/$RUN_ID"
mkdir -p "$EVID_DIR"
${EDITOR:-vi} "$EVID_DIR/index.md"
```

## Assert Vault-rendered Cosmo CLI env exists (no leakage)
```bash
COMPOSE_FILE="v2/infra/compose/docker-compose.v2.yml"
PROJECT="tribuence-v2"

# IMPORTANT: do not cat env files; only assert existence/non-empty.
# NOTE: /secrets/cosmo-cli.env is mounted into tools/helpers (e.g. supergraph-sync), not vault-agent.
docker compose -p "$PROJECT" -f "$COMPOSE_FILE" exec -T supergraph-sync sh -lc \
  "ls -la /secrets && test -s /secrets/cosmo-cli.env && echo OK:/secrets/cosmo-cli.env"
```

## WGC fetch-schema help (debug/evidence)
```bash
npx -y "wgc@${WGC_VERSION}" federated-graph fetch-schema --help | tee "$EVID_DIR/wgc-fetch-schema-help.txt"
```

## Implementation (expected targets; create if missing)
```bash
# Schema fetch + codegen (create as part of this task)
make -C v2 v2-codegen
make -C v2 v2-codegen-check

# CI ordering gate (must be explicit)
make -C v2 v2-publish
make -C v2 v2-codegen-check
pnpm -C v2/apps/tribuence-mini typecheck
```

## Git Integration (multi-repo)
```bash
git -C v2 status
git -C v2 add -A
git -C v2 commit -m "TASK-010: v2 codegen wiring (Cosmo fetch + drift gate)" || true

git -C <PH_ROOT> status
git -C <PH_ROOT> add -A
git -C <PH_ROOT> commit -m "TASK-010: update codegen task docs/evidence" || true
```

## Notes
- Do not print or capture secret values in evidence (Vault tokens, Cosmo API keys, `.env` dumps).
