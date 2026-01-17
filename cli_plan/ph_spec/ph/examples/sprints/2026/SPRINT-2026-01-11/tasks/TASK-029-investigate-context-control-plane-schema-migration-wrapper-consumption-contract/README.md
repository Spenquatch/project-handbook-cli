---
title: Task TASK-029 - Investigate: Context control plane schema migration + wrapper consumption contract
type: task
date: 2026-01-11
task_id: TASK-029
feature: v2_context-control-plane-schema
session: research-discovery
tags: [task, v2_context-control-plane-schema]
links: [../../../../../features/v2_context-control-plane-schema/overview.md]
---

# Task TASK-029: Investigate: Context control plane schema migration + wrapper consumption contract

## Overview
- **Feature**: [v2_context-control-plane-schema](../../../../../features/v2_context-control-plane-schema/overview.md)
- **Decision**: `DR-0001` (create during this task)
- **Story Points**: 3
- **Owner**: @spenser
- **Lane**: `context/control-plane`
- **Session**: `research-discovery`

## Goal
Produce an operator-approvable DR (`DR-0001`) that defines the Context control-plane snapshot query shape and the wrapper/UI consumption contract, with an additive migration plan for the existing Context service.

## Outputs (what must exist when done)
- Create and complete `project-handbook/features/v2_context-control-plane-schema/decision-register/DR-0001-context-control-plane-migration-and-consumption-contract.md` (two viable options + evidence + explicit approval request; keep DR as `Proposed`).
- `project-handbook/features/v2_context-control-plane-schema/architecture/ARCHITECTURE.md` updated with snapshot query shape + federation/consumption patterns.
- `project-handbook/features/v2_context-control-plane-schema/implementation/IMPLEMENTATION.md` updated with an execution-ready migration plan (DB delta, rollout sequencing, invariants, validation approach).
- Evidence captured under `project-handbook/status/evidence/TASK-029/` and referenced from DR-0001.

## After operator approval (same research session)
- Promote the accepted decision to an FDR under `project-handbook/features/v2_context-control-plane-schema/fdr/` (likely `0001-*`) and create execution tasks that reference the FDR (not the DR).

## Non-goals
- Do not implement schema changes or migrations in `v2/` during this task.
- Do not expand provider secret handling; the decision must preserve “no provider secrets stored/returned”.

## Agent Navigation Rules
1. **Start work**: Update `task.yaml` status to "doing"
2. **Read first**: `steps.md` for implementation sequence
3. **Use commands**: Copy-paste from `commands.md`
4. **Validate progress**: Follow `validation.md` guidelines
5. **Check completion**: Use `checklist.md` before marking done
6. **Update status**: Set to "review" when ready for review

## Context & Background
This task completes the feature-local `DR-0001` for the [v2_context-control-plane-schema] feature.

## Quick Start
```bash
pnpm -C project-handbook make -- task-status id=TASK-029 status=doing
cd project-handbook/sprints/current/tasks/TASK-029-*/
cat steps.md
cat commands.md
cat validation.md
```

## Dependencies
Review `task.yaml` for any `depends_on` tasks that must be completed first.

## Acceptance Criteria
See `task.yaml` acceptance section and `checklist.md` for completion requirements.
