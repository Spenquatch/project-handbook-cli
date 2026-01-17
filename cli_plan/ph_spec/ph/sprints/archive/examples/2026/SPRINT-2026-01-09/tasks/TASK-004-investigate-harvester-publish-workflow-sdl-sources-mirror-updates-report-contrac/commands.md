---
title: Investigate: Harvester publish workflow (SDL sources, mirror updates, report contract) + codegen wiring - Commands
type: commands
date: 2026-01-09
task_id: TASK-004
tags: [commands]
links: []
---

# Commands: Investigate: Harvester publish workflow (SDL sources, mirror updates, report contract) + codegen wiring

## Task Status
```bash
ph task status --id TASK-004 --status doing
ph task status --id TASK-004 --status review
ph task status --id TASK-004 --status done
```

## Evidence Directory (required)
```bash
EVID_DIR="ph/status/evidence/TASK-004"
mkdir -p "$EVID_DIR"
${EDITOR:-vi} "$EVID_DIR/index.md"
```

## Inventory current SDL mirrors (snippets only)
```bash
sed -n '1,120p' v2/infra/compose/graphql/subgraphs.yaml | tee "$EVID_DIR/subgraphs-yaml.txt"
find v2/infra/compose/graphql/subgraphs -maxdepth 2 -type f -name 'schema.graphql' -print | tee "$EVID_DIR/subgraphs-schema-files.txt"

# Avoid capturing the full supergraph; capture stats only
ls -lh v2/infra/compose/graphql/supergraph-local.graphql | tee "$EVID_DIR/supergraph-local-stats.txt"
shasum -a 256 v2/infra/compose/graphql/supergraph-local.graphql | tee -a "$EVID_DIR/supergraph-local-stats.txt"
```

## Inventory existing smoke expectations (inputs to publish/check)
```bash
rg -n "supergraph|subgraphs|join__Graph|composition" v2/scripts/v2-smoke.sh -S | tee "$EVID_DIR/v2-smoke-schema-hooks.txt"
```

## Search for existing codegen wiring (likely absent in v2 today)
```bash
rg -n "graphql-codegen|codegen" v2 ph -S | tee "$EVID_DIR/rg-codegen.txt"

# Reference-only: use as inspiration, do not edit
rg -n "graphql-codegen|codegen" modular-oss-saas -S | head -n 50 | tee "$EVID_DIR/rg-codegen-reference-only.txt" || true
```

## Edit the Decision Register entry
```bash
${EDITOR:-vi} ph/decision-register/DR-0006-harvester-publish-and-codegen-workflow.md
```

## Handbook Validation
```bash
ph validate
```

## Notes
- Keep evidence safe: publish reports must be sanitized; no tokens or `.env` contents in evidence.
