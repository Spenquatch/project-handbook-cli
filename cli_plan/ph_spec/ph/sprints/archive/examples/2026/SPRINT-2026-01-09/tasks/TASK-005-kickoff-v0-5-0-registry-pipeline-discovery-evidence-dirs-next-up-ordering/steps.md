---
title: Kickoff: v0.5.0 registry pipeline discovery (evidence dirs + next-up ordering) - Implementation Steps
type: implementation
date: 2026-01-09
task_id: TASK-005
tags: [implementation]
links: []
---

# Implementation Steps: Kickoff: v0.5.0 registry pipeline discovery (evidence dirs + next-up ordering)

## Overview
This is a sprint hygiene + documentation wiring task:
- validate the dependency graph so `TASK-005` is “Next up”, and
- define evidence conventions so the downstream `research-discovery` tasks (`TASK-001`..`TASK-004`) all capture comparable artefacts.

## Prerequisites
- `ph` installed
- Prefer explicit root selection when needed: `ph --root <PH_ROOT> ...`

## Step 1 — Confirm sprint task graph and “Next up”
1. Run `ph sprint status`.
2. Confirm “Next up” is `TASK-005` (all other tasks should depend on it).
3. If “Next up” is not `TASK-005`, fix only `depends_on` fields in `ph/sprints/current/tasks/*/task.yaml` until it is.

Evidence to capture:
- `ph/status/evidence/TASK-005/sprint-status.txt` (copy/paste output)

## Step 2 — Define evidence conventions for this workstream
Create `ph/status/evidence/TASK-005/README.md` that answers, explicitly:
1. For each of `TASK-001`..`TASK-004`, which evidence files must exist under `ph/status/evidence/TASK-00X/`.
2. Naming conventions (recommended):
   - `index.md` as the evidence table-of-contents for each task
   - `rg-*.txt` for ripgrep outputs
   - `*-snippets.txt` for curated excerpts
   - `*-inventory.md` for structured lists/tables
3. Redaction rules:
   - no secrets in evidence (no `.env` dumps, no tokens, no Vault JSON payloads)
   - if a command could print secrets, capture only redacted output or a “counts-only” summary

## Step 3 — Update downstream tasks to reference the conventions
Ensure each of `TASK-001`..`TASK-004`:
- points to the convention doc in its `references.md`, and
- lists the required evidence files in `validation.md`.

## Step 4 — Handbook validation
Run:
- `ph validate`

Evidence to capture:
- `ph/status/evidence/TASK-005/handbook-validate.txt`

## Step 5 — Mark ready for review
1. Complete `checklist.md`.
2. Set status: `ph task status --id TASK-005 --status review`.
