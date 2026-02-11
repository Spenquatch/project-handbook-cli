---
title: Playbook - Backlog Triage
type: process
date: {date}
tags: [process, playbook, backlog, triage]
links: []
---

# Playbook - Backlog Triage

## Purpose
Keep the backlog actionable: accurate severity, clear impact, explicit next steps, and sprint assignment when appropriate.

## Core commands
```bash
ph backlog rubric
ph backlog list --severity P0
ph backlog list --severity P1
ph backlog triage --issue BUG-P1-...
ph backlog assign --issue BUG-P1-... --sprint current
```

## Triage flow
1. Pick the next issue (start with P0, then P1).
2. Run `ph backlog triage --issue ...` and update the issue’s triage notes with:
   - reproduction / impact,
   - suspected root cause,
   - recommended approach and estimated effort,
   - whether it should be pulled into the current sprint.
3. Assign to sprint if it is actionable now:
   - `ph backlog assign --issue ... --sprint current`
