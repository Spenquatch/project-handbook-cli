---
title: Investigate: Router consumes Cosmo supergraph (pull model + auth + refresh) - Completion Checklist
type: checklist
date: 2026-01-09
task_id: TASK-003
tags: [checklist]
links: []
---

# Completion Checklist: Investigate: Router consumes Cosmo supergraph (pull model + auth + refresh)

## Completion Criteria (matches `task.yaml`)
- [x] `project-handbook/decision-register/DR-0005-router-supergraph-consumption-from-cosmo.md`:
  - [x] includes exactly two viable options (A/B) with pros/cons/implications/risks/unlocks/quick wins
  - [x] includes a recommendation and rationale
  - [x] ends with an explicit operator/user approval request
  - [x] remains `Status: Proposed` pending approval
- [x] `project-handbook/features/v2_schema-publishing-and-composition/implementation/IMPLEMENTATION.md` updated with:
  - [x] execution-ready Router consumption plan (auth material + refresh model)
  - [x] exact v2 config file paths to change
- [x] Evidence exists under `project-handbook/status/evidence/TASK-003/` and is referenced from DR-0005
- [x] `pnpm -C project-handbook make -- validate` passes
