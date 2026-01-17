---
title: Implement: Router supergraph sync from Cosmo (Option B) - Validation Guide
type: validation
date: 2026-01-10
task_id: TASK-008
tags: [validation]
links: []
---

# Validation Guide: Implement: Router supergraph sync from Cosmo (Option B)

## Automated Validation
```bash
pnpm -C project-handbook make -- validate
pnpm -C project-handbook make -- sprint-status
V2_SMOKE_MODE=infra make -C v2 v2-smoke
```

## Manual Validation (Must Be Task-Specific)
Pass/fail checks required before `review`:

1. Compose wiring changed (no secret leakage):
   - `v2/infra/compose/docker-compose.v2.yml` contains:
     - a `supergraph-sync` service/job,
     - a shared named volume for the runtime supergraph artifact (RW for sync; RO for Router),
     - Router mounts the runtime supergraph file (not the committed snapshot) and runs with hot reload enabled.
   - `supergraph-sync` is the only service that mounts `/secrets/cosmo-cli.env`.
2. Runtime artifact behavior:
   - After `make -C v2 v2-up`, the runtime supergraph file exists in the Router container and is non-empty.
   - `supergraph-sync` writes updates atomically (temp + rename) and preserves last-known-good on failures.
   - A forced refresh (atomic replace with same contents) does not break Router health.
3. Secrets posture:
   - Cosmo CLI credentials are Vault-rendered and mounted only into `supergraph-sync` (Router never mounts them).
   - No logs/evidence contain secret values (no API keys, tokens, or env dumps).
4. Smoke probes:
   - `V2_SMOKE_MODE=infra make -C v2 v2-smoke` passes and includes assertions for the runtime supergraph file and Router health stability across refresh.
5. Evidence captured (minimum):
   - `project-handbook/status/evidence/TASK-008/<run-id>/index.md`
   - `project-handbook/status/evidence/TASK-008/<run-id>/rg-router-supergraph-wiring.txt`
    - `project-handbook/status/evidence/TASK-008/<run-id>/v2-up.txt`
    - `project-handbook/status/evidence/TASK-008/<run-id>/v2-smoke-infra.txt`
    - `project-handbook/status/evidence/TASK-008/<run-id>/runtime-supergraph-router-stats.txt`
    - `project-handbook/status/evidence/TASK-008/<run-id>/supergraph-sync-logs.txt`
    - `project-handbook/status/evidence/TASK-008/<run-id>/apollo-router-logs-after-refresh.txt`
    - `project-handbook/status/evidence/TASK-008/<run-id>/token-scan-hits.txt` (must not contain secret values)

## Sign-off
- [ ] All validation steps completed
- [ ] Evidence documented above
- [ ] Ready to mark task as "done"

## Reviewer Decision (2026-01-11)
Decision: **APPROVE**

Reproduced checks (repo root):
- `pnpm -C project-handbook make -- validate` → `0 error(s), 0 warning(s)`
- `V2_SMOKE_MODE=infra make -C v2 v2-smoke` → `Summary: pass=14 fail=0 skip=0` (includes runtime supergraph existence + forced refresh + Router liveness after refresh)

Spot checks:
- `v2/infra/compose/docker-compose.v2.yml` mounts `router-supergraph-runtime-v2` at `/dist/graphql-runtime` as `ro` in `apollo-router` and `rw` in `supergraph-sync`, and only `supergraph-sync` mounts `/secrets/cosmo-cli.env`.
- Container verification:
  - `apollo-router`: `APOLLO_ROUTER_SUPERGRAPH_PATH=/dist/graphql-runtime/supergraph.graphql`, `APOLLO_ROUTER_HOT_RELOAD=true`, and `/secrets/cosmo-cli.env` absent.
  - `supergraph-sync`: `/secrets/cosmo-cli.env` present.
