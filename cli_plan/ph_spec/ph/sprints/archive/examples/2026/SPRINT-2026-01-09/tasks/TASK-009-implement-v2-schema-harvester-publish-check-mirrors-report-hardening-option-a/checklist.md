---
title: Implement: v2 schema harvester publish/check + mirrors + report hardening (Option A) - Completion Checklist
type: checklist
date: 2026-01-10
task_id: TASK-009
tags: [checklist]
links: []
---

# Completion Checklist: Implement: v2 schema harvester publish/check + mirrors + report hardening (Option A)

## Pre-Work
- [ ] Confirm `TASK-006` is `done` (`task.yaml depends_on`)
- [ ] Review `ADR-0032`, `DR-0006`, and `features/v2_schema-harvester-service/implementation/IMPLEMENTATION.md`
- [ ] Confirm you understand the rule: legacy harvester is reference-only; v2 hardening is mandatory
- [ ] Confirm Vault renders `/secrets/cosmo-cli.env` (existence only; do not print values)

## During Execution
- [ ] `v2/services/schema-harvester/` exists with a CLI-first entrypoint
- [ ] Harvester reads `v2/infra/compose/graphql/subgraphs.yaml` and processes subgraphs in stable (sorted) order
- [ ] SDL acquisition is introspection-first (`query { _service { sdl } }`), with fallback to `schema.file` only when introspection is unavailable/disabled
- [ ] Local composition preflight fails fast on composition errors (no publish/check on failure)
- [ ] Cosmo publish/check is a hard gate and fails fast on any subgraph failure
- [ ] Mirrors update only after full success and via atomic writes (temp → rename); last-known-good mirrors preserved on failure
- [ ] Deterministic sanitized publish report exists at `v2/.tmp/harvester/publish-report.json` (no secrets/tokens/JWTs; bounded error strings)
- [ ] Evidence captured under `project-handbook/status/evidence/TASK-009/<run-id>/` (index + logs + mirror hashes + report hashes)

## Before Review
- [ ] Run `pnpm -C project-handbook make -- validate`
- [ ] Run `make -C v2 v2-smoke` (and any harvester-specific tests added)
- [ ] Confirm no secret leakage in logs/reports/evidence (explicit grep checks)
- [ ] Set status to `review` via `pnpm -C project-handbook make -- task-status id=TASK-009 status=review`

## After Completion
- [ ] Peer review approved and merged
- [ ] Feature docs remain execution-ready (no placeholders or ambiguous steps introduced)
- [ ] Move status to `done` with `pnpm -C project-handbook make -- task-status id=TASK-009 status=done`
