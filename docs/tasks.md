# Tasks

Tasks are the unit of sprint execution. A task is a directory under the active sprint with a `task.yaml` metadata file and supporting docs (steps, commands, validation, checklist).

## Where tasks live

Project scope:

- `.project-handbook/sprints/current/tasks/TASK-###-<slug>/`

System scope:

- `.project-handbook/system/sprints/current/tasks/TASK-###-<slug>/`

## Creating tasks

Create a task under the current sprint:

```bash
ph task create --title "Implement X" --feature foo --decision ADR-0001 --type implementation
```

Common flags:

- `--points 5` (defaults come from `process/checks/validation_rules.json` when present)
- `--owner @alice`
- `--lane ops/automation`
- `--release current|vX.Y.Z`
- `--gate` (mark as a release gate: `release_gate: true`)

## Task taxonomy: `task_type` is canonical (v0.0.24+)

`task_type` is the canonical taxonomy field in `task.yaml`.

Allowed values:

- `implementation` (default)
- `research-discovery`
- `feature-research-planning`
- `task-docs-deep-dive`
- `sprint-gate`

Session templates are derived from `task_type` (for example, `implementation` uses `task-execution`).

Legacy `session:` in `task.yaml` is deprecated:

- if `task_type` exists, `session` is ignored for behavior
- mismatches fail validation / pre-exec
- matches emit warnings (delete `session:`)

Migration helper (current sprint only):

```bash
ph process refresh --migrate-tasks-drop-session
```

## Task structure

`ph task create` scaffolds a directory like:

```text
TASK-001-implement-x/
  task.yaml
  README.md
  steps.md
  commands.md
  checklist.md
  validation.md
  source/
```

## Updating task status

Update the task status (with dependency checks):

```bash
ph task status --id TASK-001 --status doing
```

Allowed statuses are configurable via `process/checks/validation_rules.json` (`task_status.allowed_statuses`).
If not configured, the default set is:

- `todo`, `doing`, `review`, `done`, `blocked`

## Dependencies

Dependencies are recorded in `task.yaml` as `depends_on: [...]`.

When moving a task into `doing`, `review`, or `done`, `ph task status` validates that dependency tasks are complete (unless you pass `--force`).

## Evidence

Evidence is stored separately from the task directory under:

- `.project-handbook/status/evidence/TASK-###/<RUN_ID>/`

Capture evidence for a command:

```bash
ph evidence run --task TASK-001 --name ruff -- uv run ruff check .
```

`ph evidence run` captures stdout/stderr into files (it does not stream by default).

## Quality gates

Before execution (or before handing off):

- `ph validate --quick`
- `ph pre-exec lint` (task/sprint gate)
- `ph pre-exec audit` (evidence bundle + lint)

