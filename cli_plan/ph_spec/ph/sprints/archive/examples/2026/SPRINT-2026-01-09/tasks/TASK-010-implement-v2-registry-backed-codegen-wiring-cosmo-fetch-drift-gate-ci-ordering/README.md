---
title: Task TASK-010 - Implement: v2 registry-backed codegen wiring (Cosmo fetch + drift gate + CI ordering)
type: task
date: 2026-01-10
task_id: TASK-010
feature: v2_codegen-from-registry
session: task-execution
tags: [task, v2_codegen-from-registry]
links: [../../../features/v2_codegen-from-registry/overview.md]
---

# Task TASK-010: Implement: v2 registry-backed codegen wiring (Cosmo fetch + drift gate + CI ordering)

## Overview
**Feature**: [v2_codegen-from-registry](../../../features/v2_codegen-from-registry/overview.md)
**Decision**: [ADR-0032](../../../../../adr/0032-v2-harvester-publish-and-codegen-workflow.md)
**Story Points**: 3
**Owner**: @spenser
**Lane**: registry/publish
**Session**: `task-execution`

## Implementation Contract (No Invention)
This task is `session=task-execution`: the key contracts are pre-decided and must be implemented exactly unless a new DR/ADR explicitly changes them.

### Scope (fixed)
- **UI package**: `v2/apps/tribuence-mini`
- **Generated output**: `v2/apps/tribuence-mini/src/generated/` (committed)
- **Fetched schema file (runtime; not committed)**: `v2/.tmp/codegen/supergraph.graphql` (atomic write)

### Cosmo-backed schema authority
- **Cosmo CLI**: `wgc@0.63.0` (pinned)
- **Graph identity**:
  - `COSMO_FEDERATED_GRAPH_NAME=tribuence`
  - `COSMO_FEDERATED_GRAPH_NAMESPACE=dev`
- **Control plane URL (inside the v2 network)**: `COSMO_API_URL=http://cosmo-controlplane:3001`
- **Credentials posture**: Cosmo CLI credentials are Vault-rendered and mounted only into codegen helpers (never printed).

### Canonical ordering gate
CI must enforce this ordering (and local runs follow the same sequence):
1. `make -C v2 v2-publish` (TASK-009)
2. `make -C v2 v2-codegen-check`
3. `pnpm -C v2/apps/tribuence-mini typecheck`

## Agent Navigation Rules
1. **Start work**: Update `task.yaml` status to "doing"
2. **Read first**: `steps.md` for implementation sequence
3. **Use commands**: Copy-paste from `commands.md`
4. **Validate progress**: Follow `validation.md` guidelines
5. **Check completion**: Use `checklist.md` before marking done
6. **Update status**: Set to "review" when ready for review

## Context & Background
This task implements the [ADR-0032](../../../../../adr/0032-v2-harvester-publish-and-codegen-workflow.md) decision for the [v2_codegen-from-registry] feature.

## No Ambiguity (Required)
- Codegen must treat **Cosmo as the only schema authority**; local SDL mirrors are not valid codegen inputs.
- This task is blocked until `TASK-009` is done (publish/check gate exists). CI ordering must be explicit: publish/check → codegen → typecheck.
- Legacy references may be used, but v2 must meet the hardening/enhancements in `ADR-0032`.

## Quick Start
```bash
# Claim task
pnpm -C project-handbook make -- task-status id=TASK-010 status=doing
cd project-handbook/sprints/current/tasks/TASK-010-*/

# Follow implementation
cat steps.md              # Read implementation steps
cat commands.md           # Copy-paste commands
cat validation.md         # Validation approach
```

## Dependencies
Review `task.yaml` for any `depends_on` tasks that must be completed first.

## Acceptance Criteria
See `task.yaml` acceptance section and `checklist.md` for completion requirements.
