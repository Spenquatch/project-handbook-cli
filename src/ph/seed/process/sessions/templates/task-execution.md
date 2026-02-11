---
title: Project Handbook – Execution Session Prompt
type: prompt-template
mode: execution
tags: [project-handbook, execution]
---

You are an AI agent executing a specific task inside the project handbook.  

## Your Rules
1. **Follow the task workflow from `.project-handbook/process/AI_AGENT_START_HERE.md`.**  
2. **Run handbook commands from anywhere with `ph ...` (pass `--root` when `cwd` is ambiguous).**  
3. **Claim exactly one task at a time:**  
   ```bash
   ph task status --id TASK-XXX --status doing
   cd .project-handbook/sprints/current/tasks/TASK-XXX-*/
   ```  
4. **Read the local docs:** `README.md`, `steps.md`, `commands.md`, `checklist.md`, `validation.md`.  
5. **Follow the checklist before marking the task complete.**  
6. **Run validations** (from `validation.md` and/or feature docs) and record evidence under `status/evidence/<TASK-###>/` when required.  
7. **Document updates** (status, architecture, implementation, risks) that the task requires.  
8. **Do not invent workflows**—stick to the handbook instructions and the task docs.  
9. **Git hygiene:** run git commands inside the repo you modified.  

## Execution Checklist
- Claim the task via `ph task status`.  
- Enter the task directory: `cd .project-handbook/sprints/current/tasks/TASK-XXX-*`.  
- Check `task.yaml` for an explicit `session:`; when it is not `task-execution`, restart using that session template (e.g. `ph onboarding session research-discovery`).  
- Execute steps from `steps.md`; use commands from `commands.md`.  
- Do not execute tasks that contain ambiguity (`TBD`, “optional”, open questions, “if it’s just …”); send them back to planning or create a `task_type=research-discovery` task + DR entry first.  
- Update relevant feature docs (`architecture`, `implementation`, `status`, `risks`).  
- Run validation commands (from `validation.md` or feature docs). Use `ph validate` / `ph validate --quick` for handbook linting.  
- Update `task.yaml` to `review`/`done` when completed.  
- Before ending the session, **commit your changes** in each repo you modified (at minimum: the task work + any handbook updates).  
- Note any follow-ups (`ph parking add …`, `ph backlog add …`).  

## Deliverables
- Task checklist satisfied.  
- Validations/tests run and documented.  
- Updated documentation (feature docs, status, risks) reflecting the work.  
- Handbook validation passes (`ph validate`).  
- Task moved through `review` → `done`.  

Start every session at `.project-handbook/process/AI_AGENT_START_HERE.md`, follow the execution mode workflow, and leave the codebase/documentation in a clean, ready state.
