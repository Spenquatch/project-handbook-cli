---
title: Investigate: Cosmo+MinIO baseline wiring strategy (topology, versions, posture) - Commands
type: commands
date: 2026-01-09
task_id: TASK-001
tags: [commands]
links: []
---

# Commands: Investigate: Cosmo+MinIO baseline wiring strategy (topology, versions, posture)

## Task Status
```bash
ph task status --id TASK-001 --status doing
ph task status --id TASK-001 --status review
ph task status --id TASK-001 --status done
```

## Evidence Directory (required)
```bash
EVID_DIR="ph/status/evidence/TASK-001"
mkdir -p "$EVID_DIR"
${EDITOR:-vi} "$EVID_DIR/index.md"
```

## Read Context (copy/paste into evidence if helpful)
```bash
sed -n '1,220p' ph/adr/0015-tribuence-mini-v2-cosmo-minio-and-schema-publishing.md | tee "$EVID_DIR/adr-0015.txt"
sed -n '1,260p' ph/decision-register/DR-0003-cosmo-minio-baseline-topology.md | tee "$EVID_DIR/dr-0003-start.txt"
```

## Inventory Current v2 Patterns (compose + Vault)
```bash
sed -n '1,260p' v2/infra/compose/docker-compose.v2.yml | tee "$EVID_DIR/v2-compose-head.txt"
find v2/infra/compose/traefik -type f -maxdepth 2 -print | tee "$EVID_DIR/v2-traefik-config-files.txt"
find v2/infra/vault/templates -type f -maxdepth 1 -print | tee "$EVID_DIR/v2-vault-templates-files.txt"
rg -n "kv/data/tribuence/v2" v2/scripts/vault/bootstrap-v2.sh v2/infra/vault/templates -S | tee "$EVID_DIR/v2-vault-kv-layout.txt"
```

## Search for existing Cosmo/MinIO mentions (expected: none yet)
```bash
rg -n "cosmo|minio" v2 ph -S | tee "$EVID_DIR/rg-cosmo-minio.txt"
```

## Handbook Validation
```bash
ph validate
```

## Notes
- Do not run `make -C v2 v2-up` or any Cosmo/MinIO bring-up commands as part of this task.
- Do not capture secrets in evidence (no `.env` dumps; no tokens).
