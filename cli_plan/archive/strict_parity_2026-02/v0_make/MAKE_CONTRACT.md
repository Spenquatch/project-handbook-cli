---
title: Current Make Interface Contract (v0)
type: contract
date: 2026-01-13
tags: [handbook, make, contract, automation]
links:
  - ../v1_cli/CLI_CONTRACT.md
  - ../PARITY_CHECKLIST.md
---

# Purpose

Define the authoritative behavior of the current **Make-based** interface so the new `ph` CLI can be validated for parity.

Reference implementation (real-world, pnpm-make driven):
- `/Users/spensermcconnell/__Active_Code/oss-saas/project-handbook`

This contract is exhaustive:
- full target inventory (including placeholders/no-ops),
- hook behavior (success and failure paths),
- skip rules and environment controls,
- per-command parameter requirements and side effects.

# Invocation

Supported invocations (equivalent):
- `make <target> [var=value ...]`
- `pnpm make -- <target> [var=value ...]`

Notes:
- `pnpm make -- ...` works because `package.json` defines `"make": "make"`.
- The system is designed to be run from the repo root. The CLI is expected to improve robustness when invoked from arbitrary subdirectories.

# Dispatcher model (outer/inner make)

The reference `Makefile` is a two-phase dispatcher controlled by `PH_INNER_MAKE`:

- Outer make (default): every goal routes to `__ph_dispatch`.
- Inner make (`PH_INNER_MAKE=1`): defines the actual target recipes.

Default goals:
- Inner make default: `help`
- Outer make default: `__ph_dispatch` (which runs `help` when no explicit goals are provided)

Help topic routing:
- `make help` prints the quick help.
- `make help <topic>` is implemented by mapping to `help-<topic>` inside the dispatcher (e.g. `make help sprint` → `help-sprint`).

Key outer-dispatch behaviors (contractual):
- If the inner make fails (non-zero exit), the post hook still runs in **history-only mode** (validation is skipped).
- On success, the post hook runs unless explicitly disabled via env var.

# Data root + internals

This Make interface is **project-root scoped only**:

- Data root is the repo root (`PH_ROOT`).
- Automation internals live under: `PH_ROOT/.project-handbook/`
  - `PH_ROOT/.project-handbook/history.log` (append-only)

# Target inventory (exhaustive)

This section enumerates the targets exposed via `PH_TARGETS` in the reference `Makefile`, plus “real but not in PH_TARGETS” targets that have recipes.

## Real targets (have recipes)

Help:
- `help`, `help-sprint`, `help-task`, `help-feature`, `help-release`, `help-backlog`, `help-parking`, `help-validation`, `help-utilities`

Daily:
- `daily`, `daily-force`, `daily-check`, `dashboard`

Sprint (project):
- `sprint-plan`, `sprint-open`, `sprint-status`, `sprint-tasks`, `burndown`, `sprint-close`, `sprint-capacity`, `sprint-archive`

Task (project):
- `task-create`, `task-list`, `task-show`, `task-status`

Feature (project):
- `feature-list`, `feature-create`, `feature-status`, `feature-update-status`, `feature-summary`, `feature-archive`

Backlog (project):
- `backlog-add`, `backlog-list`, `backlog-triage`, `backlog-assign`, `backlog-rubric`, `backlog-stats`

Parking lot (project):
- `parking-add`, `parking-list`, `parking-review`, `parking-promote`

Validation + status:
- `validate`, `validate-quick`, `pre-exec-lint`, `pre-exec-audit`, `status`, `check-all`, `test-system`

Release (project-scope-only):
- `release-plan`, `release-activate`, `release-clear`, `release-status`, `release-show`, `release-progress`
- `release-add-feature`, `release-suggest`, `release-list`, `release-close`

Roadmap (project-scope-only):
- `roadmap` (in `PH_TARGETS`)
- `roadmap-create`, `roadmap-validate` (not in `PH_TARGETS`, but still reachable via outer make’s `%: __ph_dispatch` rule)

Onboarding/session continuity:
- `onboarding`, `end-session`

Utilities:
- `clean`, `install-hooks`, `test-system`

## Composite targets (run via prerequisites)

- `check-all`: runs `validate` then `status`.

## Placeholder/no-op targets (exist, but do not execute work)

These exist only to support multi-goal patterns such as `make onboarding session <topic>`:

- `session` and all template topic names derived from `process/sessions/templates/*.md`
  - implemented as explicit no-op targets via:
    - `SESSION_TEMPLATES := $(patsubst %.md,%,$(notdir $(wildcard process/sessions/templates/*.md)))`
    - `.PHONY: session $(SESSION_TEMPLATES)`
    - `session $(SESSION_TEMPLATES):` then `@:` (no-op command)

Additionally, these are included in `PH_TARGETS` and marked phony, but have no explicit rules/recipes:
- `roadmap-show`
- `list`
- `continue-session`

Observed make behavior for these targets:
- inner make prints `Nothing to be done for '<target>'.`
- they are effectively placeholders only (they do not execute handbook logic)

Contract rule:
- The CLI must not reproduce “no-op placeholders”. It must model onboarding topics as arguments/subcommands.

# Hook behavior (history + validation)

## Post-make hook implementation

File: `../../process/automation/post_make_hook.py`

Behavior:
1. Append to `PH_ROOT/.project-handbook/history.log`:
   - `<timestamp> | <goals string>`
2. If validation is not skipped, run:
   - `python3 process/checks/validate_docs.py --quick --silent-success`

## Success path (outer dispatcher)

After a successful inner make:
- The outer dispatcher calls the post hook unless explicitly disabled.

Implementation details (must be preserved for parity):
- The dispatcher computes `SKIP_VALIDATE_FLAG` by checking if any goal is in: `validate validate-quick`.

## Failure path (outer dispatcher)

If the inner make fails (non-zero exit):
- The outer dispatcher still calls the post hook in history-only mode:
  - `python3 process/automation/post_make_hook.py --goals "<MAKECMDGOALS>" --skip-validate`

Net effect:
- failures are logged to history,
- failures do not auto-run validation.

## Validation skip rules (success path)

The dispatcher passes `--skip-validate` to the post hook if any goal is one of:
- `validate`, `validate-quick`

Meaning:
- validation targets still get history entries, but do not trigger a second validation pass.

## Hook control env var

- `PH_SKIP_POST_HOOK=1` skips the post hook entirely (success and failure paths).

# Parameter passing contract (Make variables)

Make variables are used as the primary parameter mechanism; targets forward these into Python flags.

Examples:
- `make task-create title="..." feature=... decision=... points=... owner=... prio=... lane=... session=...`
- `make feature-create name=... epic=true owner=@... stage=...`
- `make release-plan version=vX.Y.Z bump=patch sprints=3 sprint_ids="SPRINT-...,SPRINT-..."`
- `make backlog-add type=bug severity=P1 title="..." desc="..." owner=@...`
- `make pre-exec-audit sprint=SPRINT-... date=YYYY-MM-DD`

Missing required parameters typically cause:
- a printed `❌ Usage: ...` message,
- a non-zero exit.

## Variable schema by command

Sprint:
- `sprint-plan`: optional `sprint=<SPRINT-...>`
- `sprint-open`: required `sprint=<SPRINT-...>`
- `sprint-archive`: optional `sprint=<SPRINT-...>`

Task:
- `task-create`: required `title=... feature=... decision=...`
  - optional: `points=<int> owner=@... prio=P? lane=<string> session=<task-execution|research-discovery> release=<current|vX.Y.Z> gate=true`
- `task-show`: required `id=TASK-###`
- `task-status`: required `id=TASK-### status=<todo|doing|review|done|blocked>`
  - optional: `force=true`

Feature:
- `feature-create`: required `name=<feature>`
  - optional: `epic=true owner=@... stage=<stage>`
- `feature-status`: required `name=<feature> stage=<stage>`
- `feature-archive`: required `name=<feature>`
  - optional: `force=true`

Release (project scope only):
- `release-plan`: optional `version=<vX.Y.Z|next>`
  - optional: `bump=<patch|minor|major> sprints=<int> start=<SPRINT-...> sprint_ids="SPRINT-...,SPRINT-..."`
  - optional: `activate=true` (sets `releases/current` to this release after scaffolding)
- `release-activate`: required `release=<vX.Y.Z>`
- `release-clear`: no vars
- `release-add-feature`: required `release=<vX.Y.Z> feature=<feature>`
  - optional: `epic=true critical=true`
- `release-suggest`: required `version=<vX.Y.Z>`
- `release-close`: required `version=<vX.Y.Z>`

Pre-exec (project scope only):
- `pre-exec-lint`: no vars
- `pre-exec-audit`: optional `sprint=<SPRINT-...> date=<YYYY-MM-DD> evidence_dir=<path>`

Backlog:
- `backlog-add`: required `type=<bug|bugs|wildcards|work-items> title=... severity=<P0..P4>`
  - optional: `desc=... owner=@... impact=... workaround=...`
- `backlog-list`: optional `severity=<csv> category=<csv> format=<table|json>`
- `backlog-triage`: required `issue=<ID>`
- `backlog-assign`: required `issue=<ID>`
  - optional: `sprint=<current|next|SPRINT-...>`

Parking lot:
- `parking-add`: required `type=<features|technical-debt|research|external-requests> title=...`
  - optional: `desc=... owner=@... tags="<csv>"`
- `parking-list`: optional `category=<category> format=<table|json>`
- `parking-promote`: required `item=<ID>`
  - optional: `target=<now|next|later>` (defaults in script/Makefile)

# Command-to-script mapping (what each command does)

This section maps each command family to the underlying scripts and describes key side effects.

## Make-level guidance output (must be preserved for CLI parity)

Some commands print “next step” guidance at the Makefile layer (not in the Python scripts). The CLI MUST reproduce this guidance content (or provide equivalent structured hints) for parity.

`feature-create` prints:
```
Next steps for features/<name>/:
  1. Flesh out overview.md + status.md with owner, goals, and risks
  2. Draft architecture/implementation/testing docs before assigning sprint work
  3. Run 'make validate-quick' so docs stay lint-clean
```

`sprint-plan` prints:
```
Sprint scaffold ready:
  1. Edit sprints/current/plan.md with goals, lanes, and integration tasks
  2. Seed tasks via 'make task-create title=... feature=... decision=ADR-###'
  3. Re-run 'make sprint-status' to confirm health + next-up ordering
  4. Run 'make validate-quick' before handing off to another agent
  5. Need facilitation tips? 'make onboarding session sprint-planning'
```

`task-create` prints:
```
Next steps:
  - Open sprints/current/tasks/ for the new directory, update steps.md + commands.md
  - Set status to 'doing' when work starts and log progress in checklist.md
  - Run 'make validate-quick' once initial scaffolding is filled in
```

`release-plan` prints:
```
Release plan scaffold created under releases/<version>/plan.md
  - Assign features via 'make release-add-feature release=<version> feature=<name>'
  - Activate when ready via 'make release-activate release=<version>'
  - Confirm sprint alignment via 'make release-status' (requires an active release)
  - Run 'make validate-quick' before sharing externally
```

`sprint-close` prints:
```
Sprint closed! Next steps:
  1. Share the new retrospective and velocity summary
  2. Update roadmap/releases with completed scope
  3. Run 'make status' so status/current_summary.md reflects the close-out
  4. Kick off the next sprint via 'make sprint-plan' when ready
  5. Capture any loose ends inside parking lot or backlog
```

Notes:
- `roadmap-show`, `list`, and `continue-session` can appear in `MAKECMDGOALS` as placeholders; inner make may emit `Nothing to be done for '<target>'.` when these are present.
- The CLI MUST NOT replicate make’s placeholder targets nor the `Nothing to be done...` noise; it should model these as arguments/subcommands.

## Daily (project scope)

- `daily`: `python3 process/automation/daily_status_check.py --generate`
- `daily-force`: `python3 process/automation/daily_status_check.py --generate --force`
- `daily-check`: `python3 process/automation/daily_status_check.py --check-only --verbose`

Outputs (project):
- `status/daily/YYYY/MM/DD.md` (format and nesting controlled by `daily_status_check.py`)

## Validation

Project:
- `validate`: `python3 process/checks/validate_docs.py`
- `validate-quick`: `python3 process/checks/validate_docs.py --quick`

Outputs:
- `status/validation.json`

## Status

Project:
- `status`: `python3 process/automation/generate_project_status.py`
  - writes: `status/current.json`, `status/current_summary.md`
  - also updates feature status files via `process/automation/feature_status_updater.py`

## Dashboard

Project:
- `dashboard` prints sprint status, a best-effort listing of recent daily status files, and validation output.

Note:
- The daily-file listing uses a best-effort `ls status/daily/*.md` (or system equivalent) and may not match nested daily layouts. This is current behavior.

## Sprint

Project:
- `sprint-plan`: `python3 process/automation/sprint_manager.py --plan [--sprint <id>]`
- `sprint-open`: `python3 process/automation/sprint_manager.py --open --sprint <id>`
- `sprint-status`: `python3 process/automation/sprint_manager.py --status`
- `burndown`: `python3 process/automation/sprint_manager.py --burndown`
- `sprint-capacity`: `python3 process/automation/sprint_manager.py --capacity`
- `sprint-archive`: `python3 process/automation/sprint_manager.py --archive [--sprint <id>]`
- `sprint-close`: `python3 process/automation/sprint_manager.py --close`

Key outputs:
- `sprints/<year>/<sprint>/plan.md`, `sprints/current` symlink
- `sprints/<year>/<sprint>/retrospective.md` (on close)
- `sprints/<year>/<sprint>/burndown.md` (on burndown)
- `sprints/archive/**` and `sprints/archive/index.json` (on archive/close)

## Task

Project:
- `task-create` requires: `title`, `feature`, `decision`
- `task-show` requires: `id`
- `task-status` requires: `id`, `status`
- `task-list` has no required vars

Underlying script:
- `python3 process/automation/task_manager.py` with flags:
  - create: `--create --title ... --feature ... --decision ... [--points] [--owner] [--prio] [--lane] [--session]`
  - list: `--list`
  - show: `--show <id>`
  - status update: `--update-status <id> <status> [--force]`

Guardrail (project scope):
- none (lane is an arbitrary string in the reference Make implementation).

Outputs:
- `sprints/current/tasks/TASK-###-*/task.yaml` plus required task markdown files.

## Feature

Project:
- `feature-create` requires: `name`
- `feature-status` requires: `name`, `stage`
- `feature-archive` requires: `name`

Underlying script:
- `python3 process/automation/feature_manager.py` with flags:
  - list: `--list`
  - create: `--create <name> [--epic] [--owner <owner>] [--stage <stage>]`
  - update stage: `--update-status <name> <stage>`
  - archive: `--archive <name> [--force]`

Additional:
- `feature-update-status` and `feature-summary` call `process/automation/feature_status_updater.py`.

Guardrail (project scope):
- none (feature names are project-scoped in the reference Make implementation).

## Backlog

Project:
- `backlog-add` requires: `type`, `title`, `severity`
- `backlog-triage` requires: `issue`
- `backlog-assign` requires: `issue` (optional `sprint=current|<id>`)

Underlying script:
- `python3 process/automation/backlog_manager.py` subcommands:
  - add/list/triage/assign/rubric/stats

Outputs:
- `backlog/index.json`
- `backlog/<type>/<ID>/**`

## Parking lot

Project:
- `parking-add` requires: `type`, `title`
- `parking-promote` requires: `item`

Underlying script:
- `python3 process/automation/parking_lot_manager.py` subcommands:
  - add/list/review/promote

Outputs:
- `parking-lot/index.json`
- `parking-lot/<category>/<ID>/**`

## Roadmap (project-scope only)

- `roadmap`: `python3 process/automation/roadmap_manager.py --show`
- `roadmap-create`: `python3 process/automation/roadmap_manager.py --create`
- `roadmap-validate`: `python3 process/automation/roadmap_manager.py --validate`

Notes:
- `roadmap-show` exists as a no-op placeholder target (phony, no recipe).
- `roadmap-create` and `roadmap-validate` are supported targets even though they are not listed in `PH_TARGETS`.

## Release (project-scope only)

- `release-plan`: `python3 process/automation/release_manager.py --plan <version|next> ...`
- `release-activate`: `python3 process/automation/release_manager.py --set-current <vX.Y.Z>`
- `release-clear`: `python3 process/automation/release_manager.py --clear-current`
- `release-status`: `python3 process/automation/release_manager.py --status current`
- `release-show`: `python3 process/automation/release_manager.py --show current`
- `release-progress`: `python3 process/automation/release_manager.py --progress current`
- `release-add-feature`: `python3 process/automation/release_manager.py --add-feature <release> <feature> ...`
- `release-suggest`: `python3 process/automation/release_manager.py --suggest <version>`
- `release-list`: `python3 process/automation/release_manager.py --list`
- `release-close`: `python3 process/automation/release_manager.py --close <version>`

Contract rule:
- release targets are project-scope only (no system-scope variant exists in the reference Make interface).

## Pre-exec (project scope only)

- `pre-exec-lint`: `python3 process/checks/pre_exec_audit.py --mode lint`
- `pre-exec-audit`: `python3 process/checks/pre_exec_audit.py --mode audit [--sprint ...] [--date ...] [--evidence-dir ...]`

Evidence bundle default (when `evidence_dir` is not provided):
- `status/evidence/PRE-EXEC/<SPRINT-...>/<YYYY-MM-DD>/`

## Onboarding + end-session

- `onboarding`:
  - default: `python3 process/automation/onboarding.py`
  - session list: `make onboarding session list` → `onboarding.py --list`
  - session topic: `make onboarding session <topic>` → `onboarding.py --topic <topic>`

Important make behavior:
- `session` and `<topic>` appear in `MAKECMDGOALS` and are satisfied by no-op/phony targets to avoid make errors.
- `list` and `continue-session` are not template files, but they are included in `PH_TARGETS` and are therefore treated as phony placeholders (no recipe), avoiding errors.

- `end-session`:
  - runs `python3 process/automation/session_summary.py` with forwarded options:
    - `log`, `force`, `session_id`, `session_end_mode`, `session_end_codex`, `session_end_codex_model`, `skip_codex`

## Utilities

- `clean`:
  - deletes `*.pyc` files and `__pycache__` directories under repo root via `find`.

- `install-hooks`:
  - writes `.git/hooks/post-commit`:
    - runs `python3 process/automation/daily_status_check.py --check-only`
  - writes `.git/hooks/pre-push`:
    - runs `python3 process/checks/validate_docs.py`
  - makes both hook files executable.

- `test-system` (project scope only):
  - runs, in order:
    - `python3 process/checks/validate_docs.py`
    - `python3 process/automation/generate_project_status.py`
    - `python3 process/automation/daily_status_check.py --check-only --verbose` (allows expected “no daily status yet” case)
    - `python3 process/automation/sprint_manager.py --status`
    - `python3 process/automation/feature_manager.py --list`
    - `python3 process/automation/roadmap_manager.py --show`

# CLI parity expectations

The CLI (`cli_plan/v1_cli/`) MUST:
- preserve command semantics and “next step” hints where they exist today,
- centralize hooks (history + auto validate) with the same skip conditions,
- eliminate Make’s need for placeholder/no-op targets,
- reduce or eliminate cwd sensitivity by resolving root deterministically.
