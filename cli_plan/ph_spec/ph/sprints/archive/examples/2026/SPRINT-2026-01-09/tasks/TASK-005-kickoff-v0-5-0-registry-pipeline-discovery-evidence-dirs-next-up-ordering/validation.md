---
title: Kickoff: v0.5.0 registry pipeline discovery (evidence dirs + next-up ordering) - Validation Guide
type: validation
date: 2026-01-09
task_id: TASK-005
tags: [validation]
links: []
---

# Validation Guide: Kickoff: v0.5.0 registry pipeline discovery (evidence dirs + next-up ordering)

## Automated Validation
```bash
pnpm -C project-handbook make -- validate
pnpm -C project-handbook make -- sprint-status
```

## Manual Validation
Pass/fail checks:
1. `pnpm -C project-handbook make -- sprint-status` includes:
   - `Next up: TASK-005`
2. `project-handbook/status/evidence/TASK-005/README.md` exists and includes:
   - a section for each of `TASK-001`, `TASK-002`, `TASK-003`, `TASK-004`
   - an explicit list of required evidence files per task (or required “kinds” of evidence with naming rules)
   - a “no secrets in evidence” rule and examples of what not to capture

Evidence files that must exist before `review`:
- `project-handbook/status/evidence/TASK-005/sprint-status.txt`
- `project-handbook/status/evidence/TASK-005/handbook-validate.txt`

## Sign-off
- [ ] All validation steps completed
- [ ] Evidence documented above
- [ ] Ready to mark task as "done"
