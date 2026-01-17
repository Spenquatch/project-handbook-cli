---
title: Task TASK-009 - Implement: v2 schema harvester publish/check + mirrors + report hardening (Option A)
type: task
date: 2026-01-10
task_id: TASK-009
feature: v2_schema-harvester-service
session: task-execution
tags: [task, v2_schema-harvester-service]
links: [../../../features/v2_schema-harvester-service/overview.md]
---

# Task TASK-009: Implement: v2 schema harvester publish/check + mirrors + report hardening (Option A)

## Overview
**Feature**: [v2_schema-harvester-service](../../../features/v2_schema-harvester-service/overview.md)
**Decision**: [ADR-0032](../../../../../adr/0032-v2-harvester-publish-and-codegen-workflow.md)
**Story Points**: 3
**Owner**: @spenser
**Lane**: registry/publish
**Session**: `task-execution`

## Implementation Contract (No Invention)
This task is `session=task-execution`: the key contracts are pre-decided and must be implemented exactly unless a new DR/ADR explicitly changes them.

### Inventory + mirror writepoints
- **Subgraph inventory**: `v2/infra/compose/graphql/subgraphs.yaml`
- **Mirror files**: `v2/infra/compose/graphql/subgraphs/*/schema.graphql`
- **Mirror semantics**: mirrors are for diff/debug only (Cosmo is authoritative).

### Cosmo + CLI posture
- **Cosmo CLI**: `wgc@0.63.0` (pinned)
- **Graph identity (matches legacy reference)**:
  - `COSMO_FEDERATED_GRAPH_NAME=tribuence`
  - `COSMO_FEDERATED_GRAPH_NAMESPACE=dev` (equivalent to `tribuence@dev`)
- **Control plane URL (inside the v2 network)**: `COSMO_API_URL=http://cosmo-controlplane:3001`
- **Credentials posture**: Cosmo credentials are Vault-rendered and mounted only into harvester/codegen helpers (never Router); do not print env contents.

### Harvester publish/check gate (canonical entrypoint)
- **Canonical command**: `make -C v2 v2-publish`
- **Gate behavior**:
  - any failure (introspection, local composition, publish, check) exits non-zero,
  - mirrors update only after *all* subgraphs pass publish+check,
  - mirror updates are atomic (temp → rename), and never delete last-known-good on failures.
- **Publish report artifact (required)**:
  - write deterministic, sanitized JSON at `v2/.tmp/harvester/publish-report.json`
  - stable keys + stable ordering; no timestamps; no secrets/tokens/JWTs; bounded error strings.

## Agent Navigation Rules
1. **Start work**: Update `task.yaml` status to "doing"
2. **Read first**: `steps.md` for implementation sequence
3. **Use commands**: Copy-paste from `commands.md`
4. **Validate progress**: Follow `validation.md` guidelines
5. **Check completion**: Use `checklist.md` before marking done
6. **Update status**: Set to "review" when ready for review

## Context & Background
This task implements the [ADR-0032](../../../../../adr/0032-v2-harvester-publish-and-codegen-workflow.md) decision for the [v2_schema-harvester-service] feature.

## No Ambiguity (Required)
- Legacy reference code under `modular-oss-saas/services/schema-harvester/` can be used as inspiration or selectively reused, but **v2 must meet the hardening/enhancements** in `ADR-0032` and `features/v2_schema-harvester-service/implementation/IMPLEMENTATION.md`.
- It is **not acceptable** to “port the legacy harvester as-is” if it omits: Cosmo-side check gating, deterministic sanitized reporting, and atomic mirror updates.

## Quick Start
```bash
# Claim task
pnpm -C project-handbook make -- task-status id=TASK-009 status=doing
cd project-handbook/sprints/current/tasks/TASK-009-*/

# Follow implementation
cat steps.md              # Read implementation steps
cat commands.md           # Copy-paste commands
cat validation.md         # Validation approach
```

## Dependencies
Review `task.yaml` for any `depends_on` tasks that must be completed first.

## Acceptance Criteria
See `task.yaml` acceptance section and `checklist.md` for completion requirements.
