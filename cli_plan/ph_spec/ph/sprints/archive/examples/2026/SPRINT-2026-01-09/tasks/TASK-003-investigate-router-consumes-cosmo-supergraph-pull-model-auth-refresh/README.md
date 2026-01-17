---
title: Task TASK-003 - Investigate: Router consumes Cosmo supergraph (pull model + auth + refresh)
type: task
date: 2026-01-09
task_id: TASK-003
feature: v2_schema-publishing-and-composition
session: research-discovery
tags: [task, v2_schema-publishing-and-composition]
links: [../../../features/v2_schema-publishing-and-composition/overview.md]
---

# Task TASK-003: Investigate: Router consumes Cosmo supergraph (pull model + auth + refresh)

## Overview
- **Feature**: [v2_schema-publishing-and-composition](../../../features/v2_schema-publishing-and-composition/overview.md)
- **Decision**: `DR-0005` (`ph/decision-register/DR-0005-router-supergraph-consumption-from-cosmo.md`)
- **Story Points**: 3
- **Owner**: @spenser
- **Lane**: `registry/router`
- **Session**: `research-discovery`

## Goal
Decide and document how Apollo Router consumes a **Cosmo-produced supergraph** in v2:
- pull model (direct vs via local artifact),
- auth material + where it lives (Vault-rendered),
- refresh model (polling/signal/restart),
- and the exact v2 config files that will change.

## Outputs (what must exist when done)
- `ph/decision-register/DR-0005-router-supergraph-consumption-from-cosmo.md` fully filled (Option A/B, evidence, recommendation, approval request).
- `ph/features/v2_schema-publishing-and-composition/implementation/IMPLEMENTATION.md` updated with an execution-ready Router plan:
  - auth material requirements,
  - refresh model,
  - exact v2 config files to change (compose, router config, Vault templates).
- Evidence captured under `ph/status/evidence/TASK-003/` and referenced from `DR-0005`.

## Non-goals
- Do not modify `v2/` Router configuration during this task.
- Do not attempt to run Cosmo or fetch a live supergraph in this task; prefer repo inspection + documented APIs.

## Context & Background
ADR-0015 requires Router to serve a Cosmo-produced supergraph. Today v2 uses a local supergraph file; this task decides the registry-backed consumption model.

## Quick Start
```bash
ph task status --id TASK-003 --status doing
cd ph/sprints/current/tasks/TASK-003-*/

cat steps.md
cat commands.md
cat validation.md
```

## Dependencies
- `TASK-005` must be `done` first (evidence conventions).
- Integration dependency: `DR-0005` must align with `DR-0006` (from `TASK-004`) if Router consumes a local artifact (Option B). Do not finalize the `DR-0005` recommendation until the `DR-0006` artifact contract (path/format/update rules) is explicit.

## Acceptance Criteria
See `task.yaml` acceptance section and `checklist.md` for completion requirements.
