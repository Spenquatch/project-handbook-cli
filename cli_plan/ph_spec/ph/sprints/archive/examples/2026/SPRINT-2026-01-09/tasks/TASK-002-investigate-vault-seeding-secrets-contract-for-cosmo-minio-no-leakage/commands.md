---
title: Investigate: Vault seeding + secrets contract for Cosmo/MinIO (no leakage) - Commands
type: commands
date: 2026-01-09
task_id: TASK-002
tags: [commands]
links: []
---

# Commands: Investigate: Vault seeding + secrets contract for Cosmo/MinIO (no leakage)

## Task Status
```bash
pnpm -C project-handbook make -- task-status id=TASK-002 status=doing
pnpm -C project-handbook make -- task-status id=TASK-002 status=review
pnpm -C project-handbook make -- task-status id=TASK-002 status=done
```

## Evidence Directory (required)
```bash
EVID_DIR="project-handbook/status/evidence/TASK-002"
mkdir -p "$EVID_DIR"
${EDITOR:-vi} "$EVID_DIR/index.md"
```

## Inventory current v2 Vault contract (read-only; do not run bootstrap)
```bash
sed -n '1,240p' v2/infra/vault/templates/agent.hcl | tee "$EVID_DIR/vault-agent.hcl.txt"
find v2/infra/vault/templates -maxdepth 1 -type f -print | tee "$EVID_DIR/v2-vault-templates-inventory.txt"
rg -n "kv/data/tribuence/v2" v2/scripts/vault/bootstrap-v2.sh v2/infra/vault/templates -S | tee "$EVID_DIR/v2-vault-kv-layout.txt"

# Curate the “no leakage” mechanics (snippets only; do not capture full payloads)
rg -n "value not printed|never print|sanitize|placeholder|warn" v2/scripts/vault/bootstrap-v2.sh -S | tee "$EVID_DIR/v2-vault-bootstrap-no-leakage-snippets.txt"
```

## Edit the Decision Register entry
```bash
${EDITOR:-vi} project-handbook/decision-register/DR-0004-vault-secrets-contract-cosmo-minio.md
```

## Handbook Validation
```bash
pnpm -C project-handbook make -- validate
```

## Notes
- This task is contract definition. Avoid any command that might print or materialize secrets (`env`, `/secrets/*.env`, Vault API reads/writes).
