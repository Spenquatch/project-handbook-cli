---
title: Implement: Router supergraph sync from Cosmo (Option B) - Completion Checklist
type: checklist
date: 2026-01-10
task_id: TASK-008
tags: [checklist]
links: []
---

# Completion Checklist: Implement: Router supergraph sync from Cosmo (Option B)

## Pre-Work
- [ ] Confirm `TASK-006` and `TASK-004` are `done`
- [ ] Read: `ph/adr/0031-v2-router-supergraph-delivery-cosmo-sync-artifact.md`
- [ ] Read: `ph/decision-register/DR-0005-router-supergraph-consumption-from-cosmo.md`
- [ ] Read: `ph/decision-register/DR-0004-vault-secrets-contract-cosmo-minio.md`
- [ ] Evidence run folder created: `ph/status/evidence/TASK-008/<run-id>/`

## During Execution
- [ ] `v2/infra/compose/docker-compose.v2.yml` includes `supergraph-sync` and a shared runtime-supergraph volume (RW for sync; RO for Router)
- [ ] Runtime supergraph contract matches task docs:
  - [ ] `router-supergraph-runtime-v2` is mounted at `/dist/graphql-runtime` (RW in `supergraph-sync`, RO in `apollo-router`)
  - [ ] Router reads `/dist/graphql-runtime/supergraph.graphql`
- [ ] Router consumes the runtime supergraph file (not the committed snapshot) and hot reload is enabled (`APOLLO_ROUTER_HOT_RELOAD=true` or `--hot-reload`)
- [ ] `supergraph-sync` writes atomically (temp + rename) and preserves last-known-good
- [ ] Vault renders Cosmo CLI creds into `/secrets/cosmo-cli.env` mounted only into `supergraph-sync` (Router never mounts Cosmo creds)
- [ ] No secret values printed in logs/evidence

## Before Review
- [ ] `V2_SMOKE_MODE=infra make -C v2 v2-smoke` passes (includes runtime supergraph assertions)
- [ ] Evidence captured under `ph/status/evidence/TASK-008/<run-id>/` (see `validation.md`)
- [ ] `ph validate` passes
- [ ] Set status to `review`: `ph task status --id TASK-008 --status review`

## After Completion
- [ ] PR reviewed and merged (or commit ready in sprint worktree)
- [ ] Update owning feature docs/changelog if needed
- [ ] Move status to `done`: `ph task status --id TASK-008 --status done`
