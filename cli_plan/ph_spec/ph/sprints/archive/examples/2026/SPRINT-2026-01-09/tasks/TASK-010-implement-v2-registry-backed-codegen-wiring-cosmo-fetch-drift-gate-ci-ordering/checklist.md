---
title: Implement: v2 registry-backed codegen wiring (Cosmo fetch + drift gate + CI ordering) - Completion Checklist
type: checklist
date: 2026-01-10
task_id: TASK-010
tags: [checklist]
links: []
---

# Completion Checklist: Implement: v2 registry-backed codegen wiring (Cosmo fetch + drift gate + CI ordering)

## Pre-Work
- [ ] Confirm `TASK-009` and `TASK-006` are `done`
- [ ] Review `ADR-0032`, `ADR-0019`, and `features/v2_codegen-from-registry/implementation/IMPLEMENTATION.md`
- [ ] Confirm you understand the rule: Cosmo is authoritative; mirrors are not codegen inputs
- [ ] Confirm Vault renders `/secrets/cosmo-cli.env` (existence only; do not print values)

## During Execution
- [ ] Schema fetch helper writes `v2/.tmp/codegen/supergraph.graphql` atomically (temp → rename)
- [ ] Codegen uses `v2/.tmp/codegen/supergraph.graphql` as its schema input (no mirrors)
- [ ] GraphQL Codegen runs deterministically and outputs are committed under `v2/apps/tribuence-mini/src/generated/`
- [ ] Drift gate exists (`make -C v2 v2-codegen-check`) and fails on any diff under `v2/apps/tribuence-mini/src/generated/`
- [ ] Ordering gate exists and is explicit: `make -C v2 v2-publish` → `make -C v2 v2-codegen-check` → `pnpm -C v2/apps/tribuence-mini typecheck`
- [ ] Evidence captured under `ph/status/evidence/TASK-010/<run-id>/`

## Before Review
- [ ] Run `ph validate`
- [ ] Run `make -C v2 v2-codegen-check` and `pnpm -C v2/apps/tribuence-mini typecheck`
- [ ] Confirm no secret leakage in logs/evidence (explicit grep checks)
- [ ] Set status to `review` via `ph task status --id TASK-010 --status review`

## After Completion
- [ ] Peer review approved and merged
- [ ] Feature docs remain execution-ready (no placeholders or ambiguous steps introduced)
- [ ] Move status to `done` with `ph task status --id TASK-010 --status done`
