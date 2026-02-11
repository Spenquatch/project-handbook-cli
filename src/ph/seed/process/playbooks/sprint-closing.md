---
title: Playbook - Sprint Closing
type: process
date: {date}
tags: [process, playbook, sprint, closing, retrospective]
links:
  - ../sessions/templates/sprint-closing.md
  - ./sprint-planning.md
  - ./daily-status.md
---

# Playbook - Sprint Closing

## Purpose
Close a sprint cleanly:
- task statuses reflect reality,
- follow-ups are captured as sprint tasks, backlog issues, or parking lot items,
- the sprint is archived with a completed retrospective.

## Pre-Close Checklist
- [ ] Sprint exit criteria reviewed in `.project-handbook/sprints/current/plan.md`
- [ ] Task statuses are accurate (`todo|doing|review|done|blocked`)
- [ ] Sprint gate task is complete (exit criteria + evidence)
- [ ] If a release is active: release alignment is correct (`ph release show`)

## Closing Workflow

### 1) Snapshot current state
```bash
ph sprint status
ph sprint burndown
ph task list
ph feature summary
ph release status
ph validate --quick
```

### 2) Convert retro action items into tracked work
```bash
ph backlog add --type work-items --title "Retro action: <short>" --severity P3 --desc "<what + why>" --owner @me
ph parking add --type technical-debt --title "Retro action: <short>" --desc "<what + why>" --owner @me
```

### 3) Close the sprint
```bash
ph sprint close
```

### 4) Post-close housekeeping
```bash
ph status
ph validate --quick
```

Optional:
- Start next sprint: `ph sprint plan`
- Close release (when complete): `ph release close --version vX.Y.Z`
