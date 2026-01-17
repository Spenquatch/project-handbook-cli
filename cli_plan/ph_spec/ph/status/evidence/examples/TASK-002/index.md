---
title: TASK-002 Evidence — Vault Seeding + Secrets Contract (Cosmo/MinIO)
type: evidence
date: 2026-01-10
task_id: TASK-002
tags: [evidence, task, vault, cosmo, minio, security]
links:
  - ../../../decision-register/DR-0004-vault-secrets-contract-cosmo-minio.md
  - ../../../../v2/scripts/vault/bootstrap-v2.sh
  - ../../../../v2/infra/vault/templates/agent.hcl
---

# Evidence index — TASK-002

This directory captures repo-inspection evidence used to complete `DR-0004` without materializing or printing any secret values.

## Table of contents
- v2 baseline Vault contract (current state)
  - `project-handbook/status/evidence/TASK-002/v2-vault-templates-inventory.txt`
  - `project-handbook/status/evidence/TASK-002/vault-agent.hcl.txt`
  - `project-handbook/status/evidence/TASK-002/v2-vault-kv-layout.txt`
  - `project-handbook/status/evidence/TASK-002/v2-vault-bootstrap-no-leakage-snippets.txt`
- Legacy/reference wiring (variable names only; no values)
  - `project-handbook/status/evidence/TASK-002/modular-compose-cosmo-minio-env-snippets.txt`

## What each file proves

### v2 baseline Vault contract
- `project-handbook/status/evidence/TASK-002/v2-vault-templates-inventory.txt`
  - Which Vault Agent templates already exist in `v2/infra/vault/templates/`.
- `project-handbook/status/evidence/TASK-002/vault-agent.hcl.txt`
  - Which `/secrets/*.env` files the v2 Vault Agent currently renders.
- `project-handbook/status/evidence/TASK-002/v2-vault-kv-layout.txt`
  - The existing KV layout under `kv/data/tribuence/v2/*` and the current template ↔ KV linkages (paths + key names only).
- `project-handbook/status/evidence/TASK-002/v2-vault-bootstrap-no-leakage-snippets.txt`
  - The existing “no leakage” mechanisms in `v2/scripts/vault/bootstrap-v2.sh` (sanitize/placeholder handling and “value not printed” messaging).

### Legacy/reference wiring
- `project-handbook/status/evidence/TASK-002/modular-compose-cosmo-minio-env-snippets.txt`
  - Which env var names the legacy/reference Cosmo+MinIO compose wiring expects (used only to inform key naming in the contract; values are not present).
