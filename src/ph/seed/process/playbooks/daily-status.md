---
title: Playbook - Daily Status
type: process
date: {date}
tags: [process, playbook, daily, status]
links:
  - ../AI_AGENT_START_HERE.md
---

# Playbook - Daily Status

## Purpose
Capture a crisp daily status update that stays aligned to the current sprint and (if active) the current release.

## Daily flow
```bash
ph daily generate
ph daily check --verbose
ph sprint status
ph task list
ph feature summary
ph release status
```

## Hygiene
- Keep task statuses current: `ph task status --id TASK-### --status doing|review|done|blocked`.
- Record blockers as backlog or parking lot items:
  - `ph backlog add --type bug|wildcards|work-items --title "..." --severity P0..P4 --desc "..." --owner @me`
  - `ph parking add --type features|technical-debt|research|external-requests --title "..." --desc "..." --owner @me`
