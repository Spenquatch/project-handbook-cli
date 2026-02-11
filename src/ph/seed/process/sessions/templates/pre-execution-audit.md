---
title: Project Handbook – Pre-Execution Dependency & Quality Gate Prompt
type: prompt-template
mode: pre-execution-audit
tags: [project-handbook, dependency-check, quality-gate]
---

You are an AI agent performing a final audit on sprint planning documentation before execution begins.

## Your Rules
1. **Run after sprint planning + task doc deep dive.** Treat this as a gatekeeper: no code changes, only documentation/handbook fixes.  
2. **Work inside `.project-handbook/`** using `ph <target>`.  
3. **Verify dependencies, execution order, and readiness** for every sprint task.  
4. **Fix gaps immediately** (missing steps, weak validation, unclear ownership).  
5. **Finish with a clean validation report** (`ph validate`).
6. **Reject ambiguity (strict).** Any task containing ambiguity language must be rewritten, split, or re-routed to `session=research-discovery` (with a DR entry) before execution starts.
   - Ambiguity includes (non-exhaustive): `TBD`, `TODO`, `WIP`, `FIXME`, “open question”, “depends on local setup/environment”, “optional”, “nice to have”, “if time/possible”, “maybe”, “unclear/unknown”, “we'll decide”, and **implementation-choice language** like “implementation decision”, “choose between”, “pick an approach”.
7. **Session ↔ core purpose alignment (non-negotiable).**
   - `session: task-execution` tasks must be fully implementable with zero remaining decisions (no “choose/decide/pick approach” language anywhere in task docs).
   - `session: research-discovery` tasks must reduce uncertainty and produce a Decision Register (DR) with **exactly two options (Option A / Option B)** + recommendation + follow-up tasks.
8. **Session routing rule.** For every sprint task, confirm `task.yaml session:` matches the task docs (README front matter + steps/validation semantics). Do not approve a task under the wrong session template.

## Hard-Fail Gates (Execution Cannot Start Until Green)
- `ph validate` is clean (0 errors / 0 warnings).
- `ph sprint status` is healthy (no dependency errors; current sprint is coherent).
- If a release is active: `ph release status` is coherent (tagged work + gate burn-up match the sprint plan). For full context during audit, also check `ph release show`.
- `ph pre-exec lint` passes (session/purpose alignment + ambiguity lint + required fields/files + sprint gate task required).

## Required Audit Evidence Bundle (Do Not Skip)
All audit outputs must be captured under:
- `.project-handbook/status/evidence/PRE-EXEC/<SPRINT-ID>/<YYYY-MM-DD>/`

This evidence bundle must include (non-empty):
- `sprint-status.txt`
- `release-status.txt`
- `task-list.txt`
- `feature-summary.txt`
- `handbook-validate.txt`
- `validation.json`
- `pre-exec-lint.txt` (or equivalent “PASSED” output)

## Required Commands (Copy/Paste)
Run exactly this (it prints `EVIDENCE_DIR=...` and writes the evidence bundle):
```bash
ph pre-exec audit
```

For debugging (these are executed by `ph pre-exec audit` internally):
```bash
ph sprint status
ph release status
ph task list
ph feature summary
ph validate
ph pre-exec lint
```

## Audit Checklist
- For each sprint task (`sprints/current/tasks/TASK-XXX-*`):
  - Confirm `task.yaml` has: `owner`, `story_points`, `lane`, `feature`, `decision`, `depends_on`, `session`.  
  - If the task contributes to the active release, confirm it has `release: vX.Y.Z` (or `release: current`) and `release_gate: true|false`.  
  - Confirm README front matter matches `task.yaml` (`task_id`, `feature`, `session`).  
  - Review `README.md`, `steps.md`, `commands.md`, `checklist.md`, `validation.md`, `references.md` for completeness and *copy/paste runnable commands*.  
  - Ensure commands include prerequisites (env vars, services) and write evidence to explicit task-scoped paths.  
  - Verify validation is binary Pass/Fail and maps directly to acceptance criteria + sprint goals.  
  - Confirm dependencies are documented in feature `status.md` or sprint `plan.md`.
- Check ordering & lane boundaries:
  - Note cross-task dependencies and ensure plan includes sequencing.  
  - Confirm any external blockers/backlog items are referenced with IDs.  
  - Identify missing details (e.g., absent screenshots, outdated links).
- Log adjustments:
  - Fix documentation gaps directly.  
  - Add follow-up backlog items for unresolved issues.  
  - Update sprint `plan.md` with dependency/order notes.  

## Deliverables
- Sprint plan annotated with dependency/order notes.  
- Every task directory fully audit-ready (no missing fields, steps, or validation instructions).  
- Feature status pages updated with cross-task dependencies.  
- Backlog/parking entries for uncovered risks or follow-up work.  
- Validation report clean (`.project-handbook/status/validation.json`).  
- Audit evidence bundle present under `.project-handbook/status/evidence/PRE-EXEC/<SPRINT-ID>/<YYYY-MM-DD>/`.
- Recommended: add a summary snippet in `plan.md` confirming the audit gate passed and execution can begin.
