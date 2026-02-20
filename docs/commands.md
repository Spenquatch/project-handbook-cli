# Commands

This is a practical overview of common commands. For authoritative behavior/mapping, refer to `cli_plan/v1_cli/CLI_CONTRACT.md` in this repo.

If you’re new, start with `Quick Start`, then `Concepts` and `Workflows`.

Common global flags:

- `--root /absolute/path/to/handbook`
- `--scope project|system` (default: project)
- `--no-post-hook` / `--no-history` / `--no-validate`

Post-command behavior (defaults):

- Many mutating commands run a post-hook (history + `validate --quick`) after success; disable with `--no-validate` or `--no-post-hook`.

## Diagnostics

- `ph version`
- `ph doctor`
- `ph help [topic]`
- `ph init`
- `ph process refresh [--templates] [--playbooks] [--force] [--disable-system-scope-enforcement] [--migrate-tasks-drop-session]`

Help topics:

- `ph help sprint|task|feature|release|backlog|parking|roadmap|validation|evidence|utilities`

## Daily utilities

- `ph dashboard`
- `ph next [--format text|json]`
- `ph daily <generate|check>`
- `ph onboarding`
- `ph question <add|list|show|answer|close>`
- `ph hooks install`
- `ph clean`
- `ph end-session --log /path/to/rollout.jsonl`

## Validation + status

- `ph validate [--quick]`
- `ph pre-exec <lint|audit> [...]`
- `ph status`
- `ph check-all`
- `ph test system`

Notes:

- `ph check-all` and `ph test system` are project-scope only.

## Sprint

- `ph sprint plan [--sprint SPRINT-SEQ-####|SPRINT-YYYY-MM-DD|SPRINT-YYYY-W##] [--force]`
- `ph sprint open --sprint SPRINT-...`
- `ph sprint status`
- `ph sprint tasks`
- `ph sprint burndown`
- `ph sprint capacity`
- `ph sprint archive [--sprint SPRINT-...]`
- `ph sprint close`

Notes:

- `ph sprint plan` scaffolds a required sprint gate task from Day 0 (expected to close last).
- `ph sprint close` prints a deterministic close checklist and may print a release-close hint when applicable.

## Work items

- `ph feature <list|create|status|update-status|summary|archive>`
- `ph task <create|list|show|status>`

## Backlog + parking

- `ph backlog <add|list|triage|assign|rubric|stats>`
- `ph parking <add|list|review|promote>` (`review` is non-interactive; supports `--format text|json`)

## Evidence

- `ph evidence new --task TASK-### [--name manual] [--run-id <run-id>]`
- `ph evidence run --task TASK-### --name <label> [--run-id <run-id>] -- <cmd> [args...]`

## Roadmap + releases (project-scope only)

- `ph roadmap <show|create|validate>`
- `ph release <plan|draft|activate|clear|status|show|progress|add-feature|suggest|list|close|migrate-slot-format>`

Notes:

- `ph release close` runs a preflight and will block if slots/sprints are unfinished or release gate tasks are not done.

## Destructive operations

- `ph reset` (dry-run)
- `ph reset --confirm RESET --force true` (execute)
- `ph reset-smoke` (destructive to project scope)
