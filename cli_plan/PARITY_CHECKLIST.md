---
title: CLI Plan – Parity Checklist (Make → ph)
type: checklist
date: 2026-01-14
tags: [cli, parity, make, checklist]
links:
  - ./v1_cli/CLI_CONTRACT.md
  - ./v0_make/MAKE_CONTRACT.md
  - ../Makefile
---

# CLI Parity Checklist (Make → `ph`)

This checklist is the **exhaustive parity verification** for the Make-to-CLI mapping defined in `cli_plan/v1_cli/CLI_CONTRACT.md` (“Make-to-CLI mapping (exhaustive)”).

## Conventions

- Prefer running against a disposable copy of the handbook repo.
- Use explicit root selection for determinism: `ph --root <PH_ROOT> ...`
- Output paths are **PH_ROOT-relative** (POSIX style).
- For system scope equivalents, replace project paths with `.project-handbook/system/**` as shown.

## Checklist (exhaustive)

### Help

- [ ] `make help` → `ph help`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> help`
  - Outputs to verify: (none; stdout only)
- [ ] `make help sprint` / `make help-sprint` → `ph help sprint`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> help sprint`
  - Outputs to verify: (none; stdout only)
- [ ] `make help task` / `make help-task` → `ph help task`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> help task`
  - Outputs to verify: (none; stdout only)
- [ ] `make help feature` / `make help-feature` → `ph help feature`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> help feature`
  - Outputs to verify: (none; stdout only)
- [ ] `make help release` / `make help-release` → `ph help release`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> help release`
  - Outputs to verify: (none; stdout only)
- [ ] `make help backlog` / `make help-backlog` → `ph help backlog`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> help backlog`
  - Outputs to verify: (none; stdout only)
- [ ] `make help parking` / `make help-parking` → `ph help parking`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> help parking`
  - Outputs to verify: (none; stdout only)
- [ ] `make help validation` / `make help-validation` → `ph help validation`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> help validation`
  - Outputs to verify: (none; stdout only)
- [ ] `make help utilities` / `make help-utilities` → `ph help utilities`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> help utilities`
  - Outputs to verify: (none; stdout only)

### Daily (project)

- [ ] `make daily` → `ph daily generate`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> daily generate`
  - Outputs to verify: `status/daily/YYYY/MM/DD.md`
- [ ] `make daily-force` → `ph daily generate --force`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> daily generate --force`
  - Outputs to verify: `status/daily/YYYY/MM/DD.md`
- [ ] `make daily-check` → `ph daily check --verbose`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> daily check --verbose`
  - Outputs to verify: (none; stdout only)

### Sprint (project)

- [ ] `make sprint-plan` → `ph sprint plan`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> sprint plan`
  - Outputs to verify: `sprints/<year>/<SPRINT-...>/plan.md`, `sprints/current`
- [ ] `make sprint-open sprint=SPRINT-...` → `ph sprint open --sprint SPRINT-...`
  - Preconditions: `sprints/<year>/<SPRINT-...>/` exists
  - Command: `ph --root <PH_ROOT> sprint open --sprint SPRINT-...`
  - Outputs to verify: `sprints/current`
- [ ] `make sprint-status` → `ph sprint status`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> sprint status`
  - Outputs to verify: (none; stdout only)
- [ ] `make sprint-tasks` → `ph sprint tasks`
  - Preconditions: `sprints/current` exists
  - Command: `ph --root <PH_ROOT> sprint tasks`
  - Outputs to verify: (none; stdout only)
- [ ] `make burndown` → `ph sprint burndown`
  - Preconditions: `sprints/current` exists
  - Command: `ph --root <PH_ROOT> sprint burndown`
  - Outputs to verify: `sprints/<year>/<SPRINT-...>/burndown.md`
- [ ] `make sprint-capacity` → `ph sprint capacity`
  - Preconditions: `sprints/current` exists
  - Command: `ph --root <PH_ROOT> sprint capacity`
  - Outputs to verify: (none; stdout only)
- [ ] `make sprint-archive [sprint=SPRINT-...]` → `ph sprint archive [--sprint SPRINT-...]`
  - Preconditions: sprint exists (`sprints/<year>/<SPRINT-...>/`)
  - Command: `ph --root <PH_ROOT> sprint archive [--sprint SPRINT-...]`
  - Outputs to verify: `sprints/archive/**`, `sprints/archive/index.json`
- [ ] `make sprint-close` → `ph sprint close`
  - Preconditions: `sprints/current` exists
  - Command: `ph --root <PH_ROOT> sprint close`
  - Outputs to verify: `sprints/<year>/<SPRINT-...>/retrospective.md`, `sprints/archive/**`, `sprints/archive/index.json`

### Sprint (system)

- [ ] `make hb-sprint-plan` → `ph --scope system sprint plan`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> --scope system sprint plan`
  - Outputs to verify: `.project-handbook/system/sprints/<year>/<SPRINT-...>/plan.md`, `.project-handbook/system/sprints/current`
- [ ] `make hb-sprint-open sprint=SPRINT-...` → `ph --scope system sprint open --sprint SPRINT-...`
  - Preconditions: `.project-handbook/system/sprints/<year>/<SPRINT-...>/` exists
  - Command: `ph --root <PH_ROOT> --scope system sprint open --sprint SPRINT-...`
  - Outputs to verify: `.project-handbook/system/sprints/current`
- [ ] `make hb-sprint-status` → `ph --scope system sprint status`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> --scope system sprint status`
  - Outputs to verify: (none; stdout only)
- [ ] `make hb-sprint-tasks` → `ph --scope system sprint tasks`
  - Preconditions: `.project-handbook/system/sprints/current` exists
  - Command: `ph --root <PH_ROOT> --scope system sprint tasks`
  - Outputs to verify: (none; stdout only)
- [ ] `make hb-burndown` → `ph --scope system sprint burndown`
  - Preconditions: `.project-handbook/system/sprints/current` exists
  - Command: `ph --root <PH_ROOT> --scope system sprint burndown`
  - Outputs to verify: `.project-handbook/system/sprints/<year>/<SPRINT-...>/burndown.md`
- [ ] `make hb-sprint-capacity` → `ph --scope system sprint capacity`
  - Preconditions: `.project-handbook/system/sprints/current` exists
  - Command: `ph --root <PH_ROOT> --scope system sprint capacity`
  - Outputs to verify: (none; stdout only)
- [ ] `make hb-sprint-archive [sprint=SPRINT-...]` → `ph --scope system sprint archive [--sprint SPRINT-...]`
  - Preconditions: system sprint exists (`.project-handbook/system/sprints/<year>/<SPRINT-...>/`)
  - Command: `ph --root <PH_ROOT> --scope system sprint archive [--sprint SPRINT-...]`
  - Outputs to verify: `.project-handbook/system/sprints/archive/**`, `.project-handbook/system/sprints/archive/index.json`
- [ ] `make hb-sprint-close` → `ph --scope system sprint close`
  - Preconditions: `.project-handbook/system/sprints/current` exists
  - Command: `ph --root <PH_ROOT> --scope system sprint close`
  - Outputs to verify: `.project-handbook/system/sprints/<year>/<SPRINT-...>/retrospective.md`, `.project-handbook/system/sprints/archive/**`, `.project-handbook/system/sprints/archive/index.json`

### Task (project)

- [ ] `make task-create ...` → `ph task create ...`
  - Preconditions: `sprints/current` exists; referenced feature exists; lane must not start with `handbook/`
  - Command: `ph --root <PH_ROOT> task create --title "..." --feature <name> --decision ADR-0000 --points 1 --lane ops --session task-execution`
  - Outputs to verify: `sprints/current/tasks/TASK-###-*/task.yaml` (and other task files under the same directory)
- [ ] `make task-list` → `ph task list`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> task list`
  - Outputs to verify: (none; stdout only)
- [ ] `make task-show id=TASK-###` → `ph task show --id TASK-###`
  - Preconditions: `sprints/**/tasks/TASK-###-*/` exists
  - Command: `ph --root <PH_ROOT> task show --id TASK-###`
  - Outputs to verify: (none; stdout only)
- [ ] `make task-status id=TASK-### status=doing [force=true]` → `ph task status --id TASK-### --status doing [--force]`
  - Preconditions: `sprints/**/tasks/TASK-###-*/task.yaml` exists
  - Command: `ph --root <PH_ROOT> task status --id TASK-### --status doing [--force]`
  - Outputs to verify: `sprints/**/tasks/TASK-###-*/task.yaml`

### Task (system)

- [ ] `make hb-task-create ...` → `ph --scope system task create ...`
  - Preconditions: `.project-handbook/system/sprints/current` exists
  - Command: `ph --root <PH_ROOT> --scope system task create --title "..." --feature <name> --decision ADR-0000 --points 1 --lane handbook/automation --session task-execution`
  - Outputs to verify: `.project-handbook/system/sprints/current/tasks/TASK-###-*/task.yaml` (and other task files under the same directory)
- [ ] `make hb-task-list` → `ph --scope system task list`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> --scope system task list`
  - Outputs to verify: (none; stdout only)
- [ ] `make hb-task-show id=TASK-###` → `ph --scope system task show --id TASK-###`
  - Preconditions: `.project-handbook/system/sprints/**/tasks/TASK-###-*/` exists
  - Command: `ph --root <PH_ROOT> --scope system task show --id TASK-###`
  - Outputs to verify: (none; stdout only)
- [ ] `make hb-task-status id=TASK-### status=doing [force=true]` → `ph --scope system task status --id TASK-### --status doing [--force]`
  - Preconditions: `.project-handbook/system/sprints/**/tasks/TASK-###-*/task.yaml` exists
  - Command: `ph --root <PH_ROOT> --scope system task status --id TASK-### --status doing [--force]`
  - Outputs to verify: `.project-handbook/system/sprints/**/tasks/TASK-###-*/task.yaml`

### Feature (project)

- [ ] `make feature-list` → `ph feature list`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> feature list`
  - Outputs to verify: (none; stdout only)
- [ ] `make feature-create name=<name>` → `ph feature create --name <name>`
  - Preconditions: feature name must not start with `handbook-` or `ph-`
  - Command: `ph --root <PH_ROOT> feature create --name <name>`
  - Outputs to verify: `features/<name>/`
- [ ] `make feature-status name=<name> stage=<stage>` → `ph feature status --name <name> --stage <stage>`
  - Preconditions: `features/<name>/` exists
  - Command: `ph --root <PH_ROOT> feature status --name <name> --stage <stage>`
  - Outputs to verify: `features/<name>/overview.md` (front matter/status fields updated)
- [ ] `make feature-update-status` → `ph feature update-status`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> feature update-status`
  - Outputs to verify: `features/**/status.md` (and/or other feature status artifacts written by updater)
- [ ] `make feature-summary` → `ph feature summary`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> feature summary`
  - Outputs to verify: (none; stdout only)
- [ ] `make feature-archive name=<name> [force=true]` → `ph feature archive --name <name> [--force]`
  - Preconditions: `features/<name>/` exists
  - Command: `ph --root <PH_ROOT> feature archive --name <name> [--force]`
  - Outputs to verify: `features/implemented/<name>/`

### Feature (system)

- [ ] `make hb-feature-list` → `ph --scope system feature list`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> --scope system feature list`
  - Outputs to verify: (none; stdout only)
- [ ] `make hb-feature-create name=<name>` → `ph --scope system feature create --name <name>`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> --scope system feature create --name <name>`
  - Outputs to verify: `.project-handbook/system/features/<name>/`
- [ ] `make hb-feature-status name=<name> stage=<stage>` → `ph --scope system feature status --name <name> --stage <stage>`
  - Preconditions: `.project-handbook/system/features/<name>/` exists
  - Command: `ph --root <PH_ROOT> --scope system feature status --name <name> --stage <stage>`
  - Outputs to verify: `.project-handbook/system/features/<name>/overview.md` (front matter/status fields updated)
- [ ] `make hb-feature-update-status` → `ph --scope system feature update-status`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> --scope system feature update-status`
  - Outputs to verify: `.project-handbook/system/features/**/status.md` (and/or other feature status artifacts written by updater)
- [ ] `make hb-feature-summary` → `ph --scope system feature summary`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> --scope system feature summary`
  - Outputs to verify: (none; stdout only)
- [ ] `make hb-feature-archive name=<name> [force=true]` → `ph --scope system feature archive --name <name> [--force]`
  - Preconditions: `.project-handbook/system/features/<name>/` exists
  - Command: `ph --root <PH_ROOT> --scope system feature archive --name <name> [--force]`
  - Outputs to verify: `.project-handbook/system/features/implemented/<name>/`

### Backlog (project)

- [ ] `make backlog-add ...` → `ph backlog add ...`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> backlog add --type bugs --title \"...\" --severity P2`
  - Outputs to verify: `backlog/index.json`, `backlog/<type>/<ID>/**`
- [ ] `make backlog-list ...` → `ph backlog list ...`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> backlog list ...`
  - Outputs to verify: (none; stdout only)
- [ ] `make backlog-triage issue=<ID>` → `ph backlog triage --issue <ID>`
  - Preconditions: `backlog/<type>/<ID>/` exists
  - Command: `ph --root <PH_ROOT> backlog triage --issue <ID>`
  - Outputs to verify: `backlog/index.json`, `backlog/<type>/<ID>/**` (triage metadata updated)
- [ ] `make backlog-assign issue=<ID> [sprint=current]` → `ph backlog assign --issue <ID> [--sprint current]`
  - Preconditions: `backlog/<type>/<ID>/` exists
  - Command: `ph --root <PH_ROOT> backlog assign --issue <ID> [--sprint current]`
  - Outputs to verify: `backlog/index.json`, `backlog/<type>/<ID>/**` (assignment metadata updated)
- [ ] `make backlog-rubric` → `ph backlog rubric`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> backlog rubric`
  - Outputs to verify: (none; stdout only)
- [ ] `make backlog-stats` → `ph backlog stats`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> backlog stats`
  - Outputs to verify: (none; stdout only)

### Backlog (system)

- [ ] `make hb-backlog-add ...` → `ph --scope system backlog add ...`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> --scope system backlog add --type bugs --title \"...\" --severity P2`
  - Outputs to verify: `.project-handbook/system/backlog/index.json`, `.project-handbook/system/backlog/<type>/<ID>/**`
- [ ] `make hb-backlog-list ...` → `ph --scope system backlog list ...`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> --scope system backlog list ...`
  - Outputs to verify: (none; stdout only)
- [ ] `make hb-backlog-triage issue=<ID>` → `ph --scope system backlog triage --issue <ID>`
  - Preconditions: `.project-handbook/system/backlog/<type>/<ID>/` exists
  - Command: `ph --root <PH_ROOT> --scope system backlog triage --issue <ID>`
  - Outputs to verify: `.project-handbook/system/backlog/index.json`, `.project-handbook/system/backlog/<type>/<ID>/**` (triage metadata updated)
- [ ] `make hb-backlog-assign issue=<ID> [sprint=current]` → `ph --scope system backlog assign --issue <ID> [--sprint current]`
  - Preconditions: `.project-handbook/system/backlog/<type>/<ID>/` exists
  - Command: `ph --root <PH_ROOT> --scope system backlog assign --issue <ID> [--sprint current]`
  - Outputs to verify: `.project-handbook/system/backlog/index.json`, `.project-handbook/system/backlog/<type>/<ID>/**` (assignment metadata updated)
- [ ] `make hb-backlog-rubric` → `ph --scope system backlog rubric`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> --scope system backlog rubric`
  - Outputs to verify: (none; stdout only)
- [ ] `make hb-backlog-stats` → `ph --scope system backlog stats`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> --scope system backlog stats`
  - Outputs to verify: (none; stdout only)

### Parking (project)

- [ ] `make parking-add ...` → `ph parking add ...`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> parking add --type technical-debt --title \"...\"`
  - Outputs to verify: `parking-lot/index.json`, `parking-lot/<category>/<ID>/**`
- [ ] `make parking-list ...` → `ph parking list ...`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> parking list ...`
  - Outputs to verify: (none; stdout only)
- [ ] `make parking-review` → `ph parking review`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> parking review`
  - Outputs to verify: (none; stdout only)
- [ ] `make parking-promote item=<ID> [target=later]` → `ph parking promote --item <ID> [--target later]`
  - Preconditions: `parking-lot/<category>/<ID>/` exists
  - Command: `ph --root <PH_ROOT> parking promote --item <ID> [--target later]`
  - Outputs to verify: `parking-lot/index.json`, `parking-lot/<category>/<ID>/**` (promotion metadata updated)

### Parking (system)

- [ ] `make hb-parking-add ...` → `ph --scope system parking add ...`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> --scope system parking add --type technical-debt --title \"...\"`
  - Outputs to verify: `.project-handbook/system/parking-lot/index.json`, `.project-handbook/system/parking-lot/<category>/<ID>/**`
- [ ] `make hb-parking-list ...` → `ph --scope system parking list ...`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> --scope system parking list ...`
  - Outputs to verify: (none; stdout only)
- [ ] `make hb-parking-review` → `ph --scope system parking review`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> --scope system parking review`
  - Outputs to verify: (none; stdout only)
- [ ] `make hb-parking-promote item=<ID> [target=later]` → `ph --scope system parking promote --item <ID> [--target later]`
  - Preconditions: `.project-handbook/system/parking-lot/<category>/<ID>/` exists
  - Command: `ph --root <PH_ROOT> --scope system parking promote --item <ID> [--target later]`
  - Outputs to verify: `.project-handbook/system/parking-lot/index.json`, `.project-handbook/system/parking-lot/<category>/<ID>/**` (promotion metadata updated)

### Validation + status

- [ ] `make validate` → `ph validate`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> validate`
  - Outputs to verify: `status/validation.json`
- [ ] `make validate-quick` → `ph validate --quick`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> validate --quick`
  - Outputs to verify: `status/validation.json`
- [ ] `make status` → `ph status`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> status`
  - Outputs to verify: `status/current.json`, `status/current_summary.md`
- [ ] `make hb-validate` → `ph --scope system validate`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> --scope system validate`
  - Outputs to verify: `.project-handbook/system/status/validation.json`
- [ ] `make hb-validate-quick` → `ph --scope system validate --quick`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> --scope system validate --quick`
  - Outputs to verify: `.project-handbook/system/status/validation.json`
- [ ] `make hb-status` → `ph --scope system status`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> --scope system status`
  - Outputs to verify: `.project-handbook/system/status/current.json`, `.project-handbook/system/status/current_summary.md`

### Dashboards

- [ ] `make dashboard` → `ph dashboard`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> dashboard`
  - Outputs to verify: (none; stdout only)
- [ ] `make hb-dashboard` → `ph --scope system dashboard`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> --scope system dashboard`
  - Outputs to verify: (none; stdout only)

### Roadmap (project only)

- [ ] `make roadmap` → `ph roadmap show`
  - Preconditions: `roadmap/now-next-later.md` exists (or create it first)
  - Command: `ph --root <PH_ROOT> roadmap show`
  - Outputs to verify: (none; stdout only)
- [ ] `make roadmap-show` → `ph roadmap show`
  - Preconditions: `roadmap/now-next-later.md` exists (or create it first)
  - Command: `ph --root <PH_ROOT> roadmap show`
  - Outputs to verify: (none; stdout only)
- [ ] `make roadmap-create` → `ph roadmap create`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> roadmap create`
  - Outputs to verify: `roadmap/now-next-later.md`
- [ ] `make roadmap-validate` → `ph roadmap validate`
  - Preconditions: `roadmap/now-next-later.md` exists
  - Command: `ph --root <PH_ROOT> roadmap validate`
  - Outputs to verify: (none; stdout only)

### Release (project only)

- [ ] `make release-plan ...` → `ph release plan ...`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> release plan [--version next] ...`
  - Outputs to verify: `releases/<version>/plan.md`, `releases/<version>/progress.md`, `releases/<version>/features.yaml`, `releases/current`
- [ ] `make release-status` → `ph release status`
  - Preconditions: `releases/current` exists and points at a valid `releases/<version>/`
  - Command: `ph --root <PH_ROOT> release status`
  - Outputs to verify: (none; stdout only)
- [ ] `make release-add-feature ...` → `ph release add-feature ...`
  - Preconditions: `releases/<version>/features.yaml` exists (created by `ph release plan`)
  - Command: `ph --root <PH_ROOT> release add-feature --release <vX.Y.Z> --feature <name> ...`
  - Outputs to verify: `releases/<version>/features.yaml`
- [ ] `make release-suggest version=<vX.Y.Z>` → `ph release suggest --version <vX.Y.Z>`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> release suggest --version <vX.Y.Z>`
  - Outputs to verify: (none; stdout only)
- [ ] `make release-list` → `ph release list`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> release list`
  - Outputs to verify: (none; stdout only)
- [ ] `make release-close version=<vX.Y.Z>` → `ph release close --version <vX.Y.Z>`
  - Preconditions: `releases/<version>/` exists
  - Command: `ph --root <PH_ROOT> release close --version <vX.Y.Z>`
  - Outputs to verify: `releases/<version>/plan.md`, `releases/<version>/changelog.md`

### Onboarding + sessions

- [ ] `make onboarding` → `ph onboarding`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> onboarding`
  - Outputs to verify: (none; stdout only)
- [ ] `make onboarding session list` → `ph onboarding session list`
  - Preconditions: `process/sessions/templates/*.md` exists
  - Command: `ph --root <PH_ROOT> onboarding session list`
  - Outputs to verify: (none; stdout only)
- [ ] `make onboarding session continue-session` → `ph onboarding session continue-session`
  - Preconditions: `process/sessions/logs/latest_summary.md` exists (or has been created by `ph end-session`)
  - Command: `ph --root <PH_ROOT> onboarding session continue-session`
  - Outputs to verify: (none; stdout only)
- [ ] `make onboarding session <template>` → `ph onboarding session <template>`
  - Preconditions: `process/sessions/templates/<template>.md` exists
  - Command: `ph --root <PH_ROOT> onboarding session <template>`
  - Outputs to verify: (none; stdout only)

### Session summarization

- [ ] `make end-session ...` → `ph end-session ...`
  - Preconditions: rollout log exists at `--log <path>`
  - Command: `ph --root <PH_ROOT> end-session --log <rollout.jsonl> [--skip-codex] ...`
  - Outputs to verify:
    - `process/sessions/logs/<YYYY-MM-DD_HHMM>_summary.md`
    - `process/sessions/logs/latest_summary.md`
    - `process/sessions/logs/manifest.json`
    - `process/sessions/session_end/session_end_index.json` (when `--session-end-mode` is not `none`)
    - `process/sessions/session_end/<workstream>/*` (when `--session-end-mode` is not `none`)

### Utilities

- [ ] `make clean` → `ph clean`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> clean`
  - Outputs to verify: (none; deletes `**/__pycache__/**` and `**/*.pyc` under PH_ROOT)
- [ ] `make install-hooks` → `ph hooks install`
  - Preconditions: `.git/` exists
  - Command: `ph --root <PH_ROOT> hooks install`
  - Outputs to verify: `.git/hooks/post-commit`, `.git/hooks/pre-push`
- [ ] `make check-all` → `ph check-all`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> check-all`
  - Outputs to verify: `status/validation.json`, `status/current.json`, `status/current_summary.md`
- [ ] `make test-system` → `ph test system`
  - Preconditions: none
  - Command: `ph --root <PH_ROOT> test system`
  - Outputs to verify: `status/validation.json`, `status/current.json`, `status/current_summary.md` (written by internal `ph validate` + `ph status`)

### Destructive

- [ ] `make reset` → `ph reset`
  - Preconditions: none (dry-run)
  - Command: `ph --root <PH_ROOT> reset`
  - Outputs to verify: (none; dry-run prints delete set)
- [ ] `make reset confirm=RESET force=true` → `ph reset --confirm RESET --force true`
  - Preconditions: run on disposable copy of the repo
  - Command: `ph --root <PH_ROOT> reset --confirm RESET --force true`
  - Outputs to verify: `roadmap/now-next-later.md`, `backlog/index.json`, `parking-lot/index.json` (and project artifacts removed per spec; system artifacts preserved)
- [ ] `make reset-smoke` → `ph reset-smoke`
  - Preconditions: run on disposable copy of the repo (destructive to project scope)
  - Command: `ph --root <PH_ROOT> reset-smoke`
  - Outputs to verify: (procedure asserts filesystem conditions; see `docs/RESET_SMOKE.md`)

