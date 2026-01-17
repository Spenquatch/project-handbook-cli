---
title: Investigate: Vault seeding + secrets contract for Cosmo/MinIO (no leakage) - Completion Checklist
type: checklist
date: 2026-01-09
task_id: TASK-002
tags: [checklist]
links: []
---

# Completion Checklist: Investigate: Vault seeding + secrets contract for Cosmo/MinIO (no leakage)

## Completion Criteria (matches `task.yaml`)
- [x] `ph/decision-register/DR-0004-vault-secrets-contract-cosmo-minio.md`:
  - [x] includes exactly two viable options (A/B) with pros/cons/implications/risks/unlocks/quick wins
  - [x] includes a recommendation and rationale
  - [x] ends with an explicit operator/user approval request
  - [x] remains `Status: Proposed` pending approval
- [x] `ph/features/v2_registry-cosmo-minio-required/implementation/IMPLEMENTATION.md` updated with:
  - [x] concrete KV paths + keys for Cosmo/MinIO (names only)
  - [x] template outputs: explicit `/secrets/*.env` files and consumers
  - [x] a “no secrets printed” posture checklist
- [x] Evidence exists under `ph/status/evidence/TASK-002/` and is referenced from DR-0004
- [x] `ph validate` passes
