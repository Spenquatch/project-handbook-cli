---
title: `ph` CLI Contract (Commands, Hints, Hooks)
type: contract
date: 2026-01-13
tags: [handbook, cli, contract, automation]
links:
  - ./ADR-CLI-0001-ph-cli-migration.md
  - ./ADR-CLI-0004-ph-root-layout.md
  - ./ADR-CLI-0006-adr-commands-and-validation.md
  - ../archive/strict_parity_2026-02/v0_make/MAKE_CONTRACT.md
  - ../archive/strict_parity_2026-02/PARITY_CHECKLIST.md
---

# Purpose

Define the authoritative `ph` CLI surface:

- command tree and exact flags,
- root resolution and data roots,
- pre/post hooks and skip rules,
- “hints” and guidance printed after commands (must preserve current ergonomics),
- destructive safety semantics (CLI-only maintenance utilities).

This contract is intended to be implementable with zero ambiguity.

# Global behavior

## Global flags (apply to every command)

- `--root <path>`: handbook root override (see Root resolution)
- `--no-post-hook`: disables centralized post-command hook entirely (history + validate)
- `--no-history`: disables history logging (still allows validation unless also skipped)
- `--no-validate`: disables auto-run of quick validation (still allows history unless also skipped)

## Root resolution

`ph` MUST resolve a single handbook root directory (`PH_ROOT`) for each invocation:

- If `--root <path>` is provided, use it (must be a directory that contains `.project-handbook/config.json`).
- Else, walk up from `cwd` until a directory contains `.project-handbook/config.json`.
- Else, exit non-zero with a message that includes an example `ph --root ...`.

All filesystem operations MUST use absolute paths derived from `PH_ROOT`.

Exception:
- `ph init` is allowed to run outside an existing `PH_ROOT` and uses `--root <path>` or `cwd` as its target directory.

## Path roots

Within `PH_ROOT`, `ph` MUST use two distinct roots:

- `PH_INTERNAL_ROOT = PH_ROOT/.project-handbook` (CLI-owned state/config + system-scope data; required)
- `PH_CONTENT_ROOT = PH_ROOT` (project handbook content root)

Contract path convention:

- Any path written as `.project-handbook/<...>` is relative to `PH_ROOT` (internal root).
- Any other relative path is relative to `PH_ROOT` (content root).
  - Example: `sprints/current/plan.md` means `PH_ROOT/sprints/current/plan.md`.

## Repository asset contract (required files)

For `PH_ROOT` to be considered a valid handbook repo root, this marker file MUST exist:

- `.project-handbook/config.json`

No other repo root marker is supported (no legacy compatibility, migration, or fallback markers).

For full CLI functionality (including post-command auto-validation and onboarding sessions), these paths MUST exist:

- `process/checks/validation_rules.json`
- `process/sessions/templates/` (directory)

If any are missing, `ph` MUST exit non-zero and print remediation that includes the missing path(s).

## Repository schema/version compatibility

`.project-handbook/config.json` MUST contain:

- `handbook_schema_version`: integer, MUST be `1`
- `requires_ph_version`: string, MUST be `>=0.0.1,<0.1.0`
- `repo_root`: string, MUST be `"."` (project repo root)

On every invocation, `ph` MUST:

1. Load `.project-handbook/config.json`.
2. Refuse to run if `handbook_schema_version != 1`.
3. Refuse to run if installed `ph` version does not satisfy `requires_ph_version`.
4. Print remediation including the exact command:
   - `uv tool install project-handbook`

### `ph init`

Command:
- `ph init`

Flags:
 - `--gitignore` / `--no-gitignore`
   - default: `--gitignore`

Behavior:
- Purpose: bootstrap a Project Handbook repo by creating the marker config, required process assets, and the canonical directory tree so other `ph` commands don’t assume pre-existing files.
- Root selection:
  - If `--root <path>` is provided, write under that directory.
  - Else, write under `cwd`.
- Create these paths if missing (do not overwrite existing files):
  - `.project-handbook/` (directory; includes `.gitkeep`)
  - `.project-handbook/config.json`
  - `ONBOARDING.md` (seeded)
  - `process/checks/validation_rules.json` (seeded; v1 default MUST include `sprint_management.mode = "bounded"`)
  - `process/automation/system_scope_config.json` (optional; routing prefixes and exclusions)
  - `process/automation/reset_spec.json` (CLI-only maintenance utility)
  - `process/AI_AGENT_START_HERE.md` (seeded; lightweight agent workflow guide)
  - `process/playbooks/` (directory; seeded with basic playbooks)
  - `process/sessions/templates/` (directory)
  - `process/sessions/logs/` (directory; includes `.gitkeep`)
  - `process/sessions/logs/latest_summary.md` (seeded placeholder)
  - `process/sessions/session_end/` (directory)
  - `process/sessions/session_end/session_end_index.json` (seeded; `{ "records": [] }`)
  - Content roots (repo-root layout):
    - `adr/`
    - `assets/` (includes `.gitkeep`)
    - `backlog/{bugs,wildcards,work-items}/` and `backlog/archive/{bugs,wildcards,work-items}/`
    - `backlog/index.json` (seeded; empty index)
    - `contracts/`
    - `decision-register/`
    - `docs/logs/` (includes `.gitkeep`; contents are ignored by validation rules by default)
    - `features/implemented/`
    - `parking-lot/index.json` (seeded; empty index)
    - `parking-lot/{features,technical-debt,research,external-requests}/` and `parking-lot/archive/{features,technical-debt,research,external-requests}/`
    - `releases/planning/` and `releases/delivered/`
    - `roadmap/` (seed file: `roadmap/now-next-later.md`)
    - `sprints/archive/`
    - `sprints/archive/index.json` (seeded; empty archive index)
    - `status/{daily,evidence,exports}/`
    - `tools/` (includes `.gitkeep`)

Notes:
- `ph init` is non-destructive and idempotent: it creates missing paths but never overwrites existing content.
- Domain commands MUST still be robust (create missing parent directories they own), so running `ph init` is recommended but not required.

Gitignore behavior:
- If `--gitignore` (default), `ph init` SHOULD update/create `PH_ROOT/.gitignore` idempotently with at least:
  - `.project-handbook/history.log`
  - `process/sessions/logs/*` and `!process/sessions/logs/.gitkeep`
  - `status/exports`
- If `--no-gitignore`, `ph init` MUST NOT read or write `PH_ROOT/.gitignore`.

Stdout:
- Always print exactly one line for the marker file:
  - On create: `Created: .project-handbook/config.json`
  - If already exists: `Already exists: .project-handbook/config.json`

Exit codes:
- `0` on success (created or already exists)
- `2` on failure to write (invalid path, permissions, etc.)

Hook notes:
- On success, MUST skip post-command hooks entirely (no history, no auto-validation).

### `ph doctor`

Command:
- `ph doctor`

Behavior:
- Print:
  - resolved `PH_ROOT`
  - configured `handbook_schema_version` and `requires_ph_version`
  - installed `ph` version
  - existence checks for every required repo asset path above
- Exit codes:
  - `0` if all checks pass
  - `2` if schema/version mismatch
  - `3` if required repo assets are missing

## Post-command hooks (default enabled)

`ph` MUST implement the same effective behavior as the current Make outer dispatcher + `process/automation/post_make_hook.py`, but centralized inside the CLI.

### Success path (exit code 0)

After a successful command, `ph` MUST:

1. Append history entry to: `PH_ROOT/.project-handbook/history.log`
   - format: `<timestamp> | <entry>`
   - `<timestamp>` format: `%Y-%m-%d %H:%M:%S`
   - `<entry>` MUST be a single-line string representing the user-visible command invocation (e.g. `ph sprint plan --sprint SPRINT-...`)
   - if the user invoked `ph` with no subcommand (default help), `<entry>` MUST be `(default)` (parity with `post_make_hook.py`)
2. Run quick validation:
   - validation is implemented inside `ph` (no subprocess to repo-local Python)
   - inputs:
     - rules: `PH_ROOT/process/checks/validation_rules.json`
     - root: selected by root resolution above
   - outputs:
     - `status/validation.json`
   - validation MUST NOT create a second history entry (it is an internal hook action)

Skip conditions for auto validation:

- command is `validate` (any mode)
- command is `reset` or `reset-smoke`
- user passed `--no-validate`

Skip conditions for history logging:

- user passed `--no-history`

Skip conditions for the post-command hook entirely (history + validation):

- user passed `--no-post-hook`
- environment variable `PH_SKIP_POST_HOOK=1` is set
- command is `reset` or `reset-smoke` (parity with Make: on success, these skip the post hook entirely)

### Failure path (exit code non-zero)

If the command fails, `ph` MUST still append a history entry (unless history or the post hook is disabled), and MUST NOT run validation (parity with Make’s `--skip-validate` failure path).

## Error behavior

- Any contract violation MUST exit non-zero and print remediation.

# Command tree

The CLI tree is grouped by domain. All commands accept the global flags above.

Notation:

- “Hints” are lines printed at the end of successful execution (in addition to the command’s main output).
- “Hook notes” describe pre/post hook behavior specific to the command.

## Removed Make placeholders (MUST NOT exist as `ph` commands)

The Make interface includes placeholder/no-op targets (`roadmap-show`, `list`, and multi-goal tokens like `session <topic>`) to satisfy `make` goal parsing.

The CLI MUST NOT expose these placeholders as commands. Instead:

- `make roadmap` / `make roadmap-show` → `ph roadmap show`
- `make onboarding session list` → `ph onboarding session list`
- `make onboarding session continue-session` → `ph onboarding session continue-session`
- `make onboarding session <template>` → `ph onboarding session <template>`

## `ph help`

### `ph help`

Behavior:
- Print top-level commands and short descriptions.

No hooks beyond normal history/validate behavior.

### `ph help <topic>`

Equivalent: `make help <topic>` routing (`help-<topic>` targets)

Topics (MUST exist for Make parity):
- `ph help sprint`
- `ph help task`
- `ph help feature`
- `ph help release`
- `ph help backlog`
- `ph help parking`
- `ph help validation`
- `ph help utilities`

Additional topics (MUST exist as CLI improvements):
- `ph help adr`
- `ph help roadmap`

Behavior:
- Print the subset of commands and a short synopsis matching the topic.

## `ph validate`

### `ph validate`

Equivalent: `make validate`

Behavior:
- Run full validation.
- Write report to: `status/validation.json`
- Validation MUST include strict ADR checks for `adr/*.md` (see `ph adr`).
- Validation MUST be able to deterministically detect release/sprint misalignment by looking for exact headings/markers in Markdown bodies:
  - Release plan slot sections:
    - For each `releases/vX.Y.Z/plan.md`, validate the presence and shape of slot sections as defined in `cli_plan/ph_spec/ph/releases/contract.md` (“Release plan slot sections”).
  - Sprint plan release alignment sections:
    - For each sprint plan with front matter `release` (non-null) and `release_sprint_slot` (integer), validate the presence and shape of the alignment section as defined in `cli_plan/ph_spec/ph/sprints/contract.md` (“Sprint plan release alignment section”).
    - If the referenced release plan is resolvable (e.g. `release: current` with a valid `releases/current` pointer, or `release: vX.Y.Z`), validation MUST confirm the release plan contains the corresponding `## Slot N: ...` section for `N = release_sprint_slot`.

Flags:
- `--quick` (equivalent to `make validate-quick`)
- `--silent-success`

Hook notes:
- Auto validation hook is skipped (to avoid recursion).
- History logging still occurs unless `--no-history`.

Hints (on success):
- `validation: 0 error(s), 0 warning(s), report: <path>`

## `ph pre-exec`

Equivalent: `make pre-exec-lint`, `make pre-exec-audit`

Commands:
- `ph pre-exec lint`
- `ph pre-exec audit [--sprint <SPRINT-...>] [--date <YYYY-MM-DD>] [--evidence-dir <path>]`

Behavior:
- `lint`:
  - Strict task-doc lint gate for the active sprint (session↔purpose alignment + ambiguity language detection).
  - Sprint gates (BL-0008):
    - MUST fail non-zero if the active sprint has **zero** tasks with `task_type: sprint-gate`.
    - For each `task_type: sprint-gate` task, MUST validate the deterministic gate-doc rules under “Task types (BL-0007)” and fail non-zero on any missing marker.
  - MUST fail non-zero if any blocking findings are present.
- `audit`:
  - Capture an evidence bundle (command outputs + validation report), then run `lint` and tee its output into the bundle.
  - Default evidence bundle location (when `--evidence-dir` is not provided):
    - `status/evidence/PRE-EXEC/<SPRINT-...>/<YYYY-MM-DD>/`

Hook notes:
- Normal post-command hook runs.

## `ph dashboard`

Equivalent: `make dashboard`

Behavior:
- Print sprint status + recent daily status + validation summary.

Hook notes:
- Normal post-command hook runs (history + validate-quick), unless `--no-validate`.

Hints (MUST match current Make UX):
- Print a banner matching the current Make targets:
  - `════════════════════════════════════════════════`
  - `           PROJECT HANDBOOK DASHBOARD           `
  - `════════════════════════════════════════════════`
- For `Recent Daily Status:`, list the last 3 lexicographically-sorted matches of `status/daily/*.md`; if none exist, print `  No daily status files yet`.

Dashboard parity note (current behavior to preserve):
- The “Recent Daily Status” listing is a best-effort glob of `status/daily/*.md` and may not reflect nested daily layouts.

## `ph status`

Equivalent: `make status`

Behavior:
- Generate status rollup:
  - write JSON: `status/current.json`
  - write markdown summary: `status/current_summary.md`
- Auto-update feature status files.

Hook notes:
- Normal post-command hook runs.

Hints (must match current ergonomics):
- Print the generated paths.
- If `current_summary.md` is non-empty, print its contents wrapped exactly as:
  - `===== status/current_summary.md =====` then the file contents then `====================================`

## `ph daily`

Equivalent: `make daily`, `make daily-force`, `make daily-check`

Commands:
- `ph daily generate` (default behavior, weekend-aware)
- `ph daily generate --force` (generate even on weekends)
- `ph daily check --verbose`

Behavior:
- Writes daily status under `status/daily/YYYY/MM/DD.md` per existing logic.

Hook notes:
- Normal post-command hook runs.

Hints:
- If a daily entry was created, print its path.

## `ph sprint`

Equivalent: `make sprint-*`

### `ph sprint plan [--sprint <id>] [--force]`

Behavior:
- Create sprint dir and plan template, then set `sprints/current` to point at that sprint directory:
  - POSIX: directory symlink
  - Windows: directory junction (preferred) or symlink (if permitted)
  - If a directory link cannot be created, command MUST fail with remediation (enable Developer Mode / run elevated / filesystem must support links).

Sprint planning mode (v1 default is bounded):
- The sprint plan template MUST be selected via `PH_ROOT/process/checks/validation_rules.json`:
  - Config key: `sprint_management.mode`
  - Allowed values: `bounded` (default), `timeboxed` (explicit opt-in)
- Defensive fallback:
  - If `validation_rules.json` exists but omits `sprint_management` (or `mode` is missing/empty/invalid), `ph sprint plan` MUST treat the mode as `bounded`.

Hints:
- MUST print exactly these lines:
  - `Sprint scaffold ready:`
  - `  1. Edit sprints/current/plan.md with goals, lanes, and integration tasks`
  - `  2. Seed tasks via 'ph task create --title ... --feature ... --decision ADR-###'`
  - `  3. Re-run 'ph sprint status' to confirm health + next-up ordering`
  - `  4. Run 'ph validate --quick' before handing off to another agent`
  - `  5. Need facilitation tips? 'ph onboarding session sprint-planning'`

### `ph sprint open --sprint <id>`

Behavior:
- Set `sprints/current` to point at an existing sprint directory:
  - POSIX: directory symlink
  - Windows: directory junction (preferred) or symlink (if permitted)
  - If a directory link cannot be created, command MUST fail with remediation (enable Developer Mode / run elevated / filesystem must support links).

Hints:
- `✅ Current sprint set to: <id>`

### `ph sprint status [--sprint <id|current>]`

Behavior:
- Show sprint status.
- MUST include a “Sprint gates” summary derived from tasks with `task_type: sprint-gate` (see “Task types (BL-0007)”):
  - If zero sprint-gate tasks exist: print a blocking finding (the sprint is not closeable by default).
  - Else: list each sprint-gate task id + status, and whether it passes the deterministic gate-doc rules.

Hints:
- Include “Tip” lines already present in sprint_manager output.

### `ph sprint tasks [--sprint <id|current>]`

Behavior:
- List sprint tasks.

### `ph sprint burndown [--sprint <id|current>]`

Behavior:
- Print burndown and write it under the sprint dir.

### `ph sprint close [--sprint <id|current>] [--force]`

Behavior:
- Create retrospective and archive sprint into `sprints/archive/...`.
- Rewrite `sprints/current/tasks/...` links to archived sprint paths.
- Sprint gates (BL-0008; close blocker by default):
  - The target sprint MUST contain **at least 1** task with `task_type: sprint-gate`.
  - Every `task_type: sprint-gate` task MUST have `status: done`.
  - Every `task_type: sprint-gate` task MUST satisfy the deterministic gate-doc rules under “Task types (BL-0007)”.
  - If any of the above checks fail and `--force` is **not** provided: command MUST fail non-zero and print remediation:
    - `Sprint close blocked: sprint gates missing/incomplete.`
    - `Run: ph sprint status`
    - `Override (not recommended): ph sprint close --force`
  - If `--force` is provided: command MUST still print the same findings as warnings, then proceed with close/archival.

Hints:
- MUST print the following block exactly (byte-for-byte), though additional deterministic guidance MAY be printed before it:
  - `Sprint closed! Next steps:`
  - `  1. Share the new retrospective and velocity summary`
  - `  2. Update roadmap/releases with completed scope`
  - `  3. Run 'ph status' so status/current_summary.md reflects the close-out`
  - `  4. Kick off the next sprint via 'ph sprint plan' when ready`
  - `  5. Capture any loose ends inside parking lot or backlog`
- SHOULD also print a deterministic pre/post checklist for operators (mirrors the sprint-closing playbook).
- MAY print: `Consider closing release: ph release close --version vX.Y.Z` when closing this sprint completes the final
  release slot/timeline item (non-interactive; hint only).

### `ph sprint capacity [--sprint <id|current>]`

Behavior:
- Print capacity/telemetry view.

### `ph sprint archive [--sprint <id>]`

Behavior:
- Archive the specified sprint.

## `ph task`

Equivalent: `make task-*`

### `ph task create --title <t> --feature <f> --decision <d> [--points N] [--owner @x] [--prio Px] [--lane <lane>] [--task-type <task_type>] [--session <name>]`

Behavior:
- Create a new task directory under `sprints/current/tasks/...` with required files.
- The created `task.yaml` MUST include both:
  - `session: <string>` (legacy; BL-0005 decision invariants)
  - `task_type: <string>` (BL-0007 task taxonomy)

Defaults:
- If `--task-type` is provided:
  - Tooling MUST set `session` deterministically from the mapping table under “Task types (BL-0007)”.
  - If `--session` is also provided, it MUST match the mapped `session` for the chosen `task_type` (else fail).
- Else, if `--task-type` is omitted and `--session` is provided:
  - Tooling MUST set `task_type` deterministically from `session`:
    - `session: task-execution` → `task_type: implementation`
    - `session: research-discovery` → `task_type: research-discovery`
- Else, if both `--task-type` and `--session` are omitted:
  - Tooling MUST default to `task_type: implementation` and `session: task-execution`.

Guardrails:
- Optional (opt-in) system-scope routing:
  - If `system_scope_enforcement.enabled` is `true` in `process/checks/validation_rules.json` and the provided
    `--lane` matches a configured system-scope lane prefix (from `process/automation/system_scope_config.json`),
    command MUST fail with remediation:
    - `Use: ph --scope system task create ...`
- If `--task-type` is provided, it MUST be one of the allowed `task_type` values under “Task types (BL-0007)”.
- If `--session` is provided, it MUST be one of: `task-execution`, `research-discovery`, `sprint-gate`, `feature-research-planning`, `task-docs-deep-dive`.
- Decision/session workflow invariants (BL-0005):
  - If `--session research-discovery`, then `--decision` MUST be `DR-####` (4 digits).
  - If `--session task-execution`, then `--decision` MUST be either:
    - `ADR-####` (4 digits), or
    - an FDR id starting with `FDR-` (see FDR conventions under `ph fdr add`).
  - For `DR-####` decisions, the referenced DR MUST exist (see “DR existence + lookup” below).

Hints:
- Print the task directory path.
- Print exactly:
  - `Next steps:`
  - `  - Open sprints/current/tasks/ for the new directory, update steps.md + commands.md`
  - `  - Set status to 'doing' when work starts and log progress in checklist.md`
  - `  - Run 'ph validate --quick' once initial scaffolding is filled in`

### Task types (BL-0007)

`task_type` provides explicit task taxonomy and deterministic, string-checkable doc requirements.

Relationship to onboarding session templates:
- `session` is the onboarding session template key.
- For every allowed `session` value, a same-named onboarding session template file MUST exist:
  - `process/sessions/templates/<session>.md`
- `task_type` MUST map deterministically to a required `session` value via the mapping table below.

Relationship to `session` (legacy, BL-0005):
- `task_type` is the primary taxonomy field.
- `session` exists to drive BL-0005 decision invariants (and is also the onboarding session template key).
- Tooling MUST enforce that `task_type` and `session` are consistent via the mapping table below.

Allowed `task_type` values (explicit list):
- `implementation` (default for legacy execution tasks)
- `research-discovery` (default for legacy discovery tasks)
- `sprint-gate`
- `feature-research-planning`
- `task-docs-deep-dive`

Defaulting when `task_type` is missing (legacy tasks):
- If `session: task-execution`, tooling MUST treat the task as `task_type: implementation`.
- If `session: research-discovery`, tooling MUST treat the task as `task_type: research-discovery`.

Allowed `session` values (explicit list; onboarding template keys, BL-0007):
- `task-execution`
- `research-discovery`
- `sprint-gate`
- `feature-research-planning`
- `task-docs-deep-dive`

Mapping table (`task_type` → required `session`):

| `task_type` | `session` |
|---|---|
| `implementation` | `task-execution` |
| `research-discovery` | `research-discovery` |
| `sprint-gate` | `sprint-gate` |
| `feature-research-planning` | `feature-research-planning` |
| `task-docs-deep-dive` | `task-docs-deep-dive` |

Deterministic per-type doc rules (string/heading checks):
- `task_type: sprint-gate`
  - `validation.md` MUST include the literal string: `Sprint Goal:`
  - `validation.md` MUST include the literal string: `Exit criteria:`
  - `validation.md` MUST mention the literal filename: `secret-scan.txt`
  - `validation.md` MUST mention the evidence root path prefix: `status/evidence/`
  - `task.yaml` MUST mention the evidence root path prefix: `status/evidence/`
  - `validation.md` MUST reference the sprint plan so the goal is traceable, by including **at least one** of these literal strings:
    - `sprints/current/plan.md`
    - `../../plan.md`
- `task_type: task-docs-deep-dive`
  - `steps.md` MUST NOT contain any of these words (case-insensitive, whole-word match): `implement`, `refactor`, `deploy`, `ship`
  - `validation.md` MUST NOT contain any of these words (case-insensitive, whole-word match): `implement`, `refactor`, `deploy`, `ship`
- `task_type: feature-research-planning`
  - `steps.md` MUST contain a heading line exactly: `## Contract updates`
  - `steps.md` MUST contain a heading line exactly: `## Execution tasks to create`

### `ph task list`

Behavior:
- List tasks in current sprint.

### `ph task show --id <TASK-###>`

Behavior:
- Print metadata and file locations.

### `ph task status --id <TASK-###> --status <todo|doing|review|done|blocked> [--force]`

Behavior:
- Update status with dependency checks (repo-local).

## Decision workflow invariants (BL-0005)

These rules make the discovery → decision → execution pipeline deterministic and enforceable by validation.

### Task decision invariants

- Discovery tasks are defined as tasks with one of these session values:
  - `session: research-discovery`
  - `session: feature-research-planning`
  - `session: task-docs-deep-dive`
  - These tasks MUST reference discovery-only decisions:
    - `decision: DR-####`
- Execution tasks are defined as tasks with one of these session values:
  - `session: task-execution`
  - `session: sprint-gate`
  - These tasks MUST reference execution decisions:
    - `decision: ADR-####`, or
    - `decision: FDR-...`

### ADR/FDR existence + lookup (validation rule)

When validating a task with an execution decision:

- `decision: ADR-####`
  - MUST resolve to exactly one ADR doc under:
    - `PH_ROOT/adr/NNNN-*.md` where `NNNN` is the numeric portion of the ADR id
  - The ADR doc front matter `id` MUST equal the task’s `decision` value.
- `decision: FDR-...-NNNN`
  - MUST resolve to exactly one FDR doc under:
    - `PH_ROOT/features/<feature>/fdr/NNNN-*.md` where `NNNN` is the trailing numeric segment of the FDR id
  - The FDR doc front matter `id` MUST equal the task’s `decision` value.

Outcomes (deterministic):
- If **zero** matches are found: **error** (`missing decision doc for <decision>`).
- If **more than one** match is found: **error** (`ambiguous decision id <decision>; multiple docs found`).

### DR existence + lookup (validation rule)

When validating a task with `decision: DR-####`, `ph validate` MUST confirm the referenced DR exists as exactly one Markdown file in one of these locations:

- Project-level decision register (always searched):
  - `PH_ROOT/decision-register/DR-####-*.md`
- Feature-level decision register (searched only when `task.yaml` has `feature: <feature>`):
  - `PH_ROOT/features/<feature>/decision-register/DR-####-*.md`

Outcomes (deterministic):
- If **zero** matches are found: **error** (`missing DR doc for DR-####`).
- If **more than one** match is found (including a project + feature duplicate): **error** (`ambiguous DR id DR-####; multiple DR docs found`).
- If **exactly one** match is found: success.

### ADR/FDR backlink invariant (validation rule)

For any ADR or FDR referenced by tasks, `ph validate` MUST enforce the ADR/FDR backlink rule defined under `ph adr add` / `ph fdr add`:

- ADR/FDR front matter MUST include a `links:` list containing at least one repo-relative path to a `DR-####-*.md` file.
  - Repo-relative means PH_ROOT-relative and normalized:
    - MUST NOT start with `./` or `../`
    - MUST NOT be an absolute path
    - MUST point to a `DR-####-*.md` file (not just `DR-####`)

## `ph feature`

Equivalent: `make feature-*`

### `ph feature create --name <name> [--epic] [--owner @x] [--stage <stage>]`

Hints:
- Print the created directory path.
- Print exactly:
  - `Next steps for features/<name>/:`
  - `  1. Flesh out overview.md + status.md with owner, goals, and risks`
  - `  2. Draft architecture/implementation/testing docs before assigning sprint work`
  - `  3. Run 'ph validate --quick' so docs stay lint-clean`

### `ph feature list`

Behavior:
- List features.

### `ph feature status --name <name> --stage <stage>`

Behavior:
- Update stage.

### `ph feature update-status`

Behavior:
- Recompute status.md files from sprint/task data.

### `ph feature summary`

Behavior:
- Print feature progress summary.

### `ph feature archive --name <name> [--force]`

Behavior:
- Completeness check, then move to `features/implemented/<name>/`.

## `ph dr`

### `ph dr add --id DR-#### --title <t> [--feature <name>] [--date YYYY-MM-DD]`

Behavior:
- Scaffold a new Decision Register (DR) entry and print its path.
- Target directory:
  - If `--feature` is omitted: write to `PH_ROOT/decision-register/`.
  - If `--feature <name>` is provided: write to `PH_ROOT/features/<name>/decision-register/` (create the directory if missing).
- Target filename MUST be: `DR-####-<slug>.md` where `<slug>` is derived from `--title` as lowercase kebab-case (same slug rules as `ph adr add`).
- The generated file MUST include YAML front matter with at least:
  - `title: DR-#### — <t>` (MUST include the same `DR-####` as `--id`)
  - `type: decision-register`
  - `date: YYYY-MM-DD` (default: today, local time)
  - `links: []` (optional; may be used for cross-linking)
- The generated body SHOULD follow the standard DR structure from the decision-register spec (Problem/Context, Options, Recommendation, Follow-ups).

Guardrails:
- `--id` MUST be exactly `DR-NNNN` where `NNNN` is 4 digits (`0000`–`9999`); otherwise fail non-zero with remediation.
- The CLI MUST refuse to create the DR if the target path already exists (non-destructive).

Internal-only escape hatch (MUST exist, MUST NOT appear in CLI help output):
- `--force`:
  - Non-destructive override only.
  - If the target DR file already exists, `ph dr add --force ...` MUST succeed without modifying the file (idempotent “already exists” success).

## `ph adr`

Rationale + conventions reference:
- `cli_plan/v1_cli/ADR-CLI-0006-adr-commands-and-validation.md`

### `ph adr add --id ADR-#### --title <t> --dr DR-#### [--dr DR-####] [--status draft] [--superseded-by ADR-####] [--date YYYY-MM-DD]`

Behavior:
- Create a new ADR markdown file under `PH_ROOT/adr/` and print its path.
- The target filename MUST be: `adr/NNNN-<slug>.md` where:
  - `NNNN` is the 4-digit numeric portion of `--id` (e.g. `ADR-0007` → `0007`).
  - `<slug>` is derived deterministically from `--title` as lowercase kebab-case:
    - lowercase,
    - non-alphanumeric characters replaced with `-`,
    - collapse consecutive `-`,
    - trim leading/trailing `-`,
    - truncate to 80 characters (then trim a trailing `-` if truncation produces one).
- The generated file MUST include YAML front matter with at least:
  - `id: ADR-NNNN` (MUST match filename numeric prefix)
  - `title: <t>`
  - `type: adr`
  - `status: draft|accepted|rejected|superseded` (default: `draft`)
  - `date: YYYY-MM-DD` (default: today, local time)
  - `links: [<dr_path>, ...]` (MUST include at least one DR backlink; see rule below)
  - If `status: superseded`, then `superseded_by: ADR-NNNN` (MUST reference an existing ADR id)
- The generated file body MUST include these H1 sections (exact spelling, H1 only):
  - `# Context`
  - `# Decision`
  - `# Consequences`
  - `# Acceptance Criteria`
  - `# Rollout` (recommended; see validation warnings below)

Guardrails:
- `--id` MUST be exactly `ADR-NNNN` where `NNNN` is 4 digits (`0000`–`9999`); otherwise fail non-zero with remediation.
- `--dr DR-####` MUST be provided at least once.
- Each `--dr DR-####` MUST resolve to exactly one existing DR markdown file path:
  - `decision-register/DR-####-*.md`, or
  - `features/*/decision-register/DR-####-*.md`
  - If zero or multiple matches are found, `ph adr add` MUST fail non-zero with remediation.
- The CLI MUST refuse to create the ADR if the target path already exists (non-destructive).
- If `--status superseded`, then `--superseded-by ADR-NNNN` MUST be provided and MUST reference an existing ADR in `adr/*.md`.

Internal-only escape hatch (MUST exist, MUST NOT appear in CLI help output):
- `--force`:
  - Non-destructive override only.
  - If the target ADR file already exists, `ph adr add --force ...` MUST succeed without modifying the file (idempotent “already exists” success).

## ADR conventions + validation (strict) (BL-0001)

Naming convention for `PH_ROOT/adr/`:
- ADR filenames MUST be `NNNN-<slug>.md` where `NNNN` is 4 digits and `<slug>` is lowercase kebab-case.
- ADR front matter `id` MUST be `ADR-NNNN` and MUST match the filename numeric prefix.
- ADR ids MUST be unique across `PH_ROOT/adr/*.md` (no duplicate `id: ADR-NNNN` across multiple files).
- If front matter `status: superseded`, front matter MUST include `superseded_by: ADR-NNNN` and `superseded_by` MUST reference an existing ADR in `PH_ROOT/adr/*.md`.

Validation requirements for ADR markdown files:
- Naming/id checks (**errors**):
  - filename matches `NNNN-<slug>.md`
  - front matter `id` exists and equals `ADR-NNNN` for the filename prefix
  - front matter `id` is not duplicated across multiple files
  - if `status: superseded`, then `superseded_by` exists and references an existing ADR
- DR backlink checks (**errors**) (BL-0005):
  - front matter `links` exists and is a YAML list
  - `links` MUST contain at least one DR backlink entry that is a repo-relative path (PH_ROOT-relative) to an existing DR markdown file:
    - `decision-register/DR-####-*.md`, or
    - `features/<feature>/decision-register/DR-####-*.md`
  - A DR backlink MUST be a path to a `DR-####-*.md` file (not just `DR-####`).
  - Backlink paths MUST be PH_ROOT-relative and normalized (no `./`, no `../`, no absolute paths).
- Required H1 headings (missing any is an **error**):
  - `# Context`
  - `# Decision`
  - `# Consequences`
  - `# Acceptance Criteria`
- Recommended H1 heading (missing is a **warning**):
  - `# Rollout`

Actionable validation output:
- Errors/warnings MUST include:
  - ADR file path,
  - what was expected vs what was found (e.g., `expected id ADR-0007, found ADR-0008`),
  - for heading checks: an explicit `missing:` list and a `found_h1:` list (in document order).

## `ph fdr`

### `ph fdr add --feature <name> --id FDR-... --title <t> --dr DR-#### [--date YYYY-MM-DD]`

Behavior:
- Scaffold a new Feature Decision Record (FDR) under the owning feature directory and print its path.
- Target directory:
  - `PH_ROOT/features/<name>/fdr/` (create the directory if missing).
- Target filename MUST be: `NNNN-<slug>.md` where:
  - `NNNN` is derived from the trailing 4-digit numeric segment of `--id`:
    - allowed: `FDR-NNNN` or `FDR-<slug>-NNNN`
  - `<slug>` is derived deterministically from `--title` as lowercase kebab-case (same slug rules as `ph adr add`).
- The generated file MUST include YAML front matter with at least:
  - `id: <FDR id>` (MUST start with `FDR-` and end with `-NNNN` matching the filename prefix)
  - `title: <t>`
  - `type: fdr`
  - `date: YYYY-MM-DD` (default: today, local time)
  - `links: [<dr_path>, ...]` (MUST include at least one DR backlink; see rule below)
- The generated body SHOULD include the same core sections as ADRs (Context/Decision/Consequences/Acceptance Criteria) unless the feature contract defines a more specific FDR template.

Guardrails:
- `--feature` MUST reference an existing feature directory under `features/<name>/` (or `ph fdr add` MUST fail with remediation to create the feature first).
- `--id` MUST start with `FDR-` and MUST end with `-NNNN` where `NNNN` is 4 digits; otherwise fail non-zero with remediation.
- `--dr DR-####` MUST be provided (at least one).
- Each `--dr DR-####` MUST resolve to exactly one existing DR markdown file path, using feature-aware lookup:
  - First search `features/<name>/decision-register/DR-####-*.md`
  - Then search `decision-register/DR-####-*.md`
  - If zero or multiple matches are found, `ph fdr add` MUST fail non-zero with remediation.

Validation requirements for FDR markdown files (BL-0005):
- The referenced DR backlink(s) MUST be present in front matter `links:` as repo-relative paths to DR markdown files (not ids).

## `ph backlog`

Equivalent: `make backlog-*`

Commands:
- `ph backlog add --type <bug|bugs|wildcards|work-items> --title <t> --severity <P0..P4> [--desc <d>] [--owner <o>] ...`
- `ph backlog list [--severity <...>] [--category <...>] [--format <...>]`
- `ph backlog triage --issue <ID>`
- `ph backlog assign --issue <ID> [--sprint current|<id>]`
- `ph backlog rubric`
- `ph backlog stats`

Behavior:
- Operate within the project handbook content root.

Hints:
- On `add`, MUST print exactly:
  - `Backlog entry created.`
  - `  - Run 'ph backlog triage --issue <ID>' for P0 analysis`
  - `  - Assign it into a sprint via 'ph backlog assign --issue <ID> --sprint current'`
  - `  - Re-run 'ph validate --quick' if files were edited manually`

Defaulting:
- If `--sprint` is omitted for `ph backlog assign`, it MUST default to `current` (parity with Make).

## `ph parking`

Equivalent: `make parking-*`

Commands:
- `ph parking add --type <features|technical-debt|research|external-requests> --title <t> [--desc <d>] [--owner <o>] [--tags <csv>]`
- `ph parking list [--category <...>] [--format <...>]`
- `ph parking review`
- `ph parking promote --item <ID> [--target now|next|later]`

Behavior:
- Operate within the project handbook content root.

Hints:
- On `add`, MUST print exactly:
  - `Parking lot updated → review via 'ph parking list' or 'ph parking review'`
  - `  - Capture owner/priority inside parking-lot/<type>/ entries if missing`
  - `  - Promote items with 'ph parking promote' once they graduate to roadmap`

Defaulting:
- If `--target` is omitted for `ph parking promote`, it MUST default to `later` (parity with Make).

## `ph onboarding`

Equivalent: `make onboarding`

Commands:
- `ph onboarding` (prints `ONBOARDING.md`)
- `ph onboarding session list`
- `ph onboarding session <topic>`

Behavior:
- Read session templates from `PH_ROOT/process/sessions/templates`.
- `session list` MUST include every template name derived from template filenames (without `.md`), plus special topics:
  - `continue-session` (prints the latest session summary)
  - `list` (alias of `session list`)

Hook notes:
- Normal post-command hook runs.

## `ph end-session`

Equivalent: `make end-session`

Behavior:
- Implement the same behavior as the v0 session summarizer, but inside the installed `ph` tool (no repo-local Python execution).
- This command is a behavioral port of:
  - `process/automation/session_summary.py`
  - `process/automation/rollout_parser.py`

Outputs (project scope only):
- Write a dated summary markdown file under `PH_ROOT/process/sessions/logs/`.
- Write/overwrite `PH_ROOT/process/sessions/logs/latest_summary.md`.
- Update `PH_ROOT/process/sessions/logs/manifest.json`.
- When `--session-end-mode` is not `none`, write session_end artifacts under `PH_ROOT/process/sessions/session_end/` and update `PH_ROOT/process/sessions/session_end/session_end_index.json`.

Flags (MUST match the existing script surface):
- `--log <path>`
- `--force`
- `--session-id <id>`
- `--session-end-mode <mode>`
- `--session-end-codex`
- `--session-end-codex-model <model>`
- `--skip-codex`

Hook notes:
- Normal post-command hook runs.

## `ph check-all`

Equivalent: `make check-all`

Command:
- `ph check-all`

Behavior:
- Run, in order:
  1. `ph validate` (full validation)
  2. `ph status`

Hook notes:
- Normal post-command hook runs once for the `check-all` command (do not double-run hooks for the internal steps).

## `ph test system`

Equivalent: `make test-system`

Command:
- `ph test system`

Behavior:
- Run, in order (matching Make):
  1. `ph validate`
  2. `ph status`
  3. `ph daily check --verbose`
  4. `ph sprint status`
  5. `ph feature list`
  6. `ph roadmap show`

Hook notes:
- Normal post-command hook runs once for the `test system` command (do not double-run hooks for the internal steps).

## `ph clean`

Equivalent: `make clean`

Behavior:
- Remove Python caches under `PH_ROOT`:
  - delete `*.pyc`
  - delete `__pycache__/` directories

Hook notes:
- Normal post-command hook runs.

## `ph hooks install`

Equivalent: `make install-hooks`

Behavior:
- Write `.git/hooks/post-commit` that runs:
  - `ph --no-post-hook daily check`
- Write `.git/hooks/pre-push` that runs:
  - `ph --no-post-hook validate`
- Mark both hooks executable.

Hook notes:
- Normal post-command hook runs.

## `ph roadmap`

Equivalent: `make roadmap`, `make roadmap-create`, `make roadmap-validate`

Commands:
- `ph roadmap` (alias of `ph roadmap show`)
- `ph roadmap show`
- `ph roadmap create`
- `ph roadmap validate`

Behavior:
- `ph` implements roadmap behavior directly (no subprocess to repo-local Python).

Files:
- Roadmap path: `roadmap/now-next-later.md`

`ph roadmap show`:
- If the roadmap file does not exist, exit non-zero and print:
  - `❌ No roadmap found. Run 'ph roadmap create' to create one.`
- Else, print an extracted view grouped by sections:
  - `## Now` → “NOW”
  - `## Next` → “NEXT”
  - `## Later` → “LATER”

`ph roadmap create`:
- Create `roadmap/now-next-later.md` if missing, with valid front matter and a starter template.

`ph roadmap validate`:
- Verify the roadmap file exists.
- Verify all markdown links that resolve to `PH_ROOT/**` exist on disk (relative links).
- Exit code: `0` if valid, `1` if invalid.

## `ph release`

Equivalent: `make release-*`

Commands:
- `ph release plan [--version <vX.Y.Z|next>] [--bump patch|minor|major] [--sprints N] [--start-sprint <SPRINT-...>] [--sprint-ids <csv>] [--activate]`
- `ph release activate --release <vX.Y.Z>`
- `ph release clear`
- `ph release status`
- `ph release show`
- `ph release progress`
- `ph release add-feature --release <vX.Y.Z> --feature <name> [--epic] [--critical]`
- `ph release suggest --version <vX.Y.Z>`
- `ph release list`
- `ph release close --version <vX.Y.Z>`

Hints:
- On `plan`, print exactly:
  - `Release plan scaffold created under releases/<version>/plan.md`
  - `  - Assign features via 'ph release add-feature --release <version> --feature <name>'`
  - `  - Activate when ready via 'ph release activate --release <version>'`
  - `  - Confirm sprint alignment via 'ph release status' (requires an active release)`
  - `  - Run 'ph validate --quick' before sharing externally`

Defaulting:
- If `--version` is omitted for `ph release plan`, it MUST default to `next` (parity with Make).

Implementation mapping (MUST match Make semantics):
- `ph` implements release behavior directly (no subprocess to repo-local Python).

Files:
- Releases root: `releases/`
- Versioned releases: `releases/vX.Y.Z/`
- Active release pointer: `releases/current` (symlink to a `releases/vX.Y.Z/` directory)
- Delivered releases directory: `releases/delivered/` (legacy-reserved; may exist but is not required for normal operation)

`ph release plan`:
- Ensure a version directory exists: `releases/<version>/`.
- Ensure these files exist (create if missing):
  - `releases/<version>/plan.md`
  - `releases/<version>/progress.md`
  - `releases/<version>/features.yaml`
- If `releases/<version>/plan.md` is created, it MUST include release slot sections in its body using the exact headings/markers defined in `cli_plan/ph_spec/ph/releases/contract.md` (“Release plan slot sections”), so `ph validate` can detect missing/malformed slots deterministically.
- If `--activate` is set, also set `releases/current` to point at `releases/<version>/`.

`ph release activate`:
- Set `releases/current` to point at `releases/<release>/` (must exist).

`ph release clear`:
- Remove `releases/current` if present.

`ph release list`:
- List every `releases/v*` directory (sorted by semantic version).
- Mark the active one via the `releases/current` symlink.

`ph release status`:
- Print a status view for the active release (`releases/current`).
- If `releases/current` is missing or invalid, exit non-zero with remediation.

`ph release show`:
- Print the active release plan (`releases/current/plan.md`) plus computed status.

`ph release progress`:
- Refresh (regenerate) `releases/current/progress.md`.

`ph release add-feature`:
- Update `releases/<release>/features.yaml` to include the referenced feature, preserving existing entries.

`ph release close`:
- Ensure `releases/<version>/changelog.md` exists (create/update).
- Update front matter in `releases/<version>/plan.md` to mark `status: delivered` and include delivered metadata:
  - `delivered_sprint: <current sprint id>`
  - `delivered_date: <YYYY-MM-DD>`
- `ph release close` MUST NOT move release directories by default (parity with the reference Make-era behavior).

## `ph reset`

Not in reference Makefile (CLI-only).

Modes:
- `ph reset` (dry-run only)
- `ph reset --confirm RESET --force true` (execute)

Behavior:
- Reset of project handbook content artifacts.
- MUST preserve `.project-handbook/**`.
- Writes rewritten templates (roadmap, index.json stubs) as per reset spec.

Hook notes:
- On success, MUST skip the post-command hook entirely (no history, no auto-validation) to avoid additional side effects during destructive maintenance.
- Must still be safe-by-default.

Hints:
- In dry-run, print delete set + “how to execute”.
- On execute, print `✅ Reset complete.`

## `ph reset-smoke`

Not in reference Makefile (CLI-only).

Behavior:
- Run the same deterministic smoke procedure currently documented in `docs/RESET_SMOKE.md`.

Hook notes:
- On success, MUST skip the post-command hook entirely (no history, no auto-validation), matching Make’s `reset` / `reset-smoke` skip behavior.

# Compatibility layer

Removed. v1 is the `ph` CLI only; do not keep a Make wrapper/compatibility layer.

# Make-to-CLI mapping (exhaustive)

This mapping exists only as a **migration reference** to translate legacy Make-era instructions into `ph` commands. v1 does not assume `make` remains present.

Help:
- `make help` → `ph help`
- `make help sprint` / `make help-sprint` → `ph help sprint`
- `make help task` / `make help-task` → `ph help task`
- `make help feature` / `make help-feature` → `ph help feature`
- `make help release` / `make help-release` → `ph help release`
- `make help backlog` / `make help-backlog` → `ph help backlog`
- `make help parking` / `make help-parking` → `ph help parking`
- `make help validation` / `make help-validation` → `ph help validation`
- `make help utilities` / `make help-utilities` → `ph help utilities`

Daily:
- `make daily` → `ph daily generate`
- `make daily-force` → `ph daily generate --force`
- `make daily-check` → `ph daily check --verbose`

Sprint (project):
- `make sprint-plan` → `ph sprint plan`
- `make sprint-open sprint=SPRINT-...` → `ph sprint open --sprint SPRINT-...`
- `make sprint-status` → `ph sprint status`
- `make sprint-tasks` → `ph sprint tasks`
- `make burndown` → `ph sprint burndown`
- `make sprint-capacity` → `ph sprint capacity`
- `make sprint-archive [sprint=SPRINT-...]` → `ph sprint archive [--sprint SPRINT-...]`
- `make sprint-close` → `ph sprint close`

Task (project):
- `make task-create ...` → `ph task create ...`
- `make task-list` → `ph task list`
- `make task-show id=TASK-###` → `ph task show --id TASK-###`
- `make task-status id=TASK-### status=doing [force=true]` → `ph task status --id TASK-### --status doing [--force]`

Feature (project):
- `make feature-list` → `ph feature list`
- `make feature-create name=<name>` → `ph feature create --name <name>`
- `make feature-status name=<name> stage=<stage>` → `ph feature status --name <name> --stage <stage>`
- `make feature-update-status` → `ph feature update-status`
- `make feature-summary` → `ph feature summary`
- `make feature-archive name=<name> [force=true]` → `ph feature archive --name <name> [--force]`

Backlog (project):
- `make backlog-add ...` → `ph backlog add ...`
- `make backlog-list ...` → `ph backlog list ...`
- `make backlog-triage issue=<ID>` → `ph backlog triage --issue <ID>`
- `make backlog-assign issue=<ID> [sprint=current]` → `ph backlog assign --issue <ID> [--sprint current]`
- `make backlog-rubric` → `ph backlog rubric`
- `make backlog-stats` → `ph backlog stats`

Parking (project):
- `make parking-add ...` → `ph parking add ...`
- `make parking-list ...` → `ph parking list ...`
- `make parking-review` → `ph parking review`
- `make parking-promote item=<ID> [target=later]` → `ph parking promote --item <ID> [--target later]`

Validation + status:
- `make validate` → `ph validate`
- `make validate-quick` → `ph validate --quick`
- `make pre-exec-lint` → `ph pre-exec lint`
- `make pre-exec-audit` → `ph pre-exec audit`
- `make status` → `ph status`

Dashboards:
- `make dashboard` → `ph dashboard`

Roadmap (project only):
- `make roadmap` → `ph roadmap show`
- `make roadmap-show` → `ph roadmap show`
- `make roadmap-create` → `ph roadmap create`
- `make roadmap-validate` → `ph roadmap validate`

Release (project only):
- `make release-plan ...` → `ph release plan ...`
- `make release-activate release=<vX.Y.Z>` → `ph release activate --release <vX.Y.Z>`
- `make release-clear` → `ph release clear`
- `make release-status` → `ph release status`
- `make release-show` → `ph release show`
- `make release-progress` → `ph release progress`
- `make release-add-feature ...` → `ph release add-feature ...`
- `make release-suggest version=<vX.Y.Z>` → `ph release suggest --version <vX.Y.Z>`
- `make release-list` → `ph release list`
- `make release-close version=<vX.Y.Z>` → `ph release close --version <vX.Y.Z>`

Onboarding + sessions:
- `make onboarding` → `ph onboarding`
- `make onboarding session list` → `ph onboarding session list`
- `make onboarding session continue-session` → `ph onboarding session continue-session`
- `make onboarding session <template>` → `ph onboarding session <template>`

Session summarization:
- `make end-session ...` → `ph end-session ...`

Utilities:
- `make clean` → `ph clean`
- `make install-hooks` → `ph hooks install`
- `make check-all` → `ph check-all`
- `make test-system` → `ph test system`

CLI-only (not in reference Makefile):
- `ph reset`
- `ph reset-smoke`
