---
title: Playbook - Sprint Planning
type: process
date: {date}
tags: [process, playbook, sprint, planning]
links:
  - ../sessions/templates/sprint-planning.md
  - ./release-planning.md
  - ../AI_AGENT_START_HERE.md
---

# Playbook - Sprint Planning

## Purpose
Plan a sprint that is:
- bounded by lanes (default),
- aligned to an active release slot when applicable,
- executable with deterministic task docs,
- gated by a required sprint gate task.

## Sprint Planning Flow

### 1) Load context
```bash
cat .project-handbook/AGENT.md
cat .project-handbook/process/AI_AGENT_START_HERE.md
cat .project-handbook/process/sessions/logs/latest_summary.md
```

If a release is active:
```bash
ph release show
```

### 2) Create the sprint plan
```bash
ph sprint plan
```

### 3) Sprint gate (required; exists from Day 0, closes last)

`ph sprint plan` will scaffold a sprint gate task if one does not already exist.

Fill in the sprint gate `validation.md` early (goal + exit criteria + evidence paths), but expect to mark it `done`
at the end of the sprint once the exit criteria are met.

If you need to create one manually:
```bash
ph task create \
  --title "Sprint Gate: <goal>" \
  --feature feature-name \
  --decision ADR-XXXX \
  --type sprint-gate \
  --points 3
```

### 4) Seed tasks by lane and type
Discovery work:
```bash
ph dr add --id DR-0001 --title "<question title>" --feature feature-name
ph task create \
  --title "Investigate: <question>" \
  --feature feature-name \
  --decision DR-0001 \
  --type research-discovery \
  --points 3 \
  --lane "product/research"
```

Implementation work:
```bash
ph task create \
  --title "Implement: <deliverable>" \
  --feature feature-name \
  --decision ADR-XXXX \
  --type implementation \
  --points 3 \
  --lane "eng/<lane>"
```

Release gates (burn-up):
```bash
ph task create \
  --title "Release Gate: <name>" \
  --feature feature-name \
  --decision ADR-XXXX \
  --points 3 \
  --release current \
  --gate \
  --lane "ops/gates"
```

### 5) Run gates before execution starts
```bash
ph validate --quick
ph pre-exec lint
```

Optional (evidence bundle):
```bash
ph pre-exec audit
```

## Sprint execution hygiene
- Keep task statuses current: `ph task status --id TASK-### --status doing|review|done|blocked`.
- Record evidence under `.project-handbook/status/evidence/<TASK-###>/` when required by `validation.md`.
