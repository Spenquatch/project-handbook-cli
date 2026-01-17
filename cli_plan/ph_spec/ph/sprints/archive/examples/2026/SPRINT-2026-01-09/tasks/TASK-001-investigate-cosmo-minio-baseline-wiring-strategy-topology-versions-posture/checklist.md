---
title: Investigate: Cosmo+MinIO baseline wiring strategy (topology, versions, posture) - Completion Checklist
type: checklist
date: 2026-01-09
task_id: TASK-001
tags: [checklist]
links: []
---

# Completion Checklist: Investigate: Cosmo+MinIO baseline wiring strategy (topology, versions, posture)

## Completion Criteria (matches `task.yaml`)
- [ ] `ph/decision-register/DR-0003-cosmo-minio-baseline-topology.md`:
  - [ ] includes exactly two viable options (A/B) with pros/cons/implications/risks/unlocks/quick wins
  - [ ] includes a recommendation and rationale
  - [ ] ends with an explicit operator/user approval request
  - [ ] remains `Status: Proposed` pending approval
- [ ] `ph/features/v2_registry-cosmo-minio-required/architecture/ARCHITECTURE.md` updated with:
  - [ ] Cosmo service inventory + pinned image tags
  - [ ] MinIO inventory + posture (no Traefik exposure; explicitly state whether host binds are forbidden (Option A) or allowed on `127.0.0.1` only (Option B))
- [ ] `ph/features/v2_registry-cosmo-minio-required/implementation/IMPLEMENTATION.md` updated with:
  - [ ] exact v2 wiring points (file paths)
  - [ ] required env/secrets list (high-level; reference DR-0004 for the contract)
  - [ ] bucket init approach + smoke probes
- [ ] Evidence exists under `ph/status/evidence/TASK-001/` and is referenced from DR-0003
- [ ] `ph validate` passes
