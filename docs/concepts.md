# Concepts

## Handbook instance repo

A “handbook instance repo” is any directory that contains `.project-handbook/config.json`.

`ph` treats the directory containing that marker as `PH_ROOT`.

## Where files live

By default, `ph` writes and reads handbook content under:

- Project scope (default): `PH_ROOT/.project-handbook/`
- System scope: `PH_ROOT/.project-handbook/system/`

Within those roots you’ll see familiar handbook domains like:

- `process/` (validation rules, playbooks, session templates)
- `sprints/`, `features/`, `releases/`, `roadmap/`
- `status/` (summaries, evidence, questions, daily)
- `adr/`, `decision-register/`, `backlog/`, `parking-lot/`

## Root resolution (`PH_ROOT`)

`ph` resolves `PH_ROOT` like this:

1. If you pass `--root /path/to/handbook`, that directory must contain `.project-handbook/config.json`.
2. Otherwise, `ph` searches upward from your current working directory until it finds `.project-handbook/config.json`.

When developing or working in monorepos, prefer `--root` to avoid operating on the wrong repo.

## Scope (`--scope project|system`)

- Default scope is `project` (data root: `PH_ROOT/.project-handbook/`).
- `system` scope routes data under `PH_ROOT/.project-handbook/system/`.
- You can also set `PH_SCOPE=project|system`.

System scope is intentionally restricted:

- `roadmap` and `releases` are project-scope only.

Some commands are also project-scope only (they will print remediation if run in system scope):

- `ph check-all`
- `ph test system`

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

## Evidence capture

`ph evidence` captures command output into a deterministic directory tree:

- `ph evidence new --task TASK-123`
- `ph evidence run --task TASK-123 --name lint -- uv run ruff check .`

Evidence is written under:

- `.project-handbook/status/evidence/TASK-123/<RUN_ID>/`

By default, `ph evidence run` does not stream stdout/stderr; it writes to files (plus a `meta.json` summary).

Security: avoid capturing secrets (tokens, API keys, `.env` dumps) into evidence.
