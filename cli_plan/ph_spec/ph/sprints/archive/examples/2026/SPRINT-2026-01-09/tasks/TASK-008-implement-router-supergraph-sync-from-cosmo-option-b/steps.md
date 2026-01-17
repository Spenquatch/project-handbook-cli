---
title: Implement: Router supergraph sync from Cosmo (Option B) - Implementation Steps
type: implementation
date: 2026-01-10
task_id: TASK-008
tags: [implementation]
links: []
---

# Implementation Steps: Implement: Router supergraph sync from Cosmo (Option B)

## Overview
Implement **ADR-0031 / DR-0005 Option B**:
- `supergraph-sync` fetches the latest valid federated-graph SDL from Cosmo and writes a runtime supergraph file.
- Apollo Router consumes the runtime supergraph file and hot-reloads on updates.

This is execution work under `v2/` plus handbook doc updates under `project-handbook/`.

## Prerequisites
- `TASK-006` is `done` (Cosmo baseline exists and is reachable from inside the v2 network).
- `TASK-004` is `done` (harvester publish workflow + artifact ownership contract is explicit).
- Local Docker works.
- You will capture evidence under `project-handbook/status/evidence/TASK-008/<run-id>/` (no secrets).

## Step 1 — Confirm the contracts (already decided)
Read (canonical):
- `project-handbook/adr/0031-v2-router-supergraph-delivery-cosmo-sync-artifact.md`
- `project-handbook/decision-register/DR-0005-router-supergraph-consumption-from-cosmo.md`
- `project-handbook/decision-register/DR-0004-vault-secrets-contract-cosmo-minio.md`
- `project-handbook/features/v2_schema-publishing-and-composition/implementation/IMPLEMENTATION.md`

Then record (verbatim) in your evidence index (`project-handbook/status/evidence/TASK-008/<run-id>/index.md`):
- Runtime supergraph directory: `/dist/graphql-runtime`
- Runtime supergraph file: `/dist/graphql-runtime/supergraph.graphql`
- Shared volume name: `router-supergraph-runtime-v2`
- Fetch mechanism (Apollo Router supergraph): `npx -y wgc@0.63.0 federated-graph fetch --apollo-compatibility --federation-version 2.6.0 -n dev tribuence` + `APOLLO_ELV2_LICENSE=accept npx -y @apollo/rover@0.37.0 supergraph compose ...`
- Poll interval: `SUPERGRAPH_SYNC_POLL_INTERVAL_SECONDS` default `30`
- Failure behavior:
  - never delete the last-known-good runtime supergraph file,
  - write temp file in the same directory then atomic rename,
  - Router never mounts Cosmo credentials; only `supergraph-sync` mounts `/secrets/cosmo-cli.env`.

## Step 2 — Implement `supergraph-sync` (Cosmo → runtime supergraph file)
In `v2/infra/compose/docker-compose.v2.yml`:
- Add a shared named volume for the runtime supergraph artifact (read-write for sync; read-only for Router): `router-supergraph-runtime-v2`.
- Add a `supergraph-sync` service/job that:
  - reads `COSMO_API_KEY` and `COSMO_API_URL` from a Vault-rendered env file (`/secrets/cosmo-cli.env`),
  - uses `COSMO_FEDERATED_GRAPH_NAME=tribuence` and `COSMO_FEDERATED_GRAPH_NAMESPACE=dev`,
  - fetches the latest federated-graph SDL from Cosmo,
  - writes to a temp file and atomically renames into place,
  - never deletes the last-known-good runtime supergraph on failure,
  - logs errors without printing secret values.

Implementation details to standardize:
- Use a pinned CLI mechanism for fetching: `npx -y wgc@0.63.0 ...`
- Make polling interval configurable via env (`SUPERGRAPH_SYNC_POLL_INTERVAL_SECONDS`, default `30`).
- Ensure file updates are atomic to avoid partial reads by Router.
- Add a healthcheck that fails until the runtime supergraph file exists and is non-empty (Router should depend on this).

## Step 3 — Switch Router to runtime supergraph + hot reload
In `v2/infra/compose/docker-compose.v2.yml` and related v2 wiring:
- Change Router supergraph source from the committed snapshot to the runtime supergraph artifact volume:
  - Router mounts `router-supergraph-runtime-v2` read-only at `/dist/graphql-runtime`
  - Router reads `/dist/graphql-runtime/supergraph.graphql`
- Enable Router local file hot reload:
  - set `APOLLO_ROUTER_HOT_RELOAD=true` (or pass `--hot-reload`)
  - set `APOLLO_ROUTER_SUPERGRAPH_PATH=/dist/graphql-runtime/supergraph.graphql`

Important: keep the committed snapshot for local/dev graph detection and debugging; do not delete it.

## Step 4 — Vault seeding + template wiring (no secret leakage)
Extend the v2 Vault patterns so `supergraph-sync` can authenticate:
- Add required KV key names and a Vault Agent template for a dedicated env file mounted only into `supergraph-sync`:
  - KV path: `kv/data/tribuence/v2/cosmo-cli`
  - required keys:
    - `COSMO_API_KEY` (secret)
    - `COSMO_API_URL` (non-secret; internal URL)
    - `COSMO_FEDERATED_GRAPH_NAME` (non-secret)
    - `COSMO_FEDERATED_GRAPH_NAMESPACE` (non-secret)
  - template output: `/secrets/cosmo-cli.env`
- Update `v2/scripts/vault/bootstrap-v2.sh` to support seeding the key names without printing values (idempotent; never echo secret values).
- Add/update v2 Vault template wiring:
  - add `v2/infra/vault/templates/cosmo-cli.env.tpl` (renders `/secrets/cosmo-cli.env`)
  - update `v2/infra/vault/templates/agent.hcl` to render the new template output
- Ensure `/secrets/cosmo-cli.env` is mounted only into `supergraph-sync` (Router must not mount it).

## Step 5 — Smoke probes + validation gates
Update `v2/scripts/v2-smoke.sh` so `V2_SMOKE_MODE=infra` can prove:
1. runtime supergraph file exists and is non-empty,
2. Router health is green after a supergraph refresh (at minimum: sync job writes a new file; Router remains healthy).

## Step 6 — Evidence + handbook validation
1. Capture evidence under `project-handbook/status/evidence/TASK-008/<run-id>/`:
   - relevant compose snippets (no env values),
   - sync job logs (redaction-safe),
   - smoke outputs.
2. Run `pnpm -C project-handbook make -- validate`.
3. Complete `checklist.md` and set task status to `review`.

## Notes
- Update task.yaml status as you progress through steps
- Document any blockers or decisions in daily status
- Link any PRs/commits back to this task
