---
title: Task TASK-008 - Implement: Router supergraph sync from Cosmo (Option B)
type: task
date: 2026-01-10
task_id: TASK-008
feature: v2_schema-publishing-and-composition
session: task-execution
tags: [task, v2_schema-publishing-and-composition]
links: [../../../../../features/v2_schema-publishing-and-composition/overview.md]
---

# Task TASK-008: Implement: Router supergraph sync from Cosmo (Option B)

## Overview
**Feature**: [v2_schema-publishing-and-composition](../../../../../features/v2_schema-publishing-and-composition/overview.md)
**Decision**: [ADR-0031](../../../../../adr/0031-v2-router-supergraph-delivery-cosmo-sync-artifact.md)
**Story Points**: 3
**Owner**: @spenser
**Lane**: registry/router
**Session**: `task-execution`

## Implementation Contract (No Invention)
This task is `session=task-execution`: the key contracts are pre-decided and must be implemented exactly unless a new DR/ADR explicitly changes them.

### Runtime supergraph artifact
- **Runtime supergraph directory (inside containers)**: `/dist/graphql-runtime`
- **Runtime supergraph file (inside containers)**: `/dist/graphql-runtime/supergraph.graphql`
- **Shared volume name (compose)**: `router-supergraph-runtime-v2`
- **Update semantics**: write temp file in the same directory → atomic rename into place → never delete the last-known-good runtime supergraph file.

### Supergraph sync mechanism (Cosmo → file)
- **Cosmo CLI**: `wgc@0.63.0` (pinned)
- **Graph identity (matches legacy reference)**:
  - `COSMO_FEDERATED_GRAPH_NAME=tribuence`
  - `COSMO_FEDERATED_GRAPH_NAMESPACE=dev` (equivalent to `tribuence@dev`)
- **Control plane URL (inside the v2 network)**: `COSMO_API_URL=http://cosmo-controlplane:3001`
- **Poll interval env**: `SUPERGRAPH_SYNC_POLL_INTERVAL_SECONDS` (default `30`)
- **Credentials posture**: `COSMO_API_KEY` is Vault-rendered and mounted only into `supergraph-sync` (Router never mounts Cosmo creds).
- **Apollo Router compatibility**: `wgc federated-graph fetch-schema` returns the composed API schema (not a federation supergraph). To produce an Apollo Router-compatible supergraph, `supergraph-sync` uses `wgc federated-graph fetch --apollo-compatibility` and then runs `rover supergraph compose` to generate a federation supergraph SDL.

## Agent Navigation Rules
1. **Start work**: `pnpm -C project-handbook make -- task-status id=TASK-008 status=doing`
2. **Read first**: `steps.md` for implementation sequence
3. **Use commands**: Copy-paste from `commands.md`
4. **Validate progress**: Follow `validation.md` guidelines
5. **Check completion**: Use `checklist.md` before marking done
6. **Update status**: `pnpm -C project-handbook make -- task-status id=TASK-008 status=review`

## Context & Background
This task implements **ADR-0031** (accepted from `DR-0005`): Router consumes a Cosmo-produced supergraph via a **local runtime artifact file** that is kept up-to-date by a Harvester-owned “supergraph sync” helper.

Key posture constraints:
- Deterministic local/dev behavior (file-based supergraph, hashable, debuggable).
- No Router access to Cosmo credentials (Vault-rendered secrets only mounted into the sync helper).
- Safe refresh semantics (atomic file updates; preserve last-known-good).

## Quick Start
```bash
pnpm -C project-handbook make -- task-status id=TASK-008 status=doing
cd project-handbook/sprints/current/tasks/TASK-008-implement-router-supergraph-sync-from-cosmo-option-b/

# Follow implementation
cat steps.md              # Read implementation steps
cat commands.md           # Copy-paste commands
cat validation.md         # Validation approach
```

## Dependencies
- `TASK-006` (Cosmo+MinIO baseline up and healthy)
- `TASK-004` (harvester publish workflow contract + alignment for artifact paths/ownership)

## Acceptance Criteria
See `task.yaml` acceptance section and `checklist.md` for completion requirements.
