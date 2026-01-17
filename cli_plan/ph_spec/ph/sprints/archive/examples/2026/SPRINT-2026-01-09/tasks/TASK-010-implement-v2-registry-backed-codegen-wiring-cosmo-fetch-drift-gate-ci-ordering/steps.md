---
title: Implement: v2 registry-backed codegen wiring (Cosmo fetch + drift gate + CI ordering) - Implementation Steps
type: implementation
date: 2026-01-10
task_id: TASK-010
tags: [implementation]
links: []
---

# Implementation Steps: Implement: v2 registry-backed codegen wiring (Cosmo fetch + drift gate + CI ordering)

## Overview
Implement the canonical codegen wiring for v2 (ADR-0032 / ADR-0019):
- fetch schema inputs from Cosmo,
- run GraphQL Codegen deterministically,
- enforce drift in CI,
- ensure ordering: publish/check → codegen → typecheck.

## Prerequisites
- [ ] `TASK-009` is `done` (publish/check gate exists)
- [ ] `TASK-006` is `done` (Cosmo baseline is in v2)
- [ ] `/secrets/cosmo-cli.env` exists (Vault-rendered; do not print values)
- [ ] Scope is fixed for v0.5.0:
  - UI target: `v2/apps/tribuence-mini`
  - committed output: `v2/apps/tribuence-mini/src/generated/`
  - fetched schema file (runtime): `v2/.tmp/codegen/supergraph.graphql`

## Step 1 — Ground constraints (no local SDL authority)
Read:
- `ph/adr/0032-v2-harvester-publish-and-codegen-workflow.md`
- `ph/adr/0019-v2-codegen-from-registry.md`
- `ph/features/v2_codegen-from-registry/implementation/IMPLEMENTATION.md`

Hard rule: local mirrors are for diff/debug only. If schema fetch from Cosmo fails, codegen fails.

## Step 2 — Implement schema fetch helper (Cosmo → file)
Add a v2 script that:
- reads Cosmo CLI auth env from a Vault-rendered env file (`/secrets/cosmo-cli.env`),
- runs `npx -y wgc@0.63.0 federated-graph fetch-schema --namespace "$COSMO_FEDERATED_GRAPH_NAMESPACE" "$COSMO_FEDERATED_GRAPH_NAME" --out "$tmp"`,
- writes to `v2/.tmp/codegen/supergraph.graphql` using atomic writes (temp → rename in the same directory),
- never prints secret values.

## Step 3 — Implement GraphQL Codegen wiring (UI)
In `v2/apps/tribuence-mini/`:
- add codegen dependencies and config (`v2/apps/tribuence-mini/codegen.ts`)
- define scripts:
  - `codegen`: fetch schema from Cosmo → run GraphQL Codegen
  - `codegen:check`: run codegen and fail on git diff of generated outputs (drift gate)
- ensure generated outputs are committed and deterministic

## Step 4 — CI ordering gate
Wire CI to enforce the canonical ordering gate:
- `make -C v2 v2-publish` (TASK-009) first
- then `make -C v2 v2-codegen-check`
- then `pnpm -C v2/apps/tribuence-mini typecheck`

## Step 5 — Evidence + docs
Capture evidence under `ph/status/evidence/TASK-010/` proving:
- schema fetch comes from Cosmo,
- drift gate fails when generated output is not committed,
- CI ordering is enforced.

## Notes
- Update status via `ph task status --id TASK-010 --status <status>`
- Commit changes in each repo you modify (`git -C v2 ...`, `git -C <PH_ROOT> ...`)
