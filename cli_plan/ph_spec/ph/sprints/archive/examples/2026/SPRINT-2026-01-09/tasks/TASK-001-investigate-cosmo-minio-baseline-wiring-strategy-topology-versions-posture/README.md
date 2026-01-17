---
title: Task TASK-001 - Investigate: Cosmo+MinIO baseline wiring strategy (topology, versions, posture)
type: task
date: 2026-01-09
task_id: TASK-001
feature: v2_registry-cosmo-minio-required
session: research-discovery
tags: [task, v2_registry-cosmo-minio-required]
links: [../../../features/v2_registry-cosmo-minio-required/overview.md]
---

# Task TASK-001: Investigate: Cosmo+MinIO baseline wiring strategy (topology, versions, posture)

## Overview
- **Feature**: [v2_registry-cosmo-minio-required](../../../features/v2_registry-cosmo-minio-required/overview.md)
- **Decision**: `DR-0003` (`ph/decision-register/DR-0003-cosmo-minio-baseline-topology.md`)
- **Story Points**: 3
- **Owner**: @spenser
- **Lane**: `registry/discovery`
- **Session**: `research-discovery`

## Goal
Produce an operator-approvable Decision Register entry (`DR-0003`) that answers:
- which Cosmo + MinIO topology we run in the default v2 stack,
- which image versions we pin (and why),
- which exposure posture we enforce (choose exactly one: strict internal-only with no host binds, or internal-only with localhost-only operator binds),
- and how this wires into v2 (compose, Vault, networks, data persistence).

## Outputs (what must exist when done)
- `ph/decision-register/DR-0003-cosmo-minio-baseline-topology.md` fully filled (exactly Option A + Option B, evidence, recommendation, approval request).
- `ph/features/v2_registry-cosmo-minio-required/architecture/ARCHITECTURE.md` updated with:
  - the recommended Cosmo inventory (services + image tags + dependencies),
  - the MinIO inventory, and
  - internal-only exposure posture (Traefik exclusion; explicitly state whether host binds are forbidden (Option A) or allowed on `127.0.0.1` only (Option B)).
- `ph/features/v2_registry-cosmo-minio-required/implementation/IMPLEMENTATION.md` updated with an execution-ready plan:
  - exact v2 wiring points (files to edit),
  - required env/secrets and Vault KV layout (referencing `TASK-002`/`DR-0004` where appropriate),
  - bucket init approach + smoke probes to enforce posture.
- Evidence captured under `ph/status/evidence/TASK-001/` and referenced from `DR-0003`.

## Non-goals
- Do not implement Cosmo/MinIO in `v2/` during this task.
- Do not run service bring-up commands as part of “research”; prefer repo inspection evidence.

## Context & Background
ADR-0015 requires Cosmo + MinIO to be part of the default v2 stack. This task makes that requirement execution-ready by deciding the concrete topology and posture.

## Quick Start
```bash
# Claim task and enter directory
ph task status --id TASK-001 --status doing
cd ph/sprints/current/tasks/TASK-001-*/

# Follow the task docs
cat steps.md
cat commands.md
cat validation.md
```

## Dependencies
- `TASK-005` must be `done` first (it defines evidence conventions and locks “next up” ordering).

## Acceptance Criteria
See `task.yaml` acceptance section and `checklist.md` for completion requirements.
