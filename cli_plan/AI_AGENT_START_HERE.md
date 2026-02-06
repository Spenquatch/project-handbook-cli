---
title: CLI Plan – AI Agent Start Here
type: process
date: 2026-01-14
tags: [cli, plan, execution, agent]
links:
  - ./archive/tasks_legacy.json
  - ./tasks_v1_next.json
  - ./archive/strict_parity_2026-02/tasks_v1_parity.json
  - ./archive/strict_parity_2026-02/due-diligence.json
  - ./backlog.json
  - ./session_logs.md
  - ./archive/strict_parity_2026-02/PARITY_CHECKLIST.md
  - ./v1_cli/ADR-CLI-0001-ph-cli-migration.md
  - ./v1_cli/ADR-CLI-0002-handbook-instance-scaffolding.md
  - ./v1_cli/ADR-CLI-0003-ph-project-layout.md
  - ./v1_cli/ADR-CLI-0004-ph-root-layout.md
  - ./v1_cli/CLI_CONTRACT.md
  - ./archive/strict_parity_2026-02/v0_make/MAKE_CONTRACT.md
  - ./ph_spec/
---

# CLI Plan – AI Agent Start Here

This folder is the **only** place we track v1 CLI execution planning and due diligence. Do not update general handbook onboarding docs for v1; keep v1 planning scoped to `cli_plan/`.

## What you are building

- A separately-installed Python CLI tool named `project-handbook` that provides the `ph` command.
- The `ph` tool operates on a “handbook instance repo” (any repo with `project_handbook.config.json`) as **data/templates/plans**, and MUST NOT execute repo-local Python scripts at runtime.
  - Reference implementation for parity/real-world behavior: `/Users/spensermcconnell/__Active_Code/oss-saas/project-handbook` (invoked via `pnpm make -- <target>`).
  - When running commands during development, prefer `ph --root /absolute/path/to/target` so you don’t accidentally operate on the wrong directory.

## Sources of truth (read in this order)

1. `cli_plan/v1_cli/ADR-CLI-0004-ph-root-layout.md` (project layout + marker)
2. `cli_plan/v1_cli/CLI_CONTRACT.md`
3. `cli_plan/ph_spec/` (directory-by-directory spec + examples)
4. `cli_plan/tasks_v1_next.json` (active incremental work queue)
5. `cli_plan/archive/strict_parity_2026-02/due-diligence.json` (historical; complete)
6. `cli_plan/archive/strict_parity_2026-02/v0_make/MAKE_CONTRACT.md` (historical parity reference)
7. `cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md` (historical context)
8. `cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md` (historical context; superseded)
9. `cli_plan/v1_cli/ADR-CLI-0002-handbook-instance-scaffolding.md` (historical context; superseded)

## Root marker for v1

For v1, the handbook instance repo root is detected by the presence of:

- `project_handbook.config.json`

The `ph` CLI MUST treat the directory that contains `project_handbook.config.json` as `PH_ROOT`.

## Workstreams

There are two primary workstreams under `cli_plan/`:

1. **Next tasks (active)**: incremental v1 improvements in `cli_plan/tasks_v1_next.json`.
2. **Backlog (active)**: items that require contract/spec decisions first in `cli_plan/backlog.json` (+ tech-debt notes in `cli_plan/backlog.md`).

Historical (kept for audit trail):
- Due diligence queue: `cli_plan/archive/strict_parity_2026-02/due-diligence.json` (complete).
- Strict parity queue + checklist: `cli_plan/archive/strict_parity_2026-02/` (complete).
- Original migration queue: `cli_plan/archive/tasks_legacy.json` (complete).

Default policy:
- Use `cli_plan/tasks_v1_next.json` for new work.
- Only refer to archived queues for historical context.

Important note:
- `cli_plan/archive/tasks_legacy.json` and older `cli_plan/session_logs.md` entries include historical references to a deprecated `.ph/**` / `ph/**` layout. For v1, treat `cli_plan/v1_cli/CLI_CONTRACT.md` + `cli_plan/ph_spec/` as authoritative.

## Strict workflow (do this every session)

1. Decide the active queue:
   - Use **Next queue workflow** (`cli_plan/tasks_v1_next.json`) for new work.
2. Select exactly one task to execute (algorithm below).
3. Before doing any work:
   - set that task’s `status` to `in_progress` in the appropriate JSON file
   - append exactly one new entry to `cli_plan/session_logs.md` using the template in that file
4. Execute the task exactly as written (no scope creep; do not execute other task IDs).
5. When finished, update both:
   - the appropriate JSON file: set status to `done` OR `blocked` (and record blockers)
   - `cli_plan/session_logs.md`: fill in verification, outcome, and the computed “Next task”
6. Stop. The next session starts again from step 1.

## Task selection algorithm (zero ambiguity)

### Due diligence queue (archived) (`cli_plan/archive/strict_parity_2026-02/due-diligence.json`)

Given `cli_plan/archive/strict_parity_2026-02/due-diligence.json`:

1. If there is exactly one task with `status == "in_progress"`, continue that same task.
2. Else pick the single task with `status == "todo"` with the lowest numeric ID (e.g. `DD-0001` before `DD-0100`).
3. If none are `todo`:
   - if there are blocked tasks, pick the blocked task with the lowest numeric ID and work only on unblocking it
   - else stop and report: “No runnable due-diligence tasks. All due-diligence tasks are done.”

### CLI queue (`cli_plan/archive/tasks_legacy.json`)

Given `cli_plan/archive/tasks_legacy.json`:

1. Build the set `DONE = { task.id | task.status == "done" }`.
2. Compute the candidate list:
   - `CANDIDATES = [ task | task.status == "todo" AND every dep in task.depends_on is in DONE ]`
3. If `CANDIDATES` is empty:
   - pick the single `blocked` task with the lowest `(phase.order, task.order)` and work only on unblocking it
   - if there are no blocked tasks, stop and report: “No runnable tasks. All tasks are done.”
4. Otherwise pick the single task in `CANDIDATES` with the lowest `(phase.order, task.order)`.
5. The selected task is “the next task” for this session.

### Next queue (`cli_plan/tasks_v1_next.json`)

Given `cli_plan/tasks_v1_next.json`:

1. Build the set `DONE = { task.id | task.status == "done" }`.
2. Compute the candidate list:
   - `CANDIDATES = [ task | task.status == "todo" AND every dep in task.depends_on is in DONE ]`
3. If `CANDIDATES` is empty:
   - pick the single `blocked` task with the lowest `(phase.order, task.order)` and work only on unblocking it
   - if there are no blocked tasks, stop and report: “No runnable v1-next tasks. All v1-next tasks are done.”
4. Otherwise pick the single task in `CANDIDATES` with the lowest `(phase.order, task.order)`.
5. The selected task is “the next task” for this session.

### Parity queue (archived) (`cli_plan/archive/strict_parity_2026-02/tasks_v1_parity.json`)

Given `cli_plan/archive/strict_parity_2026-02/tasks_v1_parity.json`:

1. Build the set `DONE = { task.id | task.status == "done" }`.
2. Compute the candidate list:
   - `CANDIDATES = [ task | task.status == "todo" AND every dep in task.depends_on is in DONE ]`
3. If `CANDIDATES` is empty:
   - pick the single `blocked` task with the lowest `(phase.order, task.order)` and work only on unblocking it
   - if there are no blocked tasks, stop and report: “No runnable parity tasks. All parity tasks are done.”
4. Otherwise pick the single task in `CANDIDATES` with the lowest `(phase.order, task.order)`.
5. The selected task is “the next task” for this session.

## How to mark progress

### Due diligence tasks (archived) (`cli_plan/archive/strict_parity_2026-02/due-diligence.json`)

For the active due-diligence task object:

- On start:
  - set `"status": "in_progress"`
  - add `"started_at": "YYYY-MM-DDTHH:MM:SSZ"` (UTC)
  - add `"last_session_log_ref": "cli_plan/session_logs.md#<paste the entry heading>"`
- On completion:
  - set `"status": "done"`
  - add `"completed_at": "YYYY-MM-DDTHH:MM:SSZ"` (UTC)
  - add `"next_task_id": "<computed next DD-#### id or NONE>"`
- On blocked:
  - set `"status": "blocked"`
  - add `"blocked_at": "YYYY-MM-DDTHH:MM:SSZ"` (UTC)
  - add `"blockers": ["<concrete blocker>", "..."]`
  - add `"unblock_steps": ["<exact step to unblock>", "..."]`
  - add `"next_task_id": "<computed next DD-#### id or NONE>"`

### CLI tasks (`cli_plan/archive/tasks_legacy.json`)

For the active CLI task object:

- On start:
  - set `"status": "in_progress"`
  - set `"started_at": "YYYY-MM-DDTHH:MM:SSZ"` (UTC)
  - set `"last_session_log_ref": "cli_plan/session_logs.md#<paste the entry heading>"`
- On completion:
  - set `"status": "done"`
  - set `"completed_at": "YYYY-MM-DDTHH:MM:SSZ"` (UTC)
  - set `"next_task_id": "<computed next task id>"`
- On blocked:
  - set `"status": "blocked"`
  - set `"blocked_at": "YYYY-MM-DDTHH:MM:SSZ"` (UTC)
  - set `"blockers": ["<concrete blocker>", "..."]`
  - set `"unblock_steps": ["<exact step to unblock>", "..."]`
  - set `"next_task_id": "<computed next task id>"` (this will typically be the same task, until unblocked)

These tracking fields are permitted and expected even if they were not present originally.

## Non-negotiables

- Keep execution planning here (`cli_plan/`) only.
- Follow the contract exactly; if you must change the contract, do it as a dedicated task and explain why in session logs.
- Prefer small PR-sized tasks; do not bundle multiple task IDs into one run.
