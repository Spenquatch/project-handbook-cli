---
title: Task TASK-002 - Investigate: Vault seeding + secrets contract for Cosmo/MinIO (no leakage)
type: task
date: 2026-01-09
task_id: TASK-002
feature: v2_registry-cosmo-minio-required
session: research-discovery
tags: [task, v2_registry-cosmo-minio-required]
links: [../../../features/v2_registry-cosmo-minio-required/overview.md]
---

# Task TASK-002: Investigate: Vault seeding + secrets contract for Cosmo/MinIO (no leakage)

## Overview
- **Feature**: [v2_registry-cosmo-minio-required](../../../features/v2_registry-cosmo-minio-required/overview.md)
- **Decision**: `DR-0004` (`project-handbook/decision-register/DR-0004-vault-secrets-contract-cosmo-minio.md`)
- **Story Points**: 3
- **Owner**: @spenser
- **Lane**: `registry/security`
- **Session**: `research-discovery`

## Goal
Define a concrete, “no leakage” Vault contract for the Cosmo + MinIO baseline:
- exact Vault KV paths and field names,
- which rendered `/secrets/*.env` files exist (and which service consumes which),
- bootstrap behavior (idempotent, never prints secrets),
- and an explicit posture checklist to prevent accidental secret capture in logs/evidence.

## Outputs (what must exist when done)
- `project-handbook/decision-register/DR-0004-vault-secrets-contract-cosmo-minio.md` fully filled (Option A/B, evidence, recommendation, approval request).
- `project-handbook/features/v2_registry-cosmo-minio-required/implementation/IMPLEMENTATION.md` updated with:
  - concrete KV keys and rendered env outputs,
  - a “no secrets printed” posture checklist,
  - exact v2 files that will change during implementation (templates + bootstrap script).
- Evidence captured under `project-handbook/status/evidence/TASK-002/` and referenced from `DR-0004`.

## Non-goals
- Do not run Vault bootstrap scripts or dump env files for this task; prefer repo inspection evidence.
- Do not implement Cosmo/MinIO in `v2/` during this task.

## Context & Background
ADR-0015 requires Vault-seeded secrets for Cosmo/MinIO, rendered via Vault Agent into `/secrets/*.env`, with a strict “no secrets printed” posture.

## Quick Start
```bash
pnpm -C project-handbook make -- task-status id=TASK-002 status=doing
cd project-handbook/sprints/current/tasks/TASK-002-*/

cat steps.md
cat commands.md
cat validation.md
```

## Dependencies
- `TASK-005` must be `done` first (evidence conventions).

## Acceptance Criteria
See `task.yaml` acceptance section and `checklist.md` for completion requirements.
