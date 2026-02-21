# Concepts

## Handbook instance repo

A “handbook instance repo” is any directory that contains `.project-handbook/config.json`.

`ph` treats the directory containing that marker as `PH_ROOT`.

## Where files live

By default, `ph` writes and reads handbook content under:

- `PH_ROOT/.project-handbook/`

Within that root you’ll see familiar handbook domains like:

- `process/` (validation rules, playbooks, session templates)
- `sprints/`, `features/`, `releases/`, `roadmap/`
- `status/` (summaries, evidence, questions, daily)
- `adr/`, `decision-register/`, `backlog/`, `parking-lot/`

## Root resolution (`PH_ROOT`)

`ph` resolves `PH_ROOT` like this:

1. If you pass `--root /path/to/handbook`, that directory must contain `.project-handbook/config.json`.
2. Otherwise, `ph` searches upward from your current working directory until it finds `.project-handbook/config.json`.

When developing or working in monorepos, prefer `--root` to avoid operating on the wrong repo.

## Post-command hook (history + quick validate)

Many mutating commands run a post-command hook after success:

- append to command history
- run `ph validate --quick`

Disable as needed:

- `--no-post-hook` (disable both)
- `--no-history` (keep validation)
- `--no-validate` (keep history)

## Non-destructive defaults

Most generators are conservative:

- they create missing files/directories
- they refuse to overwrite existing content unless you pass a `--force` option (when supported)

Example: `ph sprint plan --force` overwrites an existing sprint `plan.md`.

## Output and automation

Some commands are designed for scripting and support machine-friendly output:

- `ph next --format text|json`
- `ph release draft --format text|json`
- `ph parking review --format text|json`

When a command supports JSON output, prefer avoiding extra stdout noise (or use `--no-post-hook` during debugging).

## Task taxonomy (`task_type`) and sessions

`task_type` is the canonical task taxonomy field in `task.yaml`.

Allowed values:

- `implementation`
- `research-discovery`
- `feature-research-planning`
- `task-docs-deep-dive`
- `sprint-gate`

Session templates are derived from `task_type` (for example, `task_type=implementation` uses the `task-execution` template).

Legacy tasks may contain a `session:` field in `task.yaml`. That field is deprecated:

- if `task_type` is present, `session` is ignored for behavior
- mismatches between `task_type` and `session` fail validation / pre-exec
- matches emit warnings (delete `session:`)

Migration helper (current sprint only):

- `ph process refresh --migrate-tasks-drop-session`

## Evidence capture

`ph evidence` captures command output into a deterministic directory tree:

- `ph evidence new --task TASK-123`
- `ph evidence run --task TASK-123 --name lint -- uv run ruff check .`

Evidence is written under:

- `.project-handbook/status/evidence/TASK-123/<RUN_ID>/`

By default, `ph evidence run` does not stream stdout/stderr; it writes to files (plus a `meta.json` summary).

Security: avoid capturing secrets (tokens, API keys, `.env` dumps) into evidence.
