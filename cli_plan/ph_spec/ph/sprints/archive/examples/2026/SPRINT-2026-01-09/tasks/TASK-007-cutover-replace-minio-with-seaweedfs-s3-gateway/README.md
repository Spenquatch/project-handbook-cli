---
title: Task TASK-007 - Cutover: Replace MinIO with SeaweedFS S3 gateway
type: task
date: 2026-01-09
task_id: TASK-007
feature: v2_registry-cosmo-minio-required
session: task-execution
tags: [task, v2_registry-cosmo-minio-required]
links: [../../../../../features/v2_registry-cosmo-minio-required/overview.md]
---

# Task TASK-007: Cutover: Replace MinIO with SeaweedFS S3 gateway

## Overview
**Feature**: [v2_registry-cosmo-minio-required](../../../../../features/v2_registry-cosmo-minio-required/overview.md)  
**Decision**: [ADR-0030](../../../../../adr/0030-v2-cosmo-artifact-store-minio-baseline-then-seaweedfs.md)  
**SeaweedFS inventory/pin reference**: [DR-0003](../../../../../decision-register/DR-0003-cosmo-minio-baseline-topology.md)  
**Story Points**: 3
**Owner**: @spenser
**Lane**: registry/discovery
**Session**: `task-execution`

## Agent Navigation Rules
1. **Start work**: `pnpm -C project-handbook make -- task-status id=TASK-007 status=doing`
2. **Read first**: `steps.md` for the exact sequence
3. **Use commands**: Copy-paste from `commands.md`
4. **Validate progress**: Follow `validation.md` guidelines
5. **Check completion**: Use `checklist.md` before marking done
6. **Update status**: `pnpm -C project-handbook make -- task-status id=TASK-007 status=review`

## Context & Background
This task performs the **SeaweedFS S3 gateway cutover** immediately after the MinIO baseline (`TASK-006`) is green, per:
- [ADR-0030](../../../../../adr/0030-v2-cosmo-artifact-store-minio-baseline-then-seaweedfs.md): cutover is gated by a deterministic probe.
- [DR-0003](../../../../../decision-register/DR-0003-cosmo-minio-baseline-topology.md): SeaweedFS pin (`chrislusf/seaweedfs:4.05`) and internal-only posture.

Non-negotiables:
- SeaweedFS must be **internal-only** (no Traefik routers; no host `ports:`).
- Cutover must be measurable: the existing “Cosmo artifact write/read” smoke probe must pass against SeaweedFS.
- After cutover, MinIO must be removed from the default v2 compose.

## Quick Start
```bash
pnpm -C project-handbook make -- task-status id=TASK-007 status=doing

cd project-handbook/sprints/current/tasks/TASK-007-cutover-replace-minio-with-seaweedfs-s3-gateway
cat steps.md
cat commands.md
cat validation.md
```

## Dependencies
- `TASK-006` must be `done` and its artifact write/read probe must pass against MinIO before starting this cutover.

## Acceptance Criteria
See `task.yaml` acceptance section and `checklist.md` for completion requirements.
