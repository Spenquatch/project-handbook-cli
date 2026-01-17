---
title: Task TASK-004 - Investigate: Harvester publish workflow (SDL sources, mirror updates, report contract) + codegen wiring
type: task
date: 2026-01-09
task_id: TASK-004
feature: v2_schema-harvester-service
session: research-discovery
tags: [task, v2_schema-harvester-service]
links:
  - ../../../../../features/v2_schema-harvester-service/overview.md
  - ../../../../../features/v2_codegen-from-registry/overview.md
---

# Task TASK-004: Investigate: Harvester publish workflow (SDL sources, mirror updates, report contract) + codegen wiring

## Overview
- **Feature(s)**:
  - [v2_schema-harvester-service](../../../../../features/v2_schema-harvester-service/overview.md)
  - [v2_codegen-from-registry](../../../../../features/v2_codegen-from-registry/overview.md)
- **Decision**: `DR-0006` (`project-handbook/decision-register/DR-0006-harvester-publish-and-codegen-workflow.md`)
- **Story Points**: 3
- **Owner**: @spenser
- **Lane**: `registry/publish`
- **Session**: `research-discovery`

## Goal
Decide and document the canonical publish/check workflow (harvester) and how codegen depends on it:
- SDL source-of-truth per subgraph (introspection vs repo contract SDL vs hybrid),
- mirror update rules (atomic writes; only after successful publish/check),
- publish report contract (deterministic, safe to store as evidence),
- codegen wiring (local + CI) that pulls from Cosmo and fails fast when publish/check is not satisfied.

## Outputs (what must exist when done)
- `project-handbook/decision-register/DR-0006-harvester-publish-and-codegen-workflow.md` fully filled (Option A/B, evidence, recommendation, approval request).
- `project-handbook/features/v2_schema-harvester-service/implementation/IMPLEMENTATION.md` updated with an execution-ready plan:
  - publish/check sequencing,
  - mirror write points and atomicity rules,
  - report contract and sanitization posture.
- `project-handbook/features/v2_codegen-from-registry/implementation/IMPLEMENTATION.md` updated with canonical codegen wiring (local + CI) and its dependency on publish/check.
- Evidence captured under `project-handbook/status/evidence/TASK-004/` and referenced from `DR-0006`.

## Non-goals
- Do not implement the harvester or codegen during this task; define an execution-ready plan only.

## Context & Background
ADR-0021 defines the harvester responsibility (publish + mirror). ADR-0019 defines that codegen pulls schemas from Cosmo. This task turns those requirements into an explicit workflow and report contract.

## Quick Start
```bash
pnpm -C project-handbook make -- task-status id=TASK-004 status=doing
cd project-handbook/sprints/current/tasks/TASK-004-*/

cat steps.md
cat commands.md
cat validation.md
```

## Dependencies
- `TASK-005` must be `done` first (evidence conventions).
- Integration dependency: if `DR-0006` Option B produces a local supergraph artifact (for Router consumption), the artifact contract (path/format/update rules + freshness guarantees) must be compatible with `DR-0005` (from `TASK-003`).

## Acceptance Criteria
See `task.yaml` acceptance section and `checklist.md` for completion requirements.
