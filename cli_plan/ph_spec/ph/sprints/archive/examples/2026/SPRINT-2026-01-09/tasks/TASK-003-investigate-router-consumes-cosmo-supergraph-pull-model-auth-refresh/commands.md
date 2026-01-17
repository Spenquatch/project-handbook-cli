---
title: Investigate: Router consumes Cosmo supergraph (pull model + auth + refresh) - Commands
type: commands
date: 2026-01-09
task_id: TASK-003
tags: [commands]
links: []
---

# Commands: Investigate: Router consumes Cosmo supergraph (pull model + auth + refresh)

## Task Status
```bash
ph task status --id TASK-003 --status doing
ph task status --id TASK-003 --status review
ph task status --id TASK-003 --status done
```

## Evidence Directory (required)
```bash
EVID_DIR="ph/status/evidence/TASK-003"
mkdir -p "$EVID_DIR"
${EDITOR:-vi} "$EVID_DIR/index.md"
```

## Inventory current Router wiring (snippets only)
```bash
rg -n "apollo-router|supergraph-local|APOLLO_ROUTER_SUPERGRAPH_PATH" \
  v2/infra/compose/docker-compose.v2.yml \
  v2/infra/compose/graphql/router.v2.yaml \
  v2/infra/vault/templates/router.env.tpl \
  -S | tee "$EVID_DIR/router-supergraph-wiring.txt"

# Avoid capturing the full supergraph file; capture stats only
ls -lh v2/infra/compose/graphql/supergraph-local.graphql | tee "$EVID_DIR/supergraph-local-stats.txt"
shasum -a 256 v2/infra/compose/graphql/supergraph-local.graphql | tee -a "$EVID_DIR/supergraph-local-stats.txt"
```

## Edit the Decision Register entry
```bash
${EDITOR:-vi} ph/decision-register/DR-0005-router-supergraph-consumption-from-cosmo.md
```

## Handbook Validation
```bash
ph validate
```

## Notes
- Do not capture large supergraph contents as evidence; store only a hash/size and the relevant wiring excerpts.
