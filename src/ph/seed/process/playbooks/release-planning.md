---
title: Playbook - Release Planning
type: process
date: {date}
tags: [process, playbook, release, planning]
links:
  - ../sessions/templates/release-planning.md
  - ./sprint-planning.md
  - ./roadmap-planning.md
---

# Playbook - Release Planning

## Purpose
Plan a coherent release that:
- declares goals + scope boundaries,
- plans a sprint-slot timeline with a goal for each slot,
- assigns features,
- defines explicit release gates (burn-up) as sprint tasks.

## Zero-Ambiguity Guardrail
- No execution tasks with `TBD`, “optional”, or open questions.
- When direction depends on uncertain choices: create a `task_type=research-discovery` task + `DR-XXXX` (Option A/B), get operator/user approval, then promote to ADR/FDR and create execution tasks.

## Pre-Planning Checklist
- [ ] Roadmap reviewed (`ph roadmap show`)
- [ ] Feature status reviewed (`ph feature summary`)
- [ ] Parking lot reviewed (`ph parking review`)
- [ ] Backlog reviewed (`ph backlog list --severity P0` and `ph backlog list --severity P1`)
- [ ] Capacity snapshot reviewed (`ph sprint capacity`)

## Release Planning Process

### 1) Snapshot current state
```bash
ph dashboard
ph roadmap show
ph feature summary
ph parking review
ph backlog list --severity P0
ph backlog list --severity P1
ph sprint capacity
```

### 2) Create the release plan scaffold (sprint slots)
```bash
# Choose the next semver explicitly…
ph release plan --version vX.Y.Z --sprints 3

# …or use version=next and let the CLI normalize it to vX.Y.Z
ph release plan --version next --sprints 3
```

### 3) Fill the release plan (required edits)
Edit:
- `.project-handbook/releases/vX.Y.Z/plan.md`

Minimum required:
- `## Release Goals`
- `## Release Type & Scope` (in/out + scope control)
- `## Slot Plans` (for every slot):
  - Goal / Purpose
  - Scope boundaries (in/out)
  - Intended gate(s)
  - Enablement (how this slot advances the release)

### 4) Activate the release (so sprints can align to it)
```bash
ph release activate --release vX.Y.Z
```

### 5) Assign features
```bash
ph feature list
ph feature create --name feature-name

ph release add-feature --release vX.Y.Z --feature feature-name
ph release add-feature --release vX.Y.Z --feature critical-feature --critical
ph release add-feature --release vX.Y.Z --feature big-epic --epic
```

### 6) Define explicit release gates (burn-up) as sprint tasks
Release gates are tasks tagged to the release with `--gate` (sets `release_gate: true`).

```bash
# Ensure a sprint exists before creating tasks.
ph sprint plan

ph task create \
  --title "Release Gate: <name>" \
  --feature feature-name \
  --decision ADR-XXXX \
  --points 3 \
  --release current \
  --gate \
  --lane "ops/gates"
```

### 7) Ensure sprint planning includes sprint gates (required per sprint)
Each sprint must include at least one `task_type: sprint-gate` task:
```bash
ph task create \
  --title "Sprint Gate: <goal>" \
  --feature feature-name \
  --decision ADR-XXXX \
  --type sprint-gate \
  --points 3
```

### 8) Validate release coherence
```bash
ph release show
ph validate --quick
ph pre-exec lint
```

## Ongoing monitoring (weekly)
```bash
ph release status
ph release show
ph sprint status
ph feature summary
```
