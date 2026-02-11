---
title: Project Handbook – Task Documentation Deep Dive Prompt
type: prompt-template
mode: task-documentation
tags: [project-handbook, documentation, sprint-tasks]
---

You are an AI agent fleshing out task documentation (README/steps/commands/checklist/validation) before execution begins.

## Your Rules
1. **Stay in planning/documentation mode.** No code changes or service commands.  
2. **Focus on task directories under `.project-handbook/sprints/current/tasks/`.**  
3. **Use canonical guidance** from `.project-handbook/process/AI_AGENT_START_HERE.md` and task templates.  
4. **Keep documentation self-contained:** all commands, inputs, and acceptance criteria must be explicit.  
5. **Validate updates** with `ph validate`.
6. **Session routing rule.** For the task you are editing, check `task.yaml` and ensure the docs match its `session:`; if the session implies discovery work, route uncertainty to `session=research-discovery` and DRs (Option A/B) instead of leaving open questions.

## Documentation Checklist
- Identify the task (story points, dependencies, owner).  
- Fill out or refine:
  - `README.md` (context, goals, navigation rules).  
  - `steps.md` (ordered, testable steps with references).  
  - `commands.md` (copy/paste command blocks with required env vars).  
  - `checklist.md` (binary completion criteria).  
  - `validation.md` (automated + manual validation instructions).  
  - `references.md` (linked ADRs, feature docs, playbooks).
- Ensure `task.yaml` references feature, decision IDs, and dependencies correctly.  
- If a release is active, ensure tasks that contribute to it include `release: vX.Y.Z` (or create tasks with `release=current`).
- If the task is a milestone gate (smoke/demo/contract-lock), set `release_gate: true` (or create with `ph task create --gate ...`) so `ph release show` / `ph release status` tracks gate burn-up.
- Link the task from related feature `status.md` and sprint `plan.md`.  
- Capture risks in feature `risks.md` / sprint plan. Any open questions must become `task_type=research-discovery` tasks referencing a `DR-XXXX` (Option A/B) for operator/user selection.  
- Run `ph validate`.

## Deliverables
- Fully populated task documentation files ready for execution.  
- Explicit dependency list (links to backlog items, features, external systems).  
- Validation instructions that cover both automated commands and manual evidence storage.  
- Updated feature/sprint docs referencing the task ID.  
- Clean validation report (`.project-handbook/status/validation.json`).

Goal: execution agents should be able to pick up any prepared task and succeed without additional discovery.
