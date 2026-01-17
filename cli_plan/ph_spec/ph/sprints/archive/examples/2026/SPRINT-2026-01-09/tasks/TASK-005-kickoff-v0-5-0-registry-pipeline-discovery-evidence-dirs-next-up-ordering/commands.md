---
title: Kickoff: v0.5.0 registry pipeline discovery (evidence dirs + next-up ordering) - Commands
type: commands
date: 2026-01-09
task_id: TASK-005
tags: [commands]
links: []
---

# Commands: Kickoff: v0.5.0 registry pipeline discovery (evidence dirs + next-up ordering)

## Task Status
```bash
ph task status --id TASK-005 --status doing
ph task status --id TASK-005 --status review
ph task status --id TASK-005 --status done
```

## Evidence Directory
```bash
EVID_DIR="ph/status/evidence/TASK-005"
mkdir -p "$EVID_DIR"
```

## Sprint Graph + “Next up”
```bash
ph sprint status | tee "$EVID_DIR/sprint-status.txt"
ph task list | tee "$EVID_DIR/task-list.txt"
```

## Evidence Conventions Doc
```bash
${EDITOR:-vi} "$EVID_DIR/README.md"
```

## Handbook Validation
```bash
ph validate | tee "$EVID_DIR/handbook-validate.txt"
```

## Notes
- Avoid “service commands” here; this task is handbook-only wiring. No `make -C v2 v2-up`, no Docker bring-up.
