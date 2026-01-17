---
title: Investigate: Harvester publish workflow (SDL sources, mirror updates, report contract) + codegen wiring - Completion Checklist
type: checklist
date: 2026-01-09
task_id: TASK-004
tags: [checklist]
links: []
---

# Completion Checklist: Investigate: Harvester publish workflow (SDL sources, mirror updates, report contract) + codegen wiring

## Completion Criteria (matches `task.yaml`)
- [ ] `project-handbook/decision-register/DR-0006-harvester-publish-and-codegen-workflow.md`:
  - [ ] includes exactly two viable options (A/B) with pros/cons/implications/risks/unlocks/quick wins
  - [ ] includes a recommendation and rationale
  - [ ] ends with an explicit operator/user approval request
  - [ ] remains `Status: Proposed` pending approval
- [ ] `project-handbook/features/v2_schema-harvester-service/implementation/IMPLEMENTATION.md` updated with:
  - [ ] execution-ready harvester plan (sources, sequencing, mirror writepoints, report contract, sanitization posture)
- [ ] `project-handbook/features/v2_codegen-from-registry/implementation/IMPLEMENTATION.md` updated with:
  - [ ] canonical codegen wiring (local + CI)
  - [ ] explicit dependency on publish/check
- [ ] Evidence exists under `project-handbook/status/evidence/TASK-004/` and is referenced from DR-0006
- [ ] `pnpm -C project-handbook make -- validate` passes
