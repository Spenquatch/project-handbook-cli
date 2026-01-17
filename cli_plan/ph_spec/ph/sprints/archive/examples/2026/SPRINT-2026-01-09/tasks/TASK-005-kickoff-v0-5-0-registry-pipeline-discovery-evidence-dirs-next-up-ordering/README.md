---
title: Task TASK-005 - Kickoff: v0.5.0 registry pipeline discovery (evidence dirs + next-up ordering)
type: task
date: 2026-01-09
task_id: TASK-005
feature: v2_registry-cosmo-minio-required
session: task-execution
tags: [task, v2_registry-cosmo-minio-required]
links: [../../../features/v2_registry-cosmo-minio-required/overview.md]
---

# Task TASK-005: Kickoff: v0.5.0 registry pipeline discovery (evidence dirs + next-up ordering)

## Overview
- **Feature**: [v2_registry-cosmo-minio-required](../../../features/v2_registry-cosmo-minio-required/overview.md)
- **Decision**: [ADR-0015](../../../../../adr/0015-tribuence-mini-v2-cosmo-minio-and-schema-publishing.md)
- **Story Points**: 1
- **Owner**: @spenser
- **Lane**: `registry/kickoff`
- **Session**: `task-execution`

## Goal
Make the sprint “registry pipeline discovery” tasks executable with no ambiguity by:
- ensuring the dependency graph makes `TASK-005` “Next up”, and
- defining **evidence directory conventions** that `TASK-001`..`TASK-004` will follow.

## Deliverables (this task’s outputs)
- `ph/status/evidence/TASK-005/README.md` describes:
  - what artefacts each research task must capture under `ph/status/evidence/TASK-00X/`,
  - filename conventions, and
  - “no secrets in evidence” rules.
- `ph sprint status` selects `TASK-005` as “Next up”.

## Non-goals
- No `v2/` implementation changes.
- No Cosmo/MinIO bring-up (this is planning/handbook wiring only).

## Dependencies
- This task is the sprint starter (`depends_on: [FIRST_TASK]` in `task.yaml`).
- `TASK-001`..`TASK-004` depend on this task.

## Agent Navigation Rules (execution)
1. Claim task: `ph task status --id TASK-005 --status doing`
2. Follow `steps.md` in order; copy/paste from `commands.md`
3. Record evidence under `ph/status/evidence/TASK-005/`
4. Run `validation.md`, then complete `checklist.md`
5. Set `review` when ready for review; `done` after approval

## Quick Start
```bash
# Claim task + enter directory
ph task status --id TASK-005 --status doing
cd ph/sprints/current/tasks/TASK-005-*/

# Then follow:
cat steps.md
cat commands.md
cat validation.md
```

## Acceptance Criteria
See `task.yaml` acceptance section and `checklist.md` for completion requirements.
