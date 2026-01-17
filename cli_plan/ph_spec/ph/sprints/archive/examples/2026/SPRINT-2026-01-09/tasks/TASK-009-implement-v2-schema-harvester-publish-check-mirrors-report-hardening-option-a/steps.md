---
title: Implement: v2 schema harvester publish/check + mirrors + report hardening (Option A) - Implementation Steps
type: implementation
date: 2026-01-10
task_id: TASK-009
tags: [implementation]
links: []
---

# Implementation Steps: Implement: v2 schema harvester publish/check + mirrors + report hardening (Option A)

## Overview
Implement the v2 schema harvester publish/check workflow (ADR-0032 Option A) with v2-level hardening:
- introspection-first SDL harvest (`_service.sdl`),
- Cosmo publish/check as a hard gate,
- atomic mirror updates only after success,
- deterministic, sanitized publish report artifacts,
- zero secret leakage in logs/evidence.

## Prerequisites
- [ ] `TASK-006` is `done` (Cosmo+MinIO baseline is implemented in v2; `cosmo-controlplane` reachable in-network)
- [ ] v2 stack can be started (`make -C v2 v2-up`) with non-default Keycloak admin creds
- [ ] Vault contract for Cosmo auth exists (`DR-0004`), including `/secrets/cosmo-cli.env` for harvester-only Cosmo access (do not mount into Router)
- [ ] Evidence will be captured under `project-handbook/status/evidence/TASK-009/<run-id>/` (no secrets)

## Step 1 — Confirm the contracts (already decided)
Read (canonical):
- `project-handbook/adr/0032-v2-harvester-publish-and-codegen-workflow.md`
- `project-handbook/decision-register/DR-0006-harvester-publish-and-codegen-workflow.md`
- `project-handbook/decision-register/DR-0004-vault-secrets-contract-cosmo-minio.md` (Cosmo CLI env addendum)
- `project-handbook/features/v2_schema-harvester-service/implementation/IMPLEMENTATION.md`
- Legacy reference (read-only): `modular-oss-saas/services/schema-harvester/`

Then record (verbatim) in your evidence index (`project-handbook/status/evidence/TASK-009/<run-id>/index.md`):
- Inventory file: `v2/infra/compose/graphql/subgraphs.yaml`
- Mirrors: `v2/infra/compose/graphql/subgraphs/*/schema.graphql` (atomic rename after success only)
- Canonical entrypoint: `make -C v2 v2-publish`
- Report path: `v2/.tmp/harvester/publish-report.json`
- WGC version: `wgc@0.63.0`
- Posture: never print `/secrets/*.env` contents; scan evidence for token patterns before review

## Step 2 — Ensure Cosmo CLI auth env exists (no leakage)
Target contract (from `DR-0004`):
- KV path: `kv/data/tribuence/v2/cosmo-cli`
- Rendered env file: `/secrets/cosmo-cli.env`
- Required keys:
  - `COSMO_API_KEY` (secret)
  - `COSMO_API_URL` (non-secret; inside-network URL: `http://cosmo-controlplane:3001`)
  - `COSMO_FEDERATED_GRAPH_NAME` (non-secret; `tribuence`)
  - `COSMO_FEDERATED_GRAPH_NAMESPACE` (non-secret; `dev`)

Implementation expectation:
- If `TASK-006` did not yet render `/secrets/cosmo-cli.env`, add the template + Vault Agent stanza as part of this task (harvester needs it).
- Validation must never `cat /secrets/cosmo-cli.env` or print its values; only assert presence/non-emptiness.

## Step 3 — Implement harvester (CLI-first; v2)
Implement a CLI-first harvester service under `v2/services/schema-harvester/` and wire a canonical entrypoint `make -C v2 v2-publish`.

Hard requirements:
- Inventory source: `v2/infra/compose/graphql/subgraphs.yaml` (stable order: sort by subgraph name)
- SDL acquisition (per subgraph):
  - default: introspect `_service { sdl }` against `routing_url`
    - query: `query { _service { sdl } }`
  - fallback: read the committed mirror file at `schema.file` only when introspection is unavailable/disabled
- Local composition preflight:
  - compose harvested SDLs with `@apollo/composition`
  - fail fast on composition errors (do not publish)
- Publish + check gate (Cosmo; hard stop on any failure):
  - publish: `npx -y wgc@0.63.0 subgraph publish <name> --schema <schemaFile> --routing-url <routingUrl> --namespace <namespace> --fail-on-composition-error --fail-on-admission-webhook-error`
  - check: `npx -y wgc@0.63.0 subgraph check <name> --schema <schemaFile> --namespace <namespace>`
  - namespace must come from `COSMO_FEDERATED_GRAPH_NAMESPACE` (do not hardcode)
- Report artifact:
  - always write `v2/.tmp/harvester/publish-report.json` (success *or* failure), deterministic + sanitized (see `features/v2_schema-harvester-service/implementation/IMPLEMENTATION.md`)
- Mirror updates:
  - only after *all* subgraphs pass publish+check
  - update `v2/infra/compose/graphql/subgraphs/*/schema.graphql` via temp file + atomic rename
  - never delete last-known-good mirrors on failure; never leave partial/empty files

## Step 4 — Prove hardening (no secrets, atomic writes)
Run the positive and negative validation procedures in `validation.md` and capture evidence proving:
- no secrets/tokens/JWTs appear in logs or report artifacts,
- mirrors do not change on any failure mode (publish failure, check failure, composition failure),
- mirror updates are atomic (no partial writes observed; temp file not left behind).

Capture evidence under `project-handbook/status/evidence/TASK-009/` as required by `validation.md`.

## Step 5 — Update docs and wire Make targets
Update (as needed):
- `v2/Makefile` to include a canonical publish/check target (e.g. `v2-publish`)
- `project-handbook/features/v2_schema-harvester-service/implementation/IMPLEMENTATION.md` if implementation details differ from the planned contract (keep it execution-ready)

## Notes
- Update status via `pnpm -C project-handbook make -- task-status ...`
- Commit changes in each repo you modify (`git -C v2 ...`, `git -C project-handbook ...`)
