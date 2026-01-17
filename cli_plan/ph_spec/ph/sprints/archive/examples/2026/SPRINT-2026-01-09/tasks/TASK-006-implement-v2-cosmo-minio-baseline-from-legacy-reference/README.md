---
title: Task TASK-006 - Implement: v2 Cosmo+MinIO baseline (from legacy reference)
type: task
date: 2026-01-09
task_id: TASK-006
feature: v2_registry-cosmo-minio-required
session: task-execution
tags: [task, v2_registry-cosmo-minio-required]
links: [../../../../../features/v2_registry-cosmo-minio-required/overview.md]
---

# Task TASK-006: Implement: v2 Cosmo+MinIO baseline (from legacy reference)

## Overview
**Feature**: [v2_registry-cosmo-minio-required](../../../../../features/v2_registry-cosmo-minio-required/overview.md)  
**Decision**: [ADR-0030](../../../../../adr/0030-v2-cosmo-artifact-store-minio-baseline-then-seaweedfs.md)  
**Secrets Contract**: [FDR-0001](../../../../../features/v2_registry-cosmo-minio-required/fdr/0001-vault-secrets-contract-cosmo-minio.md)  
**Story Points**: 3
**Owner**: @spenser
**Lane**: registry/discovery
**Session**: `task-execution`

## Agent Navigation Rules
1. **Start work**: `ph task status --id TASK-006 --status doing`
2. **Read first**: `steps.md` for the exact sequence
3. **Use commands**: Copy-paste from `commands.md`
4. **Validate progress**: Follow `validation.md` guidelines
5. **Check completion**: Use `checklist.md` before marking done
6. **Update status**: `ph task status --id TASK-006 --status review`

## Context & Background
This task implements the **MinIO baseline** for Cosmo artifact storage per:
- [ADR-0030](../../../../../adr/0030-v2-cosmo-artifact-store-minio-baseline-then-seaweedfs.md): MinIO first, then SeaweedFS cutover.
- [DR-0003](../../../../../decision-register/DR-0003-cosmo-minio-baseline-topology.md): approved inventory + pinned images + internal-only posture.
- [FDR-0001](../../../../../features/v2_registry-cosmo-minio-required/fdr/0001-vault-secrets-contract-cosmo-minio.md): Vault KV paths + `/secrets/*.env` outputs, “no secrets printed”.

This is an execution task: it updates v2 wiring under `v2/` and updates handbook docs under `ph/`.

## Non-Negotiables (acceptance gates)
- **Internal-only**: no Traefik routers for Cosmo/MinIO; no host `ports:` in default v2 compose for Cosmo/MinIO.
- **No secret leakage**: do not print secret values; do not `cat /secrets/*.env`; do not dump `env`.
- **Store-agnostic**: bucket init uses a generic S3 client (prefer `amazon/aws-cli`), not `minio/mc`.
- **Reusable probe**: add a deterministic “Cosmo artifact write/read” smoke probe that will be reused in `TASK-007`.

## Quick Start
```bash
ph task status --id TASK-006 --status doing

cd ph/sprints/current/tasks/TASK-006-implement-v2-cosmo-minio-baseline-from-legacy-reference
cat steps.md
cat commands.md
cat validation.md
```

## Dependencies
- `TASK-002` must be `done` (secrets contract accepted and available as FDR-0001).
- `TASK-007` depends on this task; do not do SeaweedFS work here beyond keeping the integration store-agnostic and adding the reusable probe.

## Deliverables (what changes in the repo)
- `v2/infra/compose/docker-compose.v2.yml` includes Cosmo + MinIO + deps (internal-only posture).
- `v2/infra/vault/templates/*` includes new templates for Cosmo/MinIO and an `artifacts.env` single source of truth.
- `v2/scripts/vault/bootstrap-v2.sh` seeds Cosmo/MinIO KV paths per FDR-0001 (no leakage).
- `v2/scripts/v2-smoke.sh` includes:
  - additional isolation checks (Cosmo/MinIO forbidden via Traefik),
  - “Cosmo artifact write/read” probe (reused by `TASK-007`).
- Evidence captured under `ph/status/evidence/TASK-006/` (see `validation.md`).

## Acceptance Criteria
See `task.yaml` acceptance section and `checklist.md` for completion requirements.
