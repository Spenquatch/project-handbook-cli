---
title: PH Spec Contract — sprints/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/sprints/`
- Summary: Active sprint workspaces (by sprint id) plus a `sprints/current` pointer to the currently-open sprint.

## Ownership
- Owner: Shared.
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `YYYY/SPRINT-*/plan.md` body
  - `YYYY/SPRINT-*/tasks/**` task docs
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - `current` (directory link pointer)
- Overwrite rules:
  - The CLI MUST NOT overwrite an existing sprint directory or its `plan.md` without explicit `--force`.
- Mutability:
  - Human-edited: sprint `plan.md` content and task docs under `tasks/`.
  - CLI-managed: directory scaffolding and `sprints/current` pointer updates.

## Creation
- Created/updated by:
  - `ph sprint plan [--sprint SPRINT-...]` (creates a new sprint directory and seeds `plan.md`, updates `sprints/current`)
  - `ph sprint open --sprint SPRINT-...` (updates `sprints/current` pointer)
  - `pnpm make -- sprint-plan [sprint=SPRINT-...]` (creates a new sprint directory and seeds `plan.md`, updates `sprints/current`)
  - `pnpm make -- sprint-open sprint=SPRINT-...` (updates `sprints/current` pointer)
- Non-destructive: sprint scaffolding MUST NOT overwrite an existing sprint directory or its `plan.md` unless an explicit force mode is provided by the caller.

## Required Files and Directories
- Required directories:
  - `archive/`
- Required pointer:
  - `current` (MUST behave like a directory link to the current sprint directory, when present)
    - POSIX: symlink
    - Windows: directory junction (preferred) or symlink (if permitted)
    - If neither is possible, `ph sprint plan|open` MUST fail with remediation (see CLI contract).
- Sprint directory layout (canonical):
  - Date/ISO-week ids:
    - `YYYY/SPRINT-<...>/`
      - `plan.md`
      - `tasks/`
  - Sequence ids (legacy `id_scheme=sequence`):
    - `SEQ/SPRINT-SEQ-####/`
      - `plan.md`
      - `tasks/`

## Schemas
- `YYYY/SPRINT-*/plan.md` MUST be Markdown with YAML front matter containing at least:
  - `title: <string>`
  - `type: sprint-plan`
  - `date: YYYY-MM-DD`
  - `sprint: SPRINT-...` (matching the directory name)
  - `mode: bounded|timeboxed`
- Sprint plan front matter MAY include:
  - `tags: [sprint, planning, ...]`
  - `release: <string|null>`
  - `release_sprint_slot: <int|null>` (when using sprint-slot releases)
  - `start: YYYY-MM-DD` (required when `mode: timeboxed`)
  - `end: YYYY-MM-DD` (required when `mode: timeboxed`)

### Sprint plan release alignment section (required; deterministic markers)

Sprint plans MUST pull forward the active release slot goal and enablement so validation/status can deterministically detect misalignment.

Requirement trigger:
- If sprint plan front matter has `release` set to a non-null string AND `release_sprint_slot` set to an integer, the sprint plan body MUST include the alignment section below.

Alignment section format (exact headings/markers):
- The alignment section heading MUST match:
  - `^## Release Alignment \\(Slot [1-9][0-9]*\\)$`
  - The slot number in the heading MUST equal `release_sprint_slot`.
  - Example: `## Release Alignment (Slot 2)`
- Within the section, these markers MUST exist (case + punctuation sensitive):
  - A line that starts with: `Slot goal:`
  - A line that starts with: `Enablement:`
  - A line that is exactly: `Intended gates:`
    - Followed by at least one bullet list item that starts with `- Gate:` (case + punctuation sensitive).
- Task directories under `YYYY/SPRINT-*/tasks/` (created by `ph task create`) MUST have this shape:
  - `TASK-###-<slug>/`
    - `task.yaml`
    - `README.md`
    - `steps.md`
    - `commands.md`
    - `checklist.md`
    - `validation.md`
    - `references.md` (legacy; optional but commonly scaffolded)
    - `source/` (optional; for attachments/snippets; never executed by `ph`)
- `task.yaml` MUST be YAML and include at least (legacy tasks MAY omit `task_type`; see Task type taxonomy):
  - `id: TASK-###`
  - `title: <string>`
  - `feature: <string>`
  - `lane: <string|null>` (legacy)
  - `decision: <string>` (validated by `session`; see BL-0005)
  - `session: <string>` (legacy; e.g. `task-execution`, `research-discovery`; used for decision invariants)
  - `task_type: <string>` (BL-0007; optional for legacy tasks; see Task type taxonomy)
  - `owner: <string>`
  - `status: <string>`
  - `story_points: <int>`
  - `depends_on: [<TASK-###|FIRST_TASK>, ...]`
  - `prio: P0|P1|P2|P3|P4`
  - `due: YYYY-MM-DD`
  - `release: <vX.Y.Z | current | null>` (legacy)
  - `release_gate: <boolean>` (legacy)
  - `acceptance: [<string>, ...]`
  - `links: [<string>, ...]`
- For new tasks created by `ph` tooling, `task_type` MUST be present and MUST be one of the allowed values listed below.
- Task Markdown files (`README.md`, `steps.md`, `commands.md`, `checklist.md`, `validation.md`) MUST include YAML front matter with at least:
  - `title: <string>`
  - `type: task|implementation|commands|checklist|validation` (as appropriate)
  - `date: YYYY-MM-DD`
  - `task_id: TASK-###`
- YAML front matter MAY include additional keys; unknown keys MUST be preserved.

### Task type taxonomy (BL-0007)

This contract introduces a stable `task_type` taxonomy that is:
- explicit (finite allowed values),
- backwards compatible (legacy tasks can omit `task_type`),
- deterministically mappable to the legacy `session` field (used for BL-0005 decision invariants),
- tied to onboarding session templates (each `task_type` maps to a `session`, and `session` is the onboarding template key).

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
- `sprint-gate` (required per sprint; validates sprint goal + evidence and gates sprint close)
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

## Sprint Planning Mode Configuration (v1)

`ph sprint plan` MUST determine the sprint planning mode from the repo’s validation rules file:

- Config file: `PH_ROOT/process/checks/validation_rules.json`
- Config key: `sprint_management.mode`
- Allowed values:
  - `bounded` (v1 default; safe default)
  - `timeboxed` (explicit opt-in)

Defensive fallback (required):
- If `validation_rules.json` exists but omits `sprint_management` (or `sprint_management.mode` is missing/empty/invalid), tooling MUST treat the mode as `bounded` and generate a bounded sprint plan (`mode: bounded` with no required `start`/`end`).

## Invariants
- If `sprints/current` exists, it MUST resolve to an existing sprint directory.
- For date/ISO-week ids, the sprint directory year partition `YYYY/` MUST equal the year segment in the sprint id (`SPRINT-YYYY-...`).
- A sprint directory MUST contain:
  - `plan.md`
  - `tasks/` (may be empty)

## Validation Rules
- For every sprint directory `YYYY/SPRINT-*`:
  - `plan.md` MUST exist and satisfy the sprint-plan front matter requirements above
  - `tasks/` MUST exist (may be empty)
- If a sprint plan has `release` set (non-null) AND `release_sprint_slot` set (integer):
  - `plan.md` MUST include the “Release Alignment (Slot N)” section and markers defined above.
- If `sprints/current` exists, it MUST resolve to an existing sprint directory under `sprints/YYYY/SPRINT-*`.
- Task directories under `tasks/` MUST satisfy the task file + front matter requirements above.

### Sprint gate requirements (BL-0008; deterministic)

These rules make sprint close evidence-friendly and mechanically enforceable.

- For the active sprint resolved by `sprints/current`:
  - The sprint MUST contain **at least 1** task with `task_type: sprint-gate`.
  - Every `task_type: sprint-gate` task MUST have `status: done`.
  - Every `task_type: sprint-gate` task MUST satisfy the sprint-gate per-type doc rules above.
- Evidence convention (recommended; supports the deterministic markers above):
  - Prefer storing gate evidence under `status/evidence/<TASK-###>/` and referencing those paths from the gate task’s `validation.md`.
- `ph sprint close` MUST block by default if any of the above conditions are not met (see CLI contract for the `--force` override semantics).

### Task type lint/validate rules (BL-0007; deterministic markers)

These rules are designed to be implementable as literal string/heading checks (no NLP).

For all tasks:
- If `task_type` is present, it MUST be one of the allowed `task_type` values listed above.
- If `task_type` is missing, tooling MUST apply the defaulting rules above (based on `session`).
- `session` MUST be one of the allowed `session` values listed above.
- `task_type` MUST map to the required `session` value per the mapping table above.

Per-type doc rules:

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

### Decision workflow invariants (BL-0005)

Discovery tasks:
- If `task.yaml` has one of these session values:
  - `session: research-discovery`
  - `session: feature-research-planning`
  - `session: task-docs-deep-dive`
  - `decision` MUST be `DR-####` (4 digits)
  - The referenced DR MUST exist as exactly one Markdown file in one of:
    - `PH_ROOT/decision-register/DR-####-*.md`
    - `PH_ROOT/features/<feature>/decision-register/DR-####-*.md` (only for the task’s `feature`)

Execution tasks:
- If `task.yaml` has one of these session values:
  - `session: task-execution`
  - `session: sprint-gate`
  - `decision` MUST be either `ADR-####` (4 digits) or start with `FDR-`.
  - Referenced ADRs and FDRs MUST exist as docs and be uniquely resolvable:
    - ADR lookup:
      - `PH_ROOT/adr/NNNN-*.md` where `NNNN` is the ADR numeric segment
      - ADR front matter `id` MUST equal the task `decision` value
    - FDR lookup (feature-scoped):
      - `PH_ROOT/features/<feature>/fdr/NNNN-*.md` where `NNNN` is the trailing numeric segment of the FDR id
      - FDR front matter `id` MUST equal the task `decision` value

ADR/FDR backlink invariant:
- ADR and FDR docs MUST include a `links:` list with at least one repo-relative path to a `DR-####-*.md` file (see ADR/FDR contracts).

## Examples Mapping
- `examples/2026/SPRINT-2026-01-11/plan.md` demonstrates a valid sprint plan with bounded planning metadata.
- `examples/scaffold/2026/SPRINT-2026-01-11/plan.md` demonstrates the sprint plan scaffold shape generated by tooling.
