---
title: CLI Plan – Session Logs
type: log
date: 2026-01-14
tags: [cli, plan, execution, logs]
links:
  - ./tasks_v1_parity.json
  - ./archive/tasks_legacy.json
  - ./AI_AGENT_START_HERE.md
  - ./v1_cli/ADR-CLI-0001-ph-cli-migration.md
  - ./v1_cli/CLI_CONTRACT.md
---

# CLI Plan – Session Logs

Every execution session MUST append exactly one entry below, and MUST reference a single task ID from the active task queue (`cli_plan/tasks_v1_parity.json` during strict parity work).

Note: Some older entries describe a deprecated `.ph/**` + `ph/**` layout. The current v1 layout is defined by `cli_plan/v1_cli/ADR-CLI-0004-ph-root-layout.md` (repo-root content; marker `project_handbook.config.json`; internals under `.project-handbook/**`).

Note: Older entries may reference `cli_plan/tasks.json`; that file is now archived as `cli_plan/archive/tasks_legacy.json`.

## Entry template (copy/paste)

```markdown
## YYYY-MM-DD HH:MM <timezone> — <TASK_ID> — <short title>

Agent:
Environment:
Handbook instance repo:
CLI repo:

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks_v1_parity.json (task <TASK_ID>)

Goal:

Work performed (ordered):
1.
2.
3.

Commands executed (exact):
- <command>

Files changed (exact paths):
- <path>

Verification:
- <how verified, commands + outputs>

Outcome:
- status: done | blocked
- summary:

Next task:
- <NEXT_TASK_ID>

Blockers (if blocked):
- <concrete blocker, what is needed to unblock>
```

---

## 2026-01-14 00:00 UTC — TEMPLATE — Example placeholder

Agent:
Environment:
Handbook instance repo:
CLI repo:

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task TEMPLATE)

Goal:

Work performed (ordered):
1.

Commands executed (exact):
- (none)

Files changed (exact paths):
- (none)

Verification:
- (none)

Outcome:
- status: done
- summary: Initialized log file.

Next task:
- CLI-0001

## 2026-01-14 14:31 UTC — CLI-0001 — Create project-handbook-cli repository

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0001)

Goal:
- Create the external `project-handbook-cli` repo and add the required README statements.

Work performed (ordered):
1. Created the external GitHub repo `Spenquatch/project-handbook-cli` and cloned it locally.
2. Added `README.md` with the required contract statements.
3. Committed and pushed `main` to the canonical remote.

Commands executed (exact):
- gh repo create project-handbook-cli --public --clone --description "Installed ph CLI for Project Handbook"
- git add README.md
- git commit -m "Initial commit: README"
- git push -u origin main
- make validate-quick

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/README.md

Verification:
- make validate-quick
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: Created and pushed `Spenquatch/project-handbook-cli` with a contract README.

Next task:
- CLI-0002

Blockers (if blocked):
- (none)

## 2026-01-18 00:22 UTC — DD-0129 — Complete spec contract for sprints/archive/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0129)
- cli_plan/ph_spec/ph/sprints/archive/contract.md
- cli_plan/ph_spec/ph/sprints/archive/examples/**

Goal:
- Complete and validate the contract for `ph/sprints/archive/`.

Work performed (ordered):
1. Reviewed the existing `sprints/archive/` contract stub and the included example fixtures.
2. Cross-checked v1 `ph sprint close` / `ph sprint archive` behavior in the CLI contract to ensure the archive contract matches expected side effects.
3. Completed the archive contract by specifying `index.json` constraints, sprint artifact front matter requirements, invariants, validation rules, and examples mapping.

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- cat cli_plan/ph_spec/ph/sprints/archive/contract.md
- ls -la cli_plan/ph_spec/ph/sprints/archive/examples && find cli_plan/ph_spec/ph/sprints/archive/examples -maxdepth 3 -type f -print
- sed -n '1,200p' cli_plan/ph_spec/ph/sprints/archive/examples/index.json && echo '---' && sed -n '1,200p' cli_plan/ph_spec/ph/sprints/archive/examples/2026/SPRINT-2026-01-09/plan.md && echo '---' && sed -n '1,200p' cli_plan/ph_spec/ph/sprints/archive/examples/2026/SPRINT-2026-01-09/burndown.md && echo '---' && sed -n '1,240p' cli_plan/ph_spec/ph/sprints/archive/examples/2026/SPRINT-2026-01-09/retrospective.md
- sed -n '330,470p' cli_plan/v1_cli/CLI_CONTRACT.md
- sed -n '120,170p' cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- rg -n '\\(TBD\\)|TBD' cli_plan/ph_spec/ph/sprints/archive/contract.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/sprints/archive/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the examples mapping matches the included fixtures.

Outcome:
- status: done
- summary: Completed the `ph/sprints/archive/` directory contract and reconciled it against the included example fixtures and v1 CLI contract expectations.

Next task:
- DD-0130

Blockers (if blocked):
- (none)

## 2026-01-18 00:33 UTC — DD-0130 — Complete spec contract for sprints/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0130)
- cli_plan/ph_spec/ph/sprints/contract.md
- cli_plan/ph_spec/ph/sprints/examples/**

Goal:
- Complete and validate the contract for `ph/sprints/`.

Work performed (ordered):
1. Reviewed the existing `sprints/` contract stub and the included sprint plan example fixtures.
2. Cross-checked v1 sprint behaviors (`plan`/`open`/`close`/`archive`) to ensure the `current` pointer semantics are captured.
3. Completed the contract by specifying sprint plan front matter, task directory expectations, invariants, validation rules, and examples mapping.

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,260p' cli_plan/ph_spec/ph/sprints/contract.md
- ls -la cli_plan/ph_spec/ph/sprints/examples && find cli_plan/ph_spec/ph/sprints/examples -maxdepth 3 -type f -print
- sed -n '1,260p' cli_plan/ph_spec/ph/sprints/examples/2026/SPRINT-2026-01-11/plan.md
- sed -n '1,140p' cli_plan/ph_spec/ph/sprints/examples/scaffold/2026/SPRINT-2026-01-11/plan.md
- rg -n '\\(TBD\\)|TBD' cli_plan/ph_spec/ph/sprints/contract.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/sprints/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the examples mapping matches the included fixtures.

Outcome:
- status: done
- summary: Completed the `ph/sprints/` directory contract and reconciled it against the included example fixtures.

Next task:
- DD-0131

Blockers (if blocked):
- (none)

## 2026-01-18 00:35 UTC — DD-0131 — Complete spec contract for status/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0131)
- cli_plan/ph_spec/ph/status/contract.md
- cli_plan/ph_spec/ph/status/examples/**

Goal:
- Complete and validate the contract for `ph/status/`.

Work performed (ordered):
1. Reviewed the status contract stub and the included example fixtures (`README.md`, `current.json`, `validation.json`, `current_summary.md.example`).
2. Cross-checked the v1 CLI behaviors for `ph status`, `ph validate`, and the front matter exemption rules for `status/current_summary.md`.
3. Completed the contract by specifying required subdirectories, derived artifacts, schemas, invariants, validation rules, and examples mapping.

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,260p' cli_plan/ph_spec/ph/status/contract.md
- ls -la cli_plan/ph_spec/ph/status/examples && find cli_plan/ph_spec/ph/status/examples -maxdepth 3 -type f -print | head -n 50
- sed -n '1,120p' cli_plan/ph_spec/ph/status/examples/README.md && echo '---' && cat cli_plan/ph_spec/ph/status/examples/current.json && echo '---' && cat cli_plan/ph_spec/ph/status/examples/validation.json && echo '---' && sed -n '1,220p' cli_plan/ph_spec/ph/status/examples/current_summary.md.example
- sed -n '1,260p' src/ph/status.py
- rg -n 'status/current_summary\\.md' src/ph/validate_docs.py
- rg -n '\\(TBD\\)|TBD' cli_plan/ph_spec/ph/status/contract.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/status/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the examples mapping matches the included fixtures.

Outcome:
- status: done
- summary: Completed the `ph/status/` directory contract and reconciled it against the included example fixtures and the current v1 CLI behavior.

Next task:
- DD-0132

Blockers (if blocked):
- (none)

## 2026-01-18 00:37 UTC — DD-0132 — Complete spec contract for status/daily/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0132)
- cli_plan/ph_spec/ph/status/daily/contract.md
- cli_plan/ph_spec/ph/status/daily/examples/**

Goal:
- Complete and validate the contract for `ph/status/daily/`.

Work performed (ordered):
1. Reviewed the daily status contract stub and the included daily example fixture.
2. Cross-checked the v1 CLI contract for `ph daily generate` pathing and weekend-aware behavior.
3. Completed the contract by specifying path pattern, required front matter keys, invariants, validation rules, and examples mapping.

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,260p' cli_plan/ph_spec/ph/status/daily/contract.md
- ls -la cli_plan/ph_spec/ph/status/daily/examples && find cli_plan/ph_spec/ph/status/daily/examples -maxdepth 4 -type f -print | head -n 50
- sed -n '1,260p' cli_plan/ph_spec/ph/status/daily/examples/2026/01/03.md
- sed -n '330,430p' cli_plan/v1_cli/CLI_CONTRACT.md
- rg -n '\\(TBD\\)|TBD' cli_plan/ph_spec/ph/status/daily/contract.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/status/daily/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the examples mapping matches the included fixture.

Outcome:
- status: done
- summary: Completed the `ph/status/daily/` directory contract and reconciled it against the included example fixture and v1 CLI contract expectations.

Next task:
- DD-0133

Blockers (if blocked):
- (none)

## 2026-01-18 00:38 UTC — DD-0133 — Complete spec contract for status/evidence/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0133)
- cli_plan/ph_spec/ph/status/evidence/contract.md
- cli_plan/ph_spec/ph/status/evidence/examples/**

Goal:
- Complete and validate the contract for `ph/status/evidence/`.

Work performed (ordered):
1. Reviewed the evidence contract stub and the included example evidence bundle directory.
2. Captured recommended (non-enforced) structure patterns for per-task evidence directories and index files.
3. Completed the contract by specifying purpose, creation/ownership rules, invariants (no secrets), validation guidance, and examples mapping.

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,260p' cli_plan/ph_spec/ph/status/evidence/contract.md
- ls -la cli_plan/ph_spec/ph/status/evidence/examples && find cli_plan/ph_spec/ph/status/evidence/examples -maxdepth 3 -type f -print | head -n 50
- ls -la cli_plan/ph_spec/ph/status/evidence/examples/TASK-002 && sed -n '1,120p' cli_plan/ph_spec/ph/status/evidence/examples/TASK-002/index.md
- rg -n '\\(TBD\\)|TBD' cli_plan/ph_spec/ph/status/evidence/contract.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/status/evidence/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the examples mapping matches the included fixture bundle.

Outcome:
- status: done
- summary: Completed the `ph/status/evidence/` directory contract and reconciled it against the included example evidence bundle.

Next task:
- DD-0134

Blockers (if blocked):
- (none)

## 2026-01-18 00:39 UTC — DD-0134 — Complete spec contract for status/exports/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0134)
- cli_plan/ph_spec/ph/status/exports/contract.md
- cli_plan/ph_spec/ph/status/exports/examples/**

Goal:
- Complete and validate the contract for `ph/status/exports/`.

Work performed (ordered):
1. Reviewed the exports contract stub and the included example export bundle artifacts.
2. Defined a stable export bundle grouping convention (tarball + checksum + paths + manifest + README) that matches the examples.
3. Completed the contract by specifying required file formats, invariants, validation guidance, and examples mapping.

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,260p' cli_plan/ph_spec/ph/status/exports/contract.md
- ls -la cli_plan/ph_spec/ph/status/exports/examples && find cli_plan/ph_spec/ph/status/exports/examples -maxdepth 4 -type f -print | head -n 50
- sed -n '1,120p' cli_plan/ph_spec/ph/status/exports/examples/SPRINT-2026-01-11-doc-review.README.txt && echo '---' && sed -n '1,200p' cli_plan/ph_spec/ph/status/exports/examples/SPRINT-2026-01-11-doc-review.manifest.txt && echo '---' && cat cli_plan/ph_spec/ph/status/exports/examples/SPRINT-2026-01-11-doc-review.tar.gz.sha256 && echo '---' && sed -n '1,80p' cli_plan/ph_spec/ph/status/exports/examples/SPRINT-2026-01-11-doc-review.paths.txt
- rg -n '\\(TBD\\)|TBD' cli_plan/ph_spec/ph/status/exports/contract.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/status/exports/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the examples mapping matches the included bundle fixtures.

Outcome:
- status: done
- summary: Completed the `ph/status/exports/` directory contract and reconciled it against the included example export bundle artifacts.

Next task:
- NONE

Blockers (if blocked):
- (none)

## 2026-01-17 23:44 UTC — DD-0128 — Complete spec contract for roadmap/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0128)
- cli_plan/ph_spec/ph/roadmap/contract.md
- cli_plan/ph_spec/ph/roadmap/examples/**

Goal:
- Complete and validate the contract for `ph/roadmap/`.

Work performed (ordered):
1. Reviewed the roadmap contract stub, example fixture, and v1 `ph roadmap` contract surface.
2. Completed the roadmap contract with required file, heading requirements, and command mapping (`show/create/validate`).
3. Mapped the existing roadmap example fixture to the contract.

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,240p' cli_plan/ph_spec/ph/roadmap/contract.md
- ls -la cli_plan/ph_spec/ph/roadmap/examples && find cli_plan/ph_spec/ph/roadmap/examples -maxdepth 2 -type f -print -exec sed -n '1,200p' {} \;
- sed -n '656,690p' cli_plan/v1_cli/CLI_CONTRACT.md
- rg -n "\\(TBD\\)|TBD" cli_plan/ph_spec/ph/roadmap/contract.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/roadmap/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the example fixture demonstrates the required front matter and headings.

Outcome:
- status: done
- summary: Completed the `ph/roadmap/` directory contract and reconciled it against the included example fixture and v1 CLI contract.

Next task:
- DD-0129

Blockers (if blocked):
- (none)

## 2026-01-17 23:43 UTC — DD-0127 — Complete spec contract for releases/planning/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0127)
- cli_plan/ph_spec/ph/releases/planning/contract.md
- cli_plan/ph_spec/ph/releases/planning/examples/**

Goal:
- Complete and validate the contract for `ph/releases/planning/`.

Work performed (ordered):
1. Reviewed the releases/planning contract stub, example fixture, and v1 release contract notes.
2. Completed the planning contract with minimal schema guidance and explicit “not used by v1 commands” invariants.
3. Mapped the existing example fixture to the contract.

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,240p' cli_plan/ph_spec/ph/releases/planning/contract.md
- ls -la cli_plan/ph_spec/ph/releases/planning/examples && find cli_plan/ph_spec/ph/releases/planning/examples -maxdepth 3 -type f -print -exec sed -n '1,80p' {} \;
- rg -n "releases/planning" cli_plan/v1_cli/CLI_CONTRACT.md
- rg -n "\\(TBD\\)|TBD" cli_plan/ph_spec/ph/releases/planning/contract.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/releases/planning/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the example release summary fixture is referenced in Examples Mapping.

Outcome:
- status: done
- summary: Completed the `ph/releases/planning/` directory contract and reconciled it against the included example fixture and v1 release contract notes.

Next task:
- DD-0128

Blockers (if blocked):
- (none)

## 2026-01-17 23:41 UTC — DD-0126 — Complete spec contract for releases/delivered/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0126)
- cli_plan/ph_spec/ph/releases/delivered/contract.md
- legacy-reference/project-handbook/releases/v*/** (reference only)

Goal:
- Complete and validate the contract for `ph/releases/delivered/`.

Work performed (ordered):
1. Reviewed the delivered release contract stub and legacy delivered release artifacts for schema reference.
2. Completed the delivered contract schemas and validation expectations (delivered metadata and immutability).
3. Reconciled the delivered example fixture to include `changelog.md` and `status: delivered`.

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,320p' cli_plan/ph_spec/ph/releases/delivered/contract.md
- ls -la cli_plan/ph_spec/ph/releases/delivered/examples && find cli_plan/ph_spec/ph/releases/delivered/examples -maxdepth 4 -type f -print -exec sed -n '1,80p' {} \;
- ls -la legacy-reference/project-handbook/releases | head
- sed -n '1,40p' legacy-reference/project-handbook/releases/v0.5.0/changelog.md
- rg -n "\\(TBD\\)|TBD" cli_plan/ph_spec/ph/releases/delivered/contract.md || true
- ls -la cli_plan/ph_spec/ph/releases/delivered/examples/v0.5.1 && rg -n "^status:" cli_plan/ph_spec/ph/releases/delivered/examples/v0.5.1/plan.md && rg -n "^type:|^version:" cli_plan/ph_spec/ph/releases/delivered/examples/v0.5.1/changelog.md
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/releases/delivered/contract.md
- cli_plan/ph_spec/ph/releases/delivered/examples/v0.5.1/changelog.md
- cli_plan/ph_spec/ph/releases/delivered/examples/v0.5.1/plan.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the delivered example fixture contains `changelog.md` plus `status: delivered` with delivered metadata fields.

Outcome:
- status: done
- summary: Completed the `ph/releases/delivered/` directory contract and reconciled the delivered example fixture to match delivered semantics.

Next task:
- DD-0127

Blockers (if blocked):
- (none)

## 2026-01-17 23:39 UTC — DD-0125 — Complete spec contract for releases/current/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0125)
- cli_plan/ph_spec/ph/releases/current/contract.md
- cli_plan/ph_spec/ph/releases/examples/v0.5.1/**

Goal:
- Complete and validate the contract for `ph/releases/current/`.

Work performed (ordered):
1. Reviewed the v1 `ph release` contract and the existing active-release example fixture under `releases/current/examples/`.
2. Completed the `ph/releases/current/` contract with concrete `plan.md`, `progress.md`, `features.yaml`, and `changelog.md` schema requirements.
3. Added invariants and validation expectations for sprint metadata and version consistency.

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,260p' cli_plan/ph_spec/ph/releases/current/contract.md
- find cli_plan/ph_spec/ph/releases/examples/v0.5.1 -maxdepth 1 -type f -print -exec sed -n '1,120p' {} \;
- sed -n '688,740p' cli_plan/v1_cli/CLI_CONTRACT.md
- ls -la cli_plan/ph_spec/ph/releases/current/examples 2>/dev/null || true
- find cli_plan/ph_spec/ph/releases/current/examples -maxdepth 3 -type f -print -exec sed -n '1,100p' {} \;
- rg -n "\\(TBD\\)|TBD" cli_plan/ph_spec/ph/releases/current/contract.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/releases/current/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the documented schemas match the existing example fixture file shapes.

Outcome:
- status: done
- summary: Completed the `ph/releases/current/` directory contract and reconciled it against the v1 `ph release` command contract and example fixtures.

Next task:
- DD-0126

Blockers (if blocked):
- (none)

## 2026-01-17 23:37 UTC — DD-0124 — Complete spec contract for releases/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0124)
- cli_plan/ph_spec/ph/releases/contract.md
- cli_plan/ph_spec/ph/releases/examples/**

Goal:
- Complete and validate the contract for `ph/releases/`.

Work performed (ordered):
1. Reviewed the release subdirectory contracts and existing example fixtures under `releases/examples/`.
2. Completed the `ph/releases/` root contract with explicit invariants, optional root `CHANGELOG.md` schema, and validation expectations.
3. Mapped the existing example fixtures to the documented contract structure.

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,260p' cli_plan/ph_spec/ph/releases/contract.md
- sed -n '1,260p' cli_plan/ph_spec/ph/releases/current/contract.md
- sed -n '1,320p' cli_plan/ph_spec/ph/releases/delivered/contract.md
- ls -la cli_plan/ph_spec/ph/releases/examples && find cli_plan/ph_spec/ph/releases/examples -maxdepth 4 -type f -print -exec sed -n '1,140p' {} \;
- rg -n "## `ph release`|ph release plan|ph release close|release add-feature" cli_plan/v1_cli/CLI_CONTRACT.md -n
- sed -n '680,770p' cli_plan/v1_cli/CLI_CONTRACT.md
- rg -n "\\(TBD\\)|TBD" cli_plan/ph_spec/ph/releases/contract.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/releases/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the existing example fixtures are referenced in Examples Mapping.

Outcome:
- status: done
- summary: Completed the `ph/releases/` directory contract and reconciled it against the existing example fixtures and v1 `ph release` contract surface.

Next task:
- DD-0125

Blockers (if blocked):
- (none)

## 2026-01-17 23:34 UTC — DD-0123 — Complete spec contract for parking-lot/technical-debt/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0123)
- cli_plan/ph_spec/ph/parking-lot/contract.md
- cli_plan/ph_spec/ph/parking-lot/technical-debt/contract.md
- cli_plan/ph_spec/ph/parking-lot/technical-debt/examples/**

Goal:
- Complete and validate the contract for `ph/parking-lot/technical-debt/`.

Work performed (ordered):
1. Reviewed the technical-debt category contract stub and its example fixture.
2. Completed the contract with item naming rules, required README schema, and non-destructive creation semantics.
3. Reconciled the provided example fixture to represent an active parking-lot item (`status: parking-lot`, no archival keys).

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,220p' cli_plan/ph_spec/ph/parking-lot/technical-debt/contract.md
- ls -la cli_plan/ph_spec/ph/parking-lot/technical-debt/examples && find cli_plan/ph_spec/ph/parking-lot/technical-debt/examples -maxdepth 4 -type f -print -exec sed -n '1,120p' {} \;
- rg -n "DEBT-YYYYMMDD" legacy-reference/project-handbook/docs/PARKING_LOT_SYSTEM.md
- rg -n "\\(TBD\\)|TBD" cli_plan/ph_spec/ph/parking-lot/technical-debt/contract.md cli_plan/ph_spec/ph/parking-lot/technical-debt/examples/DEBT-20260102-standardize-task-directory-slu/README.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/parking-lot/technical-debt/contract.md
- cli_plan/ph_spec/ph/parking-lot/technical-debt/examples/DEBT-20260102-standardize-task-directory-slu/README.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the reconciled example fixture now matches the active item schema (`status: parking-lot`).

Outcome:
- status: done
- summary: Completed the `ph/parking-lot/technical-debt/` directory contract and reconciled the provided example fixture to match the active parking-lot item schema.

Next task:
- DD-0124

Blockers (if blocked):
- (none)

## 2026-01-17 23:32 UTC — DD-0122 — Complete spec contract for parking-lot/research/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0122)
- cli_plan/ph_spec/ph/parking-lot/contract.md
- cli_plan/ph_spec/ph/parking-lot/research/contract.md
- cli_plan/ph_spec/ph/parking-lot/research/examples/**

Goal:
- Complete and validate the contract for `ph/parking-lot/research/`.

Work performed (ordered):
1. Reviewed the research category contract stub and its example fixture.
2. Completed the contract with item naming rules, required README schema, and non-destructive creation semantics.
3. Reconciled the provided example fixture to represent an active parking-lot item (`status: parking-lot`, no archival keys).

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,220p' cli_plan/ph_spec/ph/parking-lot/research/contract.md
- ls -la cli_plan/ph_spec/ph/parking-lot/research/examples && find cli_plan/ph_spec/ph/parking-lot/research/examples -maxdepth 4 -type f -print -exec sed -n '1,120p' {} \;
- rg -n "RES-YYYYMMDD" legacy-reference/project-handbook/docs/PARKING_LOT_SYSTEM.md
- rg -n "\\(TBD\\)|TBD" cli_plan/ph_spec/ph/parking-lot/research/contract.md cli_plan/ph_spec/ph/parking-lot/research/examples/RES-20251230-process-fix-session-end-index-/README.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/parking-lot/research/contract.md
- cli_plan/ph_spec/ph/parking-lot/research/examples/RES-20251230-process-fix-session-end-index-/README.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the reconciled example fixture now matches the active item schema (`status: parking-lot`).

Outcome:
- status: done
- summary: Completed the `ph/parking-lot/research/` directory contract and reconciled the provided example fixture to match the active parking-lot item schema.

Next task:
- DD-0123

Blockers (if blocked):
- (none)

## 2026-01-17 23:31 UTC — DD-0121 — Complete spec contract for parking-lot/features/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0121)
- cli_plan/ph_spec/ph/parking-lot/contract.md
- cli_plan/ph_spec/ph/parking-lot/features/contract.md
- cli_plan/ph_spec/ph/parking-lot/features/examples/**

Goal:
- Complete and validate the contract for `ph/parking-lot/features/`.

Work performed (ordered):
1. Reviewed the features category contract stub and confirmed there are no example fixtures for this category.
2. Completed the contract with item naming rules, required README schema, and non-destructive creation semantics.
3. Aligned the item front matter expectations with the parking-lot root contract (`status: parking-lot`, no archival keys for active items).

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,220p' cli_plan/ph_spec/ph/parking-lot/features/contract.md
- ls -la cli_plan/ph_spec/ph/parking-lot/features/examples && find cli_plan/ph_spec/ph/parking-lot/features/examples -maxdepth 4 -type f -print -exec sed -n '1,120p' {} \;
- rg -n "FEAT-<YYYYMMDD>" -n legacy-reference/project-handbook/docs/PARKING_LOT_SYSTEM.md
- rg -n "\\(TBD\\)|TBD" cli_plan/ph_spec/ph/parking-lot/features/contract.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/parking-lot/features/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and that the recommended `FEAT-<YYYYMMDD>-<slug>` naming convention is consistent with the legacy-parity documentation.

Outcome:
- status: done
- summary: Completed the `ph/parking-lot/features/` directory contract, including schema and validation rules, despite no example fixtures being present.

Next task:
- DD-0122

Blockers (if blocked):
- (none)

## 2026-01-17 23:30 UTC — DD-0120 — Complete spec contract for parking-lot/external-requests/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0120)
- cli_plan/ph_spec/ph/parking-lot/contract.md
- cli_plan/ph_spec/ph/parking-lot/external-requests/contract.md
- cli_plan/ph_spec/ph/parking-lot/external-requests/examples/**

Goal:
- Complete and validate the contract for `ph/parking-lot/external-requests/`.

Work performed (ordered):
1. Reviewed the external-requests contract stub and confirmed there are no example fixtures for this category.
2. Completed the contract with item naming rules, required README schema, and non-destructive creation semantics.
3. Aligned the item front matter expectations with the parking-lot root contract (`status: parking-lot`, no archival keys for active items).

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,220p' cli_plan/ph_spec/ph/parking-lot/external-requests/contract.md
- ls -la cli_plan/ph_spec/ph/parking-lot/external-requests/examples && find cli_plan/ph_spec/ph/parking-lot/external-requests/examples -maxdepth 4 -type f -print -exec sed -n '1,120p' {} \;
- sed -n '1,80p' legacy-reference/project-handbook/docs/PARKING_LOT_SYSTEM.md
- rg -n "\\(TBD\\)|TBD" cli_plan/ph_spec/ph/parking-lot/external-requests/contract.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/parking-lot/external-requests/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and that the recommended `EXT-<YYYYMMDD>-<slug>` naming convention matches the legacy-parity documentation.

Outcome:
- status: done
- summary: Completed the `ph/parking-lot/external-requests/` directory contract, including schema and validation rules, despite no example fixtures being present.

Next task:
- DD-0121

Blockers (if blocked):
- (none)

## 2026-01-17 23:28 UTC — DD-0119 — Complete spec contract for parking-lot/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0119)
- cli_plan/ph_spec/ph/parking-lot/contract.md
- cli_plan/ph_spec/ph/parking-lot/examples/**

Goal:
- Complete and validate the contract for `ph/parking-lot/`.

Work performed (ordered):
1. Reviewed the v1 `ph parking` contract and the existing parking-lot index example fixture.
2. Completed the `ph/parking-lot/` contract (index schema, item README front matter, invariants, and validation rules).
3. Reconciled the example `index.json` timestamp format to be RFC3339 (`Z` suffix).

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,260p' cli_plan/ph_spec/ph/parking-lot/contract.md
- ls -la cli_plan/ph_spec/ph/parking-lot/examples && find cli_plan/ph_spec/ph/parking-lot/examples -maxdepth 3 -type f -print -exec cat {} \;
- sed -n '520,560p' cli_plan/v1_cli/CLI_CONTRACT.md
- sed -n '130,220p' legacy-reference/project-handbook/docs/PARKING_LOT_SYSTEM.md
- rg -n "\\(TBD\\)|TBD" cli_plan/ph_spec/ph/parking-lot/contract.md cli_plan/ph_spec/ph/parking-lot/examples/index.json || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/parking-lot/contract.md
- cli_plan/ph_spec/ph/parking-lot/examples/index.json

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the `examples/index.json` now matches the documented timestamp format.

Outcome:
- status: done
- summary: Completed the `ph/parking-lot/` directory contract and reconciled the bundled index example with the documented schema.

Next task:
- DD-0120

Blockers (if blocked):
- (none)

## 2026-01-17 22:29 UTC — DD-0118 — Complete spec contract for parking-lot/archive/technical-debt/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0118)
- cli_plan/ph_spec/ph/parking-lot/archive/contract.md
- cli_plan/ph_spec/ph/parking-lot/archive/technical-debt/contract.md
- cli_plan/ph_spec/ph/parking-lot/archive/technical-debt/examples/**

Goal:
- Complete and validate the contract for `ph/parking-lot/archive/technical-debt/`.

Work performed (ordered):
1. Reviewed the archive technical-debt contract stub and the existing archived technical-debt example fixture.
2. Completed the contract with explicit archive move semantics and schema rules inherited from the archive root contract.
3. Mapped the archived technical-debt example fixture to the documented schema and validation rules.

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,240p' cli_plan/ph_spec/ph/parking-lot/archive/technical-debt/contract.md
- ls -la cli_plan/ph_spec/ph/parking-lot/archive/technical-debt/examples && find cli_plan/ph_spec/ph/parking-lot/archive/technical-debt/examples -maxdepth 4 -type f -print -exec sed -n '1,120p' {} \;
- find cli_plan/ph_spec/ph/parking-lot/archive/examples/technical-debt -maxdepth 3 -type f -print -exec sed -n '1,140p' {} \;
- rg -n "\\(TBD\\)|TBD" cli_plan/ph_spec/ph/parking-lot/archive/technical-debt/contract.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/parking-lot/archive/technical-debt/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the example fixture includes `status: archived` plus the required archival metadata keys.

Outcome:
- status: done
- summary: Completed the `ph/parking-lot/archive/technical-debt/` directory contract and reconciled it against the included archived technical-debt example fixture.

Next task:
- DD-0119

Blockers (if blocked):
- (none)

## 2026-01-17 22:28 UTC — DD-0117 — Complete spec contract for parking-lot/archive/research/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0117)
- cli_plan/ph_spec/ph/parking-lot/archive/contract.md
- cli_plan/ph_spec/ph/parking-lot/archive/research/contract.md
- cli_plan/ph_spec/ph/parking-lot/archive/research/examples/**

Goal:
- Complete and validate the contract for `ph/parking-lot/archive/research/`.

Work performed (ordered):
1. Reviewed the archive research contract stub and the existing archived research example fixture.
2. Completed the contract with explicit archive move semantics and schema rules inherited from the archive root contract.
3. Mapped the archived research example fixture to the documented schema and validation rules.

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,240p' cli_plan/ph_spec/ph/parking-lot/archive/research/contract.md
- ls -la cli_plan/ph_spec/ph/parking-lot/archive/research/examples && find cli_plan/ph_spec/ph/parking-lot/archive/research/examples -maxdepth 4 -type f -print -exec sed -n '1,120p' {} \;
- find cli_plan/ph_spec/ph/parking-lot/archive/examples/research -maxdepth 3 -type f -print -exec sed -n '1,120p' {} \;
- rg -n "\\(TBD\\)|TBD" cli_plan/ph_spec/ph/parking-lot/archive/research/contract.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/parking-lot/archive/research/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the example fixture includes `status: archived` plus the required archival metadata keys.

Outcome:
- status: done
- summary: Completed the `ph/parking-lot/archive/research/` directory contract and reconciled it against the included archived research example fixture.

Next task:
- DD-0118

Blockers (if blocked):
- (none)

## 2026-01-17 22:26 UTC — DD-0116 — Complete spec contract for parking-lot/archive/features/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0116)
- cli_plan/ph_spec/ph/parking-lot/archive/contract.md
- cli_plan/ph_spec/ph/parking-lot/archive/features/contract.md
- cli_plan/ph_spec/ph/parking-lot/archive/features/examples/**

Goal:
- Complete and validate the contract for `ph/parking-lot/archive/features/`.

Work performed (ordered):
1. Reviewed the archive feature category contract stub and confirmed there are no example fixtures for this category.
2. Completed the contract with explicit archive move semantics and schema rules inherited from the archive root contract.
3. Added validation expectations for archived feature items.

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,240p' cli_plan/ph_spec/ph/parking-lot/archive/features/contract.md
- ls -la cli_plan/ph_spec/ph/parking-lot/archive/features/examples && find cli_plan/ph_spec/ph/parking-lot/archive/features/examples -maxdepth 4 -type f -print -exec sed -n '1,120p' {} \;
- find cli_plan/ph_spec/ph/parking-lot/archive/examples -maxdepth 4 -type f -print -exec rg -n "type: features" {} \; 2>/dev/null || true
- rg -n "^archived_at:|^type:|^status:" -n cli_plan/ph_spec/ph/parking-lot/archive/examples/technical-debt/DEBT-20260102-standardize-task-directory-slu/README.md cli_plan/ph_spec/ph/parking-lot/archive/examples/research/RES-20251230-process-fix-session-end-index-/README.md
- rg -n "\\(TBD\\)|TBD" cli_plan/ph_spec/ph/parking-lot/archive/features/contract.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/parking-lot/archive/features/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and aligns with the archive root schema requirements for `status: archived` + archival metadata.

Outcome:
- status: done
- summary: Completed the `ph/parking-lot/archive/features/` directory contract, including schema and validation rules, despite no example fixtures being present.

Next task:
- DD-0117

Blockers (if blocked):
- (none)

## 2026-01-17 22:19 UTC — DD-0115 — Complete spec contract for parking-lot/archive/external-requests/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0115)
- cli_plan/ph_spec/ph/parking-lot/archive/external-requests/contract.md
- cli_plan/ph_spec/ph/parking-lot/archive/external-requests/examples/**

Goal:
- Complete and validate the contract for `ph/parking-lot/archive/external-requests/`.

Work performed (ordered):
1. Reviewed the external-requests archive contract stub and confirmed there are no example fixtures for this category.
2. Completed the contract with explicit archive move semantics and naming/schema rules inherited from the archive root contract.
3. Added validation expectations for archived external request items.

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,240p' cli_plan/ph_spec/ph/parking-lot/archive/external-requests/contract.md
- ls -la cli_plan/ph_spec/ph/parking-lot/archive/external-requests/examples && find cli_plan/ph_spec/ph/parking-lot/archive/external-requests/examples -maxdepth 3 -type f -print -exec sed -n '1,140p' {} \;
- find cli_plan/ph_spec/ph/parking-lot/archive/examples -maxdepth 3 -type f -print | rg -n "external-requests" || true
- ls -la cli_plan/ph_spec/ph/parking-lot/examples && find cli_plan/ph_spec/ph/parking-lot/examples -maxdepth 4 -type f -print -exec sed -n '1,80p' {} \;
- rg -n "external-requests|EXT-|REQ-|XR-" -S legacy-reference cli_plan/ph_spec/ph | head -n 50
- rg -n "\\(TBD\\)|TBD" cli_plan/ph_spec/ph/parking-lot/archive/external-requests/contract.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/parking-lot/archive/external-requests/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and that the recommended `EXT-<YYYYMMDD>-<slug>` naming convention is consistent with the legacy reference.

Outcome:
- status: done
- summary: Completed the `ph/parking-lot/archive/external-requests/` directory contract, including schema and validation rules, despite no example fixtures being present.

Next task:
- DD-0116

Blockers (if blocked):
- (none)

## 2026-01-17 22:18 UTC — DD-0114 — Complete spec contract for parking-lot/archive/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0114)
- cli_plan/ph_spec/ph/parking-lot/archive/contract.md
- cli_plan/ph_spec/ph/parking-lot/archive/examples/**

Goal:
- Complete and validate the contract for `ph/parking-lot/archive/`.

Work performed (ordered):
1. Reviewed the archive contract stub and the existing archived parking-lot example fixtures.
2. Completed the archive contract with explicit archive move semantics and required archived README front matter.
3. Added validation expectations (archive is read-only; archived items excluded from the active `index.json` catalog).

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,260p' cli_plan/ph_spec/ph/parking-lot/archive/contract.md
- sed -n '1,260p' cli_plan/ph_spec/ph/parking-lot/contract.md
- ls -la cli_plan/ph_spec/ph/parking-lot/archive/examples && find cli_plan/ph_spec/ph/parking-lot/archive/examples -maxdepth 4 -type f -print -exec sed -n '1,160p' {} \;
- rg -n -- "ph parking" cli_plan/v1_cli/CLI_CONTRACT.md | head -n 120
- rg -n "\\(TBD\\)|TBD" cli_plan/ph_spec/ph/parking-lot/archive/contract.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/parking-lot/archive/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the documented archived README front matter requirements match the provided archive example fixtures.

Outcome:
- status: done
- summary: Completed the `ph/parking-lot/archive/` directory contract and reconciled it against the included archived example fixtures.

Next task:
- DD-0115

Blockers (if blocked):
- (none)

## 2026-01-17 22:15 UTC — DD-0113 — Complete spec contract for features/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0113)
- cli_plan/ph_spec/ph/features/contract.md
- cli_plan/ph_spec/ph/features/examples/**

Goal:
- Complete and validate the contract for `ph/features/`.

Work performed (ordered):
1. Reviewed the feature example fixture to infer the standard file set and required front matter keys.
2. Completed the `ph/features/` contract with creation/move semantics and explicit required vs optional artifacts.
3. Reconciled schema expectations with the v1 CLI feature command surface (`create`, `status`, `update-status`, `archive`).

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,260p' cli_plan/ph_spec/ph/features/contract.md
- ls -la cli_plan/ph_spec/ph/features/examples && find cli_plan/ph_spec/ph/features/examples -maxdepth 4 -type f -print -exec sed -n '1,160p' {} \;
- rg -n "## `ph feature`|ph feature create|ph feature list|ph feature status|ph feature update-status|ph feature summary" cli_plan/v1_cli/CLI_CONTRACT.md
- sed -n '456,520p' cli_plan/v1_cli/CLI_CONTRACT.md
- find cli_plan/ph_spec/ph/features/examples/v2_launch -maxdepth 3 -type f -print
- sed -n '1,160p' cli_plan/ph_spec/ph/features/examples/v2_launch/testing/TESTING.md
- sed -n '460,505p' cli_plan/v1_cli/CLI_CONTRACT.md
- rg -n -- "--stage <" cli_plan/v1_cli/CLI_CONTRACT.md
- rg -n "\\(TBD\\)|TBD" cli_plan/ph_spec/ph/features/contract.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/features/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and its required file set matches the included feature example fixture.

Outcome:
- status: done
- summary: Completed the `ph/features/` directory contract and reconciled it against the v1 CLI feature commands and the provided example feature docs.

Next task:
- DD-0114

Blockers (if blocked):
- (none)

## 2026-01-17 22:06 UTC — DD-0112 — Complete spec contract for features/archive/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0112)
- cli_plan/ph_spec/ph/features/archive/contract.md
- cli_plan/ph_spec/ph/features/archive/examples/**

Goal:
- Complete and validate the contract for `ph/features/archive/`.

Work performed (ordered):
1. Reviewed the existing `ph/features/archive/` contract stub and confirmed there are no example fixtures for this directory.
2. Completed the archive contract with move semantics (`ph feature archive`), immutability rules, and validation expectations.
3. Reconciled the contract against the v1 CLI contract’s feature archive behavior (move-only, `--force` for collisions).

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,240p' cli_plan/ph_spec/ph/features/archive/contract.md
- rg -n "## `ph feature`|ph feature" cli_plan/v1_cli/CLI_CONTRACT.md | head -n 120
- sed -n '450,520p' cli_plan/v1_cli/CLI_CONTRACT.md
- rg -n "ph feature archive" cli_plan/v1_cli/CLI_CONTRACT.md
- ls -la cli_plan/ph_spec/ph/features/archive/examples && find cli_plan/ph_spec/ph/features/archive/examples -maxdepth 3 -type f -print -exec sed -n '1,120p' {} \;
- rg -n "\\(TBD\\)|TBD" cli_plan/ph_spec/ph/features/archive/contract.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/features/archive/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and its move/immutability rules align with `ph feature archive` as defined in `CLI_CONTRACT.md`.

Outcome:
- status: done
- summary: Completed the `ph/features/archive/` directory contract with explicit archive move semantics and read-only expectations.

Next task:
- DD-0113

Blockers (if blocked):
- (none)

## 2026-01-17 22:05 UTC — DD-0111 — Complete spec contract for decision-register/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0111)
- cli_plan/ph_spec/ph/decision-register/contract.md
- cli_plan/ph_spec/ph/decision-register/examples/**

Goal:
- Complete and validate the contract for `ph/decision-register/`.

Work performed (ordered):
1. Reviewed the existing `ph/decision-register/` contract stub and the bundled example DR/README fixtures.
2. Completed the directory contract (purpose, creation rules, file naming, front matter requirements, and validation expectations).
3. Mapped the example fixtures to the documented schema and conventions.

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,260p' cli_plan/ph_spec/ph/decision-register/contract.md
- ls -la cli_plan/ph_spec/ph/decision-register/examples && find cli_plan/ph_spec/ph/decision-register/examples -maxdepth 2 -type f -print -exec sed -n '1,200p' {} \;
- rg -n "decision-register|\\bDR-" cli_plan/v1_cli/CLI_CONTRACT.md | head -n 80
- rg -n "\\(TBD\\)|TBD" cli_plan/ph_spec/ph/decision-register/contract.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/decision-register/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the example fixtures match the documented filename/front matter conventions.

Outcome:
- status: done
- summary: Completed the `ph/decision-register/` directory contract and reconciled it against the included example README and DR entry.

Next task:
- DD-0112

Blockers (if blocked):
- (none)

## 2026-01-17 22:03 UTC — DD-0110 — Complete spec contract for contracts/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0110)
- cli_plan/ph_spec/ph/contracts/contract.md
- cli_plan/ph_spec/ph/contracts/examples/**

Goal:
- Complete and validate the contract for `ph/contracts/`.

Work performed (ordered):
1. Reviewed existing `ph/contracts/` contract stub and example fixtures.
2. Completed the directory contract with purpose, ownership/overwrite rules, optional schemas, and validation expectations.
3. Mapped the existing examples to the documented contract structure.

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,240p' cli_plan/ph_spec/ph/contracts/contract.md
- rg -n "ph contract|contracts/" cli_plan/v1_cli/CLI_CONTRACT.md | head -n 80
- ls -la cli_plan/ph_spec/ph/contracts/examples && find cli_plan/ph_spec/ph/contracts/examples -maxdepth 3 -type f -print -exec sed -n '1,160p' {} \;
- rg -n "\\(TBD\\)|TBD" cli_plan/ph_spec/ph/contracts/contract.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/contracts/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the documented examples exist under `ph/contracts/examples/`.

Outcome:
- status: done
- summary: Completed the `ph/contracts/` directory contract and reconciled it with the existing example fixtures.

Next task:
- DD-0111

Blockers (if blocked):
- (none)

## 2026-01-17 21:59 UTC — DD-0109 — Complete spec contract for ph/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0109)
- cli_plan/ph_spec/ph/contract.md
- cli_plan/ph_spec/ph/**/contract.md

Goal:
- Complete and validate the contract for the `ph/` root directory.

Work performed (ordered):
1. Reviewed the v1 layout/contract sources of truth for the `PH_CONTENT_ROOT` (`ph/`) content tree.
2. Completed the `ph/` root contract with required top-level directories, invariants, and validation delegation to subdirectory contracts.
3. Reconciled the `ph/examples/backlog/bugs` example fixture with the non-archive bug contract by removing archived-only front matter keys.

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- ls -la cli_plan/ph_spec/ph && ls -la cli_plan/ph_spec/ph/examples 2>/dev/null || true
- sed -n '1,220p' cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- find cli_plan/ph_spec/ph/examples -maxdepth 3 -type f -print | head -n 50
- find cli_plan/ph_spec/ph/examples -maxdepth 2 -type d -print
- find cli_plan/ph_spec/ph/examples/backlog -type f -maxdepth 3 -print -exec sed -n '1,80p' {} \;
- find cli_plan/ph_spec/ph/examples/sprints -type f -maxdepth 4 -print -exec sed -n '1,120p' {} \;
- rg -n "PH_CONTENT_ROOT|content root" cli_plan/v1_cli/CLI_CONTRACT.md
- sed -n '1,120p' cli_plan/v1_cli/CLI_CONTRACT.md
- rg -n "now-next-later\\.md" cli_plan/v1_cli/CLI_CONTRACT.md
- sed -n '120,170p' cli_plan/v1_cli/CLI_CONTRACT.md
- rg -n "\\(TBD\\)|TBD" cli_plan/ph_spec/ph/contract.md || true
- rg -n "archived_" cli_plan/ph_spec/ph/examples/backlog/bugs/EXAMPLE-BUG-P0-20250922-1144/README.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/contract.md
- cli_plan/ph_spec/ph/examples/backlog/bugs/EXAMPLE-BUG-P0-20250922-1144/README.md

Verification:
- Confirmed the root `ph/` contract has no remaining `(TBD)` placeholders and the updated example fixture no longer includes archived-only front matter keys.

Outcome:
- status: done
- summary: Completed the `ph/` root contract and reconciled the bundled example fixture with the non-archive bug contract.

Next task:
- DD-0110

Blockers (if blocked):
- (none)

## 2026-01-17 21:57 UTC — DD-0108 — Complete spec contract for backlog/work-items/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0108)
- cli_plan/ph_spec/ph/backlog/contract.md
- cli_plan/ph_spec/ph/backlog/work-items/contract.md
- cli_plan/ph_spec/ph/backlog/work-items/examples/**

Goal:
- Complete and validate the contract for `ph/backlog/work-items/`.

Work performed (ordered):
1. Reviewed the backlog contracts and the existing example work-item README fixture.
2. Completed the `ph/backlog/work-items/` contract sections (purpose, creation, required layout, schema, invariants, validation, examples).
3. Reconciled the work-item schema with `ph backlog add` and the archived work-item contract (archival keys forbidden for active items).

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ" && date -u +"%Y-%m-%d %H:%M UTC"
- sed -n '1,220p' cli_plan/ph_spec/ph/backlog/contract.md
- sed -n '1,200p' cli_plan/ph_spec/ph/backlog/work-items/contract.md
- ls -la cli_plan/ph_spec/ph/backlog/work-items/examples
- find cli_plan/ph_spec/ph/backlog/work-items/examples/WORK-P2-20260106-213751 -maxdepth 2 -type f -print -exec sed -n '1,160p' {} \;
- sed -n '1,240p' cli_plan/ph_spec/ph/backlog/archive/work-items/contract.md
- rg -n "backlog add|ph backlog" cli_plan/v1_cli/CLI_CONTRACT.md
- sed -n '480,570p' cli_plan/v1_cli/CLI_CONTRACT.md
- rg -n "\\(TBD\\)|TBD" cli_plan/ph_spec/ph/backlog/work-items/contract.md || true
- date -u +"%Y-%m-%dT%H:%M:%SZ"

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/backlog/work-items/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the example fixture includes the required front matter keys for active work-items.

Outcome:
- status: done
- summary: Completed the backlog work-items directory contract and reconciled it against the examples and the CLI/backlog contracts.

Next task:
- DD-0109

Blockers (if blocked):
- (none)

## 2026-01-17 04:13 UTC — DD-0006 — Define content vs internal ownership rules

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: (not used; due-diligence only)

Inputs reviewed:
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0006)
- cli_plan/ph_spec/CONTRACT_TEMPLATE.md
- cli_plan/ph_spec/ph/**/contract.md

Goal:
- Define a consistent, explicit ownership/regeneration policy and ensure every `ph_spec` directory contract calls out which artifacts are human-authored (“content”) vs CLI-authored (“internal”), including overwrite rules.

Work performed (ordered):
1. Updated `cli_plan/ph_spec/CONTRACT_TEMPLATE.md` and `cli_plan/ph_spec/ph/contract.md` to define consistent “content vs internal” terminology and default overwrite rules.
2. Updated every `cli_plan/ph_spec/ph/**/contract.md` ownership section to explicitly list content artifacts, internal artifacts safe to regenerate, and overwrite rules.

Commands executed (exact):
- find adr -maxdepth 2 -type f | head
- find backlog -maxdepth 3 -type f | head -n 40
- find status -maxdepth 3 -type f | head -n 40
- find features -maxdepth 3 -type f | head -n 40
- python3 - <<'PY'

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/ph_spec/CONTRACT_TEMPLATE.md
- cli_plan/ph_spec/ph/adr/contract.md
- cli_plan/ph_spec/ph/backlog/archive/bugs/contract.md
- cli_plan/ph_spec/ph/backlog/archive/contract.md
- cli_plan/ph_spec/ph/backlog/archive/wildcards/contract.md
- cli_plan/ph_spec/ph/backlog/archive/work-items/contract.md
- cli_plan/ph_spec/ph/backlog/bugs/contract.md
- cli_plan/ph_spec/ph/backlog/contract.md
- cli_plan/ph_spec/ph/backlog/wildcards/contract.md
- cli_plan/ph_spec/ph/backlog/work-items/contract.md
- cli_plan/ph_spec/ph/contract.md
- cli_plan/ph_spec/ph/contracts/contract.md
- cli_plan/ph_spec/ph/decision-register/contract.md
- cli_plan/ph_spec/ph/features/archive/contract.md
- cli_plan/ph_spec/ph/features/contract.md
- cli_plan/ph_spec/ph/parking-lot/archive/contract.md
- cli_plan/ph_spec/ph/parking-lot/archive/external-requests/contract.md
- cli_plan/ph_spec/ph/parking-lot/archive/features/contract.md
- cli_plan/ph_spec/ph/parking-lot/archive/research/contract.md
- cli_plan/ph_spec/ph/parking-lot/archive/technical-debt/contract.md
- cli_plan/ph_spec/ph/parking-lot/contract.md
- cli_plan/ph_spec/ph/parking-lot/external-requests/contract.md
- cli_plan/ph_spec/ph/parking-lot/features/contract.md
- cli_plan/ph_spec/ph/parking-lot/research/contract.md
- cli_plan/ph_spec/ph/parking-lot/technical-debt/contract.md
- cli_plan/ph_spec/ph/releases/contract.md
- cli_plan/ph_spec/ph/releases/current/contract.md
- cli_plan/ph_spec/ph/releases/delivered/contract.md
- cli_plan/ph_spec/ph/releases/planning/contract.md
- cli_plan/ph_spec/ph/roadmap/contract.md
- cli_plan/ph_spec/ph/sprints/archive/contract.md
- cli_plan/ph_spec/ph/sprints/contract.md
- cli_plan/ph_spec/ph/status/contract.md
- cli_plan/ph_spec/ph/status/daily/contract.md
- cli_plan/ph_spec/ph/status/evidence/contract.md
- cli_plan/ph_spec/ph/status/exports/contract.md
- cli_plan/session_logs.md

Verification:
- python3 - <<'PY'
  - output: OK 35

Outcome:
- status: done
- summary: Standardized content-vs-internal ownership language across `ph_spec` and added explicit overwrite rules to every `contract.md` under `cli_plan/ph_spec/ph/**`.

Next task:
- DD-0007

Blockers (if blocked):
- (none)

## 2026-01-17 04:21 UTC — DD-0007 — Align validation rules with new ph/.ph layout

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: (not used; due-diligence only)

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0007)
- process/checks/validation_rules.json
- process/checks/validate_docs.py

Goal:
- Remove legacy/backward-compat validation behavior (system scope, legacy execution phases) and align validation paths/checks to the v1 `.ph/**` internals + `ph/**` content layout.

Work performed (ordered):
1. Removed system-scope + legacy “execution phase” validation behavior.
2. Updated validator roots so it validates only `PH_ROOT/ph/**` and writes reports under `PH_ROOT/.ph/status/validation.json`.
3. Aligned CLI contract session template/log paths to `.ph/process/sessions/**`.

Commands executed (exact):
- cat process/checks/validation_rules.json
- sed -n '1,220p' process/checks/validate_docs.py
- rg -n "ph validate|ph check|validation\\.json" cli_plan/v1_cli/CLI_CONTRACT.md | head -n 80
- sed -n '240,340p' cli_plan/v1_cli/CLI_CONTRACT.md
- rg -n "PH_ROOT/process/sessions" cli_plan/v1_cli/CLI_CONTRACT.md
- python3 process/checks/validate_docs.py --quick
- ls -la .ph && find .ph -maxdepth 3 -type f -print

Files changed (exact paths):
- .gitignore
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- process/checks/validate_docs.py
- process/checks/validation_rules.json
- .ph/status/validation.json

Verification:
- python3 process/checks/validate_docs.py --quick
  - output: report written under `.ph/status/validation.json` (as per contract); expected errors because this repo does not yet have `ph/` or `.ph/process/checks/validation_rules.json`.

Outcome:
- status: done
- summary: Removed legacy/system-scope validation behavior and updated paths to the v1 `.ph/**` + `ph/**` layout (including `.ph/process/sessions/**` references in the CLI contract).

Next task:
- DD-0100

Blockers (if blocked):
- (none)

## 2026-01-17 04:34 UTC — DD-0100 — Complete spec contract for adr/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: (not used; due-diligence only)

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0100)
- cli_plan/ph_spec/ph/adr/contract.md
- cli_plan/ph_spec/ph/adr/examples/**

Goal:
- Write an explicit, unambiguous contract for `ph/adr/` including naming, required front matter schema, invariants, validation rules, and example mapping.

Work performed (ordered):
1. Reviewed the ADR example under `cli_plan/ph_spec/ph/adr/examples/` and confirmed it matches current ADR front matter conventions.
2. Updated the `ph/adr/` contract with filename conventions, required front matter schema, invariants, and validation expectations.

Commands executed (exact):
- find cli_plan/ph_spec/ph/adr -maxdepth 2 -type f -print
- sed -n '1,200p' cli_plan/ph_spec/ph/adr/examples/0007-tribuence-mini-v2-supergraph-context.md
- sed -n '1,220p' cli_plan/ph_spec/ph/adr/contract.md

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/ph_spec/ph/adr/contract.md
- cli_plan/session_logs.md

Verification:
- Confirmed `cli_plan/ph_spec/ph/adr/contract.md` specifies naming, front matter schema, invariants, validation rules, and example mapping.

Outcome:
- status: done
- summary: Defined an explicit `ph/adr/` contract (naming + front matter schema + invariants) and mapped it to the existing example fixture.

Next task:
- DD-0101

Blockers (if blocked):
- (none)

## 2026-01-17 04:38 UTC — DD-0101 — Complete spec contract for backlog/archive/bugs/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: (not used; due-diligence only)

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0101)
- cli_plan/ph_spec/ph/backlog/archive/bugs/contract.md
- cli_plan/ph_spec/ph/backlog/archive/bugs/examples/**

Goal:
- Write an explicit contract for archived backlog bugs under `ph/backlog/archive/bugs/` including expected directory layout, file schemas, invariants, and example mapping.

Work performed (ordered):
1. Reviewed the archived bug example fixture and extracted a minimal file + front matter schema.
2. Updated the `ph/backlog/archive/bugs/` contract to specify allowed directory names, required files, and invariants for archived items.

Commands executed (exact):
- find cli_plan/ph_spec/ph/backlog/archive/bugs -maxdepth 3 -type f -print
- sed -n '1,200p' cli_plan/ph_spec/ph/backlog/archive/bugs/examples/EXAMPLE-BUG-P0-20250922-1144/README.md
- sed -n '1,200p' cli_plan/ph_spec/ph/backlog/archive/bugs/examples/EXAMPLE-BUG-P0-20250922-1144/triage.md
- sed -n '1,200p' cli_plan/ph_spec/ph/backlog/archive/bugs/contract.md

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/ph_spec/ph/backlog/archive/bugs/contract.md
- cli_plan/session_logs.md

Verification:
- Confirmed the example fixture aligns with the contract (README front matter + optional `triage.md`).

Outcome:
- status: done
- summary: Defined an explicit contract for archived backlog bugs (required README schema + archival invariants) and reconciled it with the example fixture.

Next task:
- DD-0102

Blockers (if blocked):
- (none)

## 2026-01-17 04:40 UTC — DD-0102 — Complete spec contract for backlog/archive/

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: (not used; due-diligence only)

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0102)
- cli_plan/ph_spec/ph/backlog/archive/contract.md
- cli_plan/ph_spec/ph/backlog/archive/**

Goal:
- Write an explicit contract for the `ph/backlog/archive/` container directory (structure, invariants, and validation expectations), and ensure it is consistent with the child archive category contracts.

Work performed (ordered):
1. Reviewed the `ph/backlog/archive/` subtree and confirmed there are no container-level example fixtures.
2. Updated the container contract to specify required category subdirectories and to defer schemas/examples to the child category contracts.

Commands executed (exact):
- find cli_plan/ph_spec/ph/backlog/archive -maxdepth 2 -type f -print
- sed -n '1,220p' cli_plan/ph_spec/ph/backlog/archive/contract.md

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/ph_spec/ph/backlog/archive/contract.md
- cli_plan/session_logs.md

Verification:
- Confirmed the `ph/backlog/archive/` contract is consistent with child archive category contracts and does not invent container-level schemas/examples.

Outcome:
- status: done
- summary: Defined an explicit `ph/backlog/archive/` container contract (required subdirs + invariants) and linked validation expectations to the child category contracts.

Next task:
- DD-0103

Blockers (if blocked):
- (none)

## 2026-01-17 14:04 UTC — DD-0008 — Clarify human vs agent authorship in ownership language

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: (not used; due-diligence only)

Inputs reviewed:
- cli_plan/due-diligence.json (task DD-0008)
- cli_plan/ph_spec/CONTRACT_TEMPLATE.md
- cli_plan/ph_spec/ph/**/contract.md

Goal:
- Update spec language so “content artifacts” are project-owned (human-directed) even when generated/edited via `ph` inputs by AI agents; keep “internal/derived artifacts” reserved for safe-to-regenerate outputs.

Work performed (ordered):
1. Reworded the ownership template and root `ph/` contract to distinguish project-owned content (human-directed) from safe-to-regenerate derived/internal artifacts.
2. Updated every `ph_spec` directory contract to use “project-owned (human/agent-authored)” wording for content artifacts.

Commands executed (exact):
- rg -n "Content artifacts \\(human-authored\\)|Owner: Human\\." cli_plan/ph_spec -S
- python3 - <<'PY'

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/ph_spec/CONTRACT_TEMPLATE.md
- cli_plan/ph_spec/ph/contract.md
- cli_plan/ph_spec/ph/**/contract.md
- cli_plan/session_logs.md

Verification:
- rg confirms no remaining `human-authored` ownership labels in `cli_plan/ph_spec/**`.
- python check confirms all 35 contracts include the updated ownership wording.

Outcome:
- status: done
- summary: Clarified that “content” is project-owned (human-directed) even when generated/edited by `ph` inputs via AI agents, and reserved “derived/internal” for explicitly safe-to-regenerate artifacts.

Next task:
- DD-0103

Blockers (if blocked):
- (none)

## 2026-01-17 03:59 UTC — DD-0005 — Confirm symlink policy for sprints/current

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: (not used; due-diligence only)

Inputs reviewed:
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0005)
- cli_plan/ph_spec/ph/sprints/contract.md
- cli_plan/ph_spec/ph/sprints/archive/contract.md

Goal:
- Define canonical `sprints/current` behavior and a safe fallback for platforms without symlink support.

Work performed (ordered):
1. Defined `sprints/current` as a directory link with a Windows-safe fallback (junction).
2. Updated `ph_spec` and CLI contract wording so `ph sprint plan|open` are explicit about link behavior and remediation.

Commands executed (exact):
- rg -n "symlink" cli_plan/v1_cli/CLI_CONTRACT.md
- nl -ba cli_plan/v1_cli/CLI_CONTRACT.md | sed -n '340,390p'

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/ph_spec/ph/sprints/contract.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/session_logs.md

Verification:
- Confirmed `ph sprint plan|open` explicitly specify POSIX symlink vs Windows junction behavior in `cli_plan/v1_cli/CLI_CONTRACT.md`.

Outcome:
- status: done
- summary: Canonicalized `sprints/current` as a directory link and documented a Windows-compatible fallback (junction) with explicit remediation on failure.

Next task:
- DD-0006

Blockers (if blocked):
- (none)

## 2026-01-17 03:55 UTC — DD-0004 — Define sprint lifecycle contract (plan/open/close/archive)

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: (not used; due-diligence only)

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0004)
- cli_plan/ph_spec/ph/sprints/**/contract.md

Goal:
- Specify required sprint artifacts and lifecycle transitions, including archive index semantics and `sprints/current` behavior.

Work performed (ordered):
1. Reviewed `ph sprint *` behavior in the v1 CLI contract and the legacy sprint automation to extract required artifacts and archive behaviors.
2. Updated `ph_spec` sprint contracts to specify required files/dirs, `sprints/current` pointer behavior, and archive index semantics.

Commands executed (exact):
- nl -ba cli_plan/v1_cli/CLI_CONTRACT.md | sed -n '330,520p'
- ls -la sprints && find sprints -maxdepth 3 -type f -print | head -n 200
- cat sprints/archive/index.json
- sed -n '1,200p' sprints/2026/SPRINT-2026-01-11/plan.md
- find sprints/archive/2026/SPRINT-2026-01-09 -maxdepth 2 -type f -print
- for d in sprints/archive/2026/*; do echo "-- $d"; ls -1 "$d"; done | head -n 120
- rg -n "sprints/current|sprints/archive|archive/index\\.json|SPRINT-" process/automation/sprint_manager.py | head -n 120
- nl -ba process/automation/sprint_manager.py | sed -n '1,220p'
- rg -n "burndown\\.md" process/automation/sprint_manager.py | head -n 80
- nl -ba process/automation/sprint_manager.py | sed -n '980,1060p'
- rg -n "def archive_sprint_directory\\(" -n process/automation/sprint_manager.py && nl -ba process/automation/sprint_manager.py | sed -n '520,640p'

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/ph_spec/ph/sprints/contract.md
- cli_plan/ph_spec/ph/sprints/archive/contract.md
- cli_plan/session_logs.md

Verification:
- Confirmed the contract matches `cli_plan/v1_cli/CLI_CONTRACT.md` command descriptions and the archive index schema in `sprints/archive/index.json`.

Outcome:
- status: done
- summary: Defined sprint lifecycle artifacts and archive/index invariants, with a clear `sprints/current` pointer model.

Next task:
- DD-0005

Blockers (if blocked):
- (none)

## 2026-01-17 03:50 UTC — DD-0003 — Define release lifecycle contract (planning/current/delivered)

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: (not used; due-diligence only)

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0003)
- cli_plan/ph_spec/ph/releases/**/contract.md

Goal:
- Specify required release files and transitions across `planning/`, `current/`, and `delivered/`, including `ph release close` semantics.

Work performed (ordered):
1. Reviewed the v1 CLI contract and existing Make-era release behavior to extract the required release artifact set.
2. Updated `ph_spec` release contracts to define required files, schemas, and lifecycle transitions across `planning/`, `current/`, and `delivered/`.

Commands executed (exact):
- nl -ba cli_plan/v1_cli/CLI_CONTRACT.md | sed -n '650,780p'
- ls -la releases && find releases -maxdepth 2 -type f -print
- ls -la process/automation | rg -n "release" -S || true
- sed -n '1,240p' process/automation/release_manager.py
- rg -n "write_text\\(|changelog\\.md|progress\\.md|features\\.yaml" process/automation/release_manager.py | head -n 80
- nl -ba process/automation/release_manager.py | sed -n '220,340p'
- nl -ba process/automation/release_manager.py | sed -n '700,840p'

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/ph_spec/ph/releases/contract.md
- cli_plan/ph_spec/ph/releases/planning/contract.md
- cli_plan/ph_spec/ph/releases/current/contract.md
- cli_plan/ph_spec/ph/releases/delivered/contract.md
- cli_plan/session_logs.md

Verification:
- Confirmed the file set and move semantics align with `cli_plan/v1_cli/CLI_CONTRACT.md` `ph release *` file paths.

Outcome:
- status: done
- summary: Defined the release lifecycle contract with explicit required files and `ph release close` move/version semantics.

Next task:
- DD-0004

Blockers (if blocked):
- (none)

## 2026-01-17 03:48 UTC — DD-0002 — Confirm parking-lot category taxonomy

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: (not used; due-diligence only)

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0002)
- cli_plan/ph_spec/ph/parking-lot/**/contract.md
- process/checks/validation_rules.json

Goal:
- Decide whether `ph/parking-lot/external-requests/` is an allowed category and ensure the choice is consistent across spec/contracts/validation rules.

Work performed (ordered):
1. Confirmed `external-requests` is an allowed v1 parking-lot category (consistent across ADR, CLI contract, and validation rules).
2. Updated `ph_spec` parking-lot contracts to explicitly list the allowed categories.

Commands executed (exact):
- rg -n "external-requests" -S cli_plan process | head -n 50
- sed -n '1,200p' process/checks/validation_rules.json
- sed -n '1,200p' cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- sed -n '1,250p' cli_plan/v1_cli/CLI_CONTRACT.md
- sed -n '1,200p' cli_plan/ph_spec/ph/parking-lot/examples/index.json

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/ph_spec/ph/parking-lot/contract.md
- cli_plan/ph_spec/ph/parking-lot/archive/contract.md
- cli_plan/session_logs.md

Verification:
- Verified consistency by inspecting:
  - `process/checks/validation_rules.json` (`parking_lot.allowed_categories`)
  - `cli_plan/v1_cli/CLI_CONTRACT.md` and `cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md` path lists

Outcome:
- status: done
- summary: Kept `external-requests` as an allowed parking-lot category and documented the allowed categories in `ph_spec` contracts.

Next task:
- DD-0003

Blockers (if blocked):
- (none)

## 2026-01-17 03:43 UTC — DD-0001 — Define contract.md standard template

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: (not used; due-diligence only)

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0001)
- cli_plan/ph_spec/ph/**/contract.md

Goal:
- Define a standard outline for all `cli_plan/ph_spec/**/contract.md` files and apply it consistently.

Work performed (ordered):
1. Added a standard `contract.md` outline template for `ph_spec`.
2. Applied that outline across every `cli_plan/ph_spec/ph/**/contract.md`.
3. Verified there are no `contract.md` files missing the template.

Commands executed (exact):
- date -u +"%Y-%m-%dT%H:%M:%SZ"
- find cli_plan/ph_spec -maxdepth 4 -type f -name 'contract.md' -print
- python3 - <<'PY'
- python3 - <<'PY'
- git diff --name-only
- git status --porcelain

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/ph_spec/CONTRACT_TEMPLATE.md
- cli_plan/ph_spec/ph/adr/contract.md
- cli_plan/ph_spec/ph/backlog/archive/bugs/contract.md
- cli_plan/ph_spec/ph/backlog/archive/contract.md
- cli_plan/ph_spec/ph/backlog/archive/wildcards/contract.md
- cli_plan/ph_spec/ph/backlog/archive/work-items/contract.md
- cli_plan/ph_spec/ph/backlog/bugs/contract.md
- cli_plan/ph_spec/ph/backlog/contract.md
- cli_plan/ph_spec/ph/backlog/wildcards/contract.md
- cli_plan/ph_spec/ph/backlog/work-items/contract.md
- cli_plan/ph_spec/ph/contract.md
- cli_plan/ph_spec/ph/contracts/contract.md
- cli_plan/ph_spec/ph/decision-register/contract.md
- cli_plan/ph_spec/ph/features/archive/contract.md
- cli_plan/ph_spec/ph/features/contract.md
- cli_plan/ph_spec/ph/parking-lot/archive/contract.md
- cli_plan/ph_spec/ph/parking-lot/archive/external-requests/contract.md
- cli_plan/ph_spec/ph/parking-lot/archive/features/contract.md
- cli_plan/ph_spec/ph/parking-lot/archive/research/contract.md
- cli_plan/ph_spec/ph/parking-lot/archive/technical-debt/contract.md
- cli_plan/ph_spec/ph/parking-lot/contract.md
- cli_plan/ph_spec/ph/parking-lot/external-requests/contract.md
- cli_plan/ph_spec/ph/parking-lot/features/contract.md
- cli_plan/ph_spec/ph/parking-lot/research/contract.md
- cli_plan/ph_spec/ph/parking-lot/technical-debt/contract.md
- cli_plan/ph_spec/ph/releases/contract.md
- cli_plan/ph_spec/ph/releases/current/contract.md
- cli_plan/ph_spec/ph/releases/delivered/contract.md
- cli_plan/ph_spec/ph/releases/planning/contract.md
- cli_plan/ph_spec/ph/roadmap/contract.md
- cli_plan/ph_spec/ph/sprints/archive/contract.md
- cli_plan/ph_spec/ph/sprints/contract.md
- cli_plan/ph_spec/ph/status/contract.md
- cli_plan/ph_spec/ph/status/daily/contract.md
- cli_plan/ph_spec/ph/status/evidence/contract.md
- cli_plan/ph_spec/ph/status/exports/contract.md
- cli_plan/session_logs.md

Verification:
- python3 - <<'PY'
  - output: missing 0

Outcome:
- status: done
- summary: Defined a standard `ph_spec` `contract.md` outline and applied it across all existing `contract.md` files.

Next task:
- DD-0002

Blockers (if blocked):
- (none)

## 2026-01-15 02:21 UTC — CLI-0507 — ADR: Scaffold a full handbook instance filesystem

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/ADR-CLI-0002-handbook-instance-scaffolding.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0507)

Goal:
- Define an implementable `ph` approach for scaffolding a full handbook instance repo filesystem (offline-capable, deterministic, no overwrites) and record decisions around internal state placement and documentation conventions.

Work performed (ordered):
1. Authored `ADR-CLI-0002` defining a recommended scaffolding command surface (`ph scaffold full` / `ph init --full`), embedded template strategy, and upgrade direction.
2. Documented guidance on internal state location (`.project-handbook/**` preferred over introducing `.ph/`) and documentation placement (keep handbook docs conventional; keep CLI product docs in the CLI repo).
3. Updated `cli_plan/AI_AGENT_START_HERE.md` to link the new ADR.

Commands executed (exact):
- (none; docs-only)

Files changed (exact paths):
- cli_plan/AI_AGENT_START_HERE.md
- cli_plan/session_logs.md
- cli_plan/tasks.json
- cli_plan/v1_cli/ADR-CLI-0002-handbook-instance-scaffolding.md

Verification:
- (docs change only)

Outcome:
- status: done
- summary: Added an ADR defining how `ph` should scaffold a full handbook instance filesystem (offline, deterministic, non-destructive) and captured the recommendation to keep internal state under `.project-handbook/**`.

Next task:
- NONE

Blockers (if blocked):
- (none)

## 2026-01-15 03:18 UTC — CLI-0508 — ADR + contract: adopt .ph internals and ph content layout; remove system scope

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/ADR-CLI-0002-handbook-instance-scaffolding.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0508)

Goal:
- Define the v1 “ph inside any project repo” layout: `.ph/**` for CLI-owned internals, `ph/**` for handbook content, marker `.ph/config.json`, and remove system scope.

Work performed (ordered):
1. Authored `ADR-CLI-0003` defining the on-project layout: `.ph/**` for CLI-owned internals, `ph/**` for handbook content, marker `.ph/config.json`, and explicitly removing system scope.
2. Updated `cli_plan/v1_cli/CLI_CONTRACT.md` to match the new marker, path roots, required assets, and hook/validation/history outputs under `.ph/**`.
3. Removed system-scope and migration-command semantics from the contract (no `--scope system`, no `ph migrate ...`; removed `hb-*` mappings).
4. Updated `cli_plan/AI_AGENT_START_HERE.md` + `cli_plan/tasks.json` to reference the new marker and the new primary ADR.

Commands executed (exact):
- `make validate-quick`

Files changed (exact paths):
- cli_plan/AI_AGENT_START_HERE.md
- cli_plan/session_logs.md
- cli_plan/tasks.json
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/ADR-CLI-0002-handbook-instance-scaffolding.md
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md

Verification:
- `make validate-quick`
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: Locked in the v1 on-project layout (`.ph/**` internals + `ph/**` content) with marker `.ph/config.json`, removed system scope and migration commands from the contract, and updated start-here + task config to match.

Next task:
- NONE

Blockers (if blocked):
- (none)

## 2026-01-15 03:50 UTC — CLI-0509 — Specify full ph/** content scaffold + seed files for ph init

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0509)

Goal:
- Specify the full `ph/**` handbook content scaffold and required seed files that `ph init` should create (non-destructive), including `ph/roadmap/now-next-later.md`.

Work performed (ordered):
1. Inventoried the legacy handbook repo directories and identified the intended `ph/**` content subtree (excluding `docs/` and all CLI internals).
2. Updated `ADR-CLI-0003` with an explicit scaffold spec for both `ph/**` (content) and `.ph/**` (internals), including the required seed file `ph/roadmap/now-next-later.md`.
3. Updated `CLI_CONTRACT.md` so `ph init` is contractually required to create the enumerated `ph/**` directory structure + seed file (non-destructive; no overwrites).

Commands executed (exact):
- `make validate-quick`

Files changed (exact paths):
- cli_plan/session_logs.md
- cli_plan/tasks.json
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md

Verification:
- `make validate-quick`
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: Documented the full `ph/**` content scaffold (plus seed files like `ph/roadmap/now-next-later.md`) and updated the contract so `ph init` must create it without overwriting existing files.

Next task:
- NONE

Blockers (if blocked):
- (none)

## 2026-01-15 15:54 UTC — CLI-0510 — Add ph init gitignore flags

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0510)

Goal:
- Define `ph init` flags `--gitignore` / `--no-gitignore` and specify deterministic, idempotent `.gitignore` behavior.

Work performed (ordered):
1. Updated `ADR-CLI-0003` to specify `ph init` gitignore behavior and the default (ignore `.ph/`, not `ph/`).
2. Updated `CLI_CONTRACT.md` `ph init` to add `--gitignore` / `--no-gitignore` with deterministic, idempotent `.gitignore` semantics.

Commands executed (exact):
- `make validate-quick`

Files changed (exact paths):
- cli_plan/session_logs.md
- cli_plan/tasks.json
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md

Verification:
- `make validate-quick`
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: Added `ph init` gitignore control in the contract/ADR (`--gitignore` default on, `--no-gitignore` opt-out) and specified that only `.ph/` is ignored by default.

Next task:
- NONE

Blockers (if blocked):
- (none)

## 2026-01-16 00:36 UTC — CLI-0511 — Scaffold cli_plan/ph_spec with examples + per-dir contracts

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/tasks.json (task CLI-0511)

Goal:
- Create `cli_plan/ph_spec/` mirroring the `ph/**` content-tree scaffold, with per-directory `contract.md` files and representative real examples copied from this repo.

Work performed (ordered):
1. Created `cli_plan/ph_spec/` and mirrored the full `ph/**` content-tree scaffold into `cli_plan/ph_spec/ph/**` with `examples/` + `contract.md` in every directory.
2. Copied representative real examples from this repo into the appropriate `examples/` folders (ADR, backlog items, contracts, feature, sprint plan + a task, roadmap, status artifacts).
3. Updated `contract.md` stubs to include minimal front matter so handbook validation passes.

Commands executed (exact):
- `make validate-quick`

Files changed (exact paths):
- cli_plan/ph_spec/**
- cli_plan/session_logs.md
- cli_plan/tasks.json

Verification:
- `make validate-quick`
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: Added `cli_plan/ph_spec/` scaffold with per-directory contracts and real examples; validation passes.

Next task:
- NONE

Blockers (if blocked):
- Missing local examples in this repo for: `ph/features/implemented/`, `ph/releases/delivered/`, and all `ph/parking-lot/**` category directories (only `parking-lot/index.json` exists here).

## 2026-01-16 01:03 UTC — CLI-0512 — Update ph_spec for releases + parking-lot examples; remove features implemented

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/ph_spec/**
- cli_plan/tasks.json (task CLI-0512)

Goal:
- Update the `ph/**` scaffold + `cli_plan/ph_spec/` to (1) use `releases/current/` directory + `releases/delivered/` versions, (2) populate parking-lot examples from archived items, and (3) remove `features/implemented/`.

Work performed (ordered):
1. Updated ADR + contract to remove `features/implemented/` from the scaffold, and to model releases as `releases/planning/`, `releases/current/` (directory), and `releases/delivered/<version>/`.
2. Updated `cli_plan/ph_spec/` to match (removed `ph/features/implemented/`, added `ph/features/archive/`, added `ph/releases/current/` + `ph/releases/planning/`, populated releases examples, and copied parking-lot archived items into the relevant examples directories).

Commands executed (exact):
- `make validate-quick`

Files changed (exact paths):
- cli_plan/ph_spec/**
- cli_plan/session_logs.md
- cli_plan/tasks.json
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md

Verification:
- `make validate-quick`
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: `ph_spec` now reflects the updated releases layout and removes the incorrect `features/implemented` concept; parking-lot examples are sourced from archived items where available.

Next task:
- NONE

Blockers (if blocked):
- Missing local examples in this repo for: `ph/features/archive/`, `ph/parking-lot/features/` + `ph/parking-lot/archive/features/`, and `ph/parking-lot/external-requests/` + `ph/parking-lot/archive/external-requests/`.

## 2026-01-17 02:19 UTC — CLI-0513 — Add sprint-plan scaffold example + current symlink to ph_spec

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/ph_spec/**
- cli_plan/tasks.json (task CLI-0513)

Goal:
- Add an explicit example of `ph sprint plan` outputs (plan.md + tasks dir + `sprints/current` symlink) under `cli_plan/ph_spec/ph/sprints/examples/`.

Work performed (ordered):
1. Added a sprint scaffold example under `cli_plan/ph_spec/ph/sprints/examples/scaffold/` including `sprints/<year>/<SPRINT-...>/plan.md` and an empty `tasks/` directory.
2. Added a `sprints/current` symlink for the example (`cli_plan/ph_spec/ph/sprints/examples/scaffold/current` → `2026/SPRINT-2026-01-11`).

Commands executed (exact):
- `make validate-quick`

Files changed (exact paths):
- cli_plan/ph_spec/ph/sprints/examples/scaffold/**
- cli_plan/session_logs.md
- cli_plan/tasks.json

Verification:
- `make validate-quick`
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: `cli_plan/ph_spec` now includes an explicit sprint-plan scaffold example with a `current` symlink and the expected sprint directory skeleton.

Next task:
- NONE

Blockers (if blocked):
- (none)

## 2026-01-17 02:55 UTC — CLI-0514 — Create due-diligence.json task list for ph_spec contract completion

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/ph_spec/**
- cli_plan/tasks.json (task CLI-0514)

Goal:
- Create `cli_plan/due-diligence.json` with an exhaustive task list for validating `ph_spec` examples and writing explicit per-area contracts for documents/commands.

Work performed (ordered):
1. Enumerated every `cli_plan/ph_spec/ph/**/contract.md` directory and created a corresponding due-diligence task to validate examples and write an explicit contract.
2. Added cross-cutting due-diligence tasks for taxonomy decisions (parking-lot categories), lifecycle contracts (releases/sprints), symlink policy, and validation-rule alignment.

Commands executed (exact):
- `make validate-quick`

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/tasks.json

Verification:
- `make validate-quick`
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: Added `cli_plan/due-diligence.json` with an exhaustive ph_spec contract-completion checklist (per-directory + cross-cutting).

Next task:
- NONE

Blockers (if blocked):
- (none)

## 2026-01-15 00:52 UTC — CLI-0506 — Enhance ph init to scaffold required repo assets

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0506)

Goal:
Make `ph init` create the minimum required repo assets so a fresh directory passes `ph doctor`.

Work performed (ordered):
1. Updated the CLI contract so `ph init` is specified to create the minimum required repo assets (in addition to the root marker).
2. Updated `ph init` to create missing required files/directories with safe default JSON (no overwrites).
3. Updated integration tests and verified `ph init` + `ph doctor` succeed in a brand-new directory.

Commands executed (exact):
- `uv run ruff format . && uv run ruff check . && uv run pytest -q && uv run mkdocs build`
- `uv --project /Users/spensermcconnell/__Active_Code/project-handbook-cli run ph --root <tmpdir> init`
- `uv --project /Users/spensermcconnell/__Active_Code/project-handbook-cli run ph --root <tmpdir> doctor`

Files changed (exact paths):
- cli_plan/session_logs.md
- cli_plan/tasks.json
- cli_plan/v1_cli/CLI_CONTRACT.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/docs/quickstart.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/init_repo.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_init.py

Verification:
- `uv run pytest -q`
  - 124 passed
- `uv --project /Users/spensermcconnell/__Active_Code/project-handbook-cli run ph --root <tmpdir> init` then `... doctor`
  - `ph doctor` exit 0 with all required assets OK

Outcome:
- status: done
- summary: `ph init` now scaffolds the required repo assets so a fresh directory passes `ph doctor`.

Next task:
- (none) — No runnable tasks. All tasks are done.

Blockers (if blocked):
- (none)

## 2026-01-14 23:28 UTC — CLI-0505 — Implement ph init and update CLI contract

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0505)

Goal:
Add `ph init` to create `cli_plan/project_handbook.config.json` for new handbook instance repos, and update the CLI contract/docs to reflect the new command.

Work performed (ordered):
1. Updated `cli_plan/v1_cli/CLI_CONTRACT.md` to define `ph init` and document the root resolution exception.
2. Implemented `ph init` in the installed CLI so it runs without an existing root marker and skips post-command hooks on success.
3. Added deterministic integration tests and documented `ph init` in MkDocs quickstart.

Commands executed (exact):
- `uv run ruff format . && uv run ruff check . && uv run pytest -q`
- `uv run mkdocs build`

Files changed (exact paths):
- cli_plan/session_logs.md
- cli_plan/tasks.json
- cli_plan/v1_cli/CLI_CONTRACT.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/docs/quickstart.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/help_text.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/hooks.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/init_repo.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_init.py

Verification:
- `uv run pytest -q`
  - 124 passed
- `uv run mkdocs build`
  - exits 0

Outcome:
- status: done
- summary: Added `ph init` (root marker initializer) with contract update, docs, and deterministic tests; successful `ph init` runs skip post-command hooks.

Next task:
- (none) — No runnable tasks. All tasks are done.

Blockers (if blocked):
- (none)

## 2026-01-14 22:04 UTC — CLI-0504 — Implement ph migrate system-scope

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0504)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/migrate_system_scope.py
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/system_scope_config.json

Goal:
Implement `ph migrate system-scope` by porting v0 deterministic migration + link rewrite behavior, enforcing the confirmations + JSON stdout contract, and adding deterministic integration tests.

Work performed (ordered):
1. Ported v0 migration + link rewrite logic into the CLI as `src/ph/migrate_system_scope.py`, adapting to PH_ROOT and PH_ROOT-relative JSON output.
2. Added `ph migrate system-scope` command wiring with strict `--confirm RESET --force true` gating (exit 2 with empty stdout on mismatch).
3. Added deterministic integration tests for successful moves/JSON contract and confirmation failure; suppressed post-hook validation output for `migrate` to keep stdout JSON-only.

Commands executed (exact):
- `uv run ruff format . && uv run ruff check . && uv run pytest -q`

Files changed (exact paths):
- cli_plan/session_logs.md
- cli_plan/tasks.json
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/hooks.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/migrate_system_scope.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_migrate_system_scope.py

Verification:
- `uv run pytest -q`
  - 122 passed

Outcome:
- status: done
- summary: Added `ph migrate system-scope` with v0-parity moves + link rewriting and stable JSON stdout contract, plus deterministic tests and confirmation gating.

Next task:
- (none) — No runnable tasks. All tasks are done.

Blockers (if blocked):
- (none)

## 2026-01-14 21:57 UTC — CLI-0503 — Implement ph reset-smoke

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0503)
- /Users/spensermcconnell/__Active_Code/project-handbook/docs/RESET_SMOKE.md
- /Users/spensermcconnell/__Active_Code/project-handbook/Makefile (target `reset-smoke`)

Goal:
Implement `ph reset-smoke` as a deterministic end-to-end reset proof, matching the documented procedure and hook-skip semantics, with an integration test.

Work performed (ordered):
1. Implemented `ph reset-smoke` orchestration inside the CLI (no subprocess calls), executing the 5-step procedure in order across both scopes.
2. Added explicit filesystem assertions for project deletion and system preservation, plus explicit `ph validate --quick` and post-reset `ph sprint plan`.
3. Added deterministic integration test that runs `ph --root <PH_ROOT> reset-smoke` and verifies outcomes + hook skip behavior.

Commands executed (exact):
- `uv run ruff format . && uv run ruff check . && uv run pytest -q`

Files changed (exact paths):
- cli_plan/session_logs.md
- cli_plan/tasks.json
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/reset_smoke.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_reset_smoke.py

Verification:
- `uv run pytest -q`
  - 120 passed

Outcome:
- status: done
- summary: Added contract-aligned `ph reset-smoke` orchestration with deterministic assertions + health checks, and an integration test; successful runs skip the post-command hook.

Next task:
- CLI-0504

Blockers (if blocked):
- (none)

## 2026-01-14 21:52 UTC — CLI-0502 — Implement ph reset

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0502)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/reset_manager.py
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/reset_spec.json

Goal:
Port v0 reset behavior into the installed CLI as `ph reset` (dry-run by default), including template rewrites and hook-skip behavior, with deterministic integration tests.

Work performed (ordered):
1. Ported `process/automation/reset_manager.py` into the CLI as `src/ph/reset.py`, preserving safety invariants and report output while updating Make-era template commands to `ph`.
2. Wired the new `reset` command into `src/ph/cli.py` with `--spec/--confirm/--force` arguments.
3. Added deterministic integration tests covering dry-run safety, execute deletion/preservation, template rewrites, and hook-skip behavior.

Commands executed (exact):
- `uv run ruff format . && uv run ruff check . && uv run pytest -q`

Files changed (exact paths):
- cli_plan/session_logs.md
- cli_plan/tasks.json
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/reset.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_reset.py

Verification:
- `uv run pytest -q`
  - 119 passed

Outcome:
- status: done
- summary: Added `ph reset` with v0-parity safety + templates, CLI-style execution confirmations, and integration tests; successful reset skips post-command hook.

Next task:
- CLI-0503

Blockers (if blocked):
- (none)

## 2026-01-14 21:47 UTC — CLI-0501 — Create cli_plan/PARITY_CHECKLIST.md and link it

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0501)
- cli_plan/v0_make/MAKE_CONTRACT.md

Goal:
Create an exhaustive, deterministic parity checklist for the Make→CLI mapping, and link it from the v1 CLI planning index.

Work performed (ordered):
1. Extracted the exhaustive Make-to-CLI mapping list from `cli_plan/v1_cli/CLI_CONTRACT.md`.
2. Created `cli_plan/PARITY_CHECKLIST.md` enumerating every mapping with preconditions and PH_ROOT-relative output paths.
3. Linked the checklist from `cli_plan/AI_AGENT_START_HERE.md`.

Commands executed (exact):
- `sed -n '760,1080p' cli_plan/v1_cli/CLI_CONTRACT.md`
- `sed -n '360,650p' cli_plan/v0_make/MAKE_CONTRACT.md`
- `python3 - <<'PY' ... PY` (verify every `make ...` mapping appears in the checklist)

Files changed (exact paths):
- cli_plan/AI_AGENT_START_HERE.md
- cli_plan/PARITY_CHECKLIST.md
- cli_plan/session_logs.md
- cli_plan/tasks.json

Verification:
- Verified coverage: all `make ...` commands in the contract mapping appear in `cli_plan/PARITY_CHECKLIST.md` (0 missing).

Outcome:
- status: done
- summary: Added an exhaustive Make→CLI parity checklist and linked it from the v1 execution plan index.

Next task:
- CLI-0502

Blockers (if blocked):
- (none)

## 2026-01-14 20:46 UTC — CLI-0462 — Implement ph roadmap validate

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0462)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/roadmap_manager.py

Goal:
- Implement project-only `ph roadmap validate` with deterministic link parsing/validation rules and integration tests for failure/success and system-scope rejection.

Work performed (ordered):
1. Implemented `ph roadmap validate` link extraction + filesystem validation, including outside-root detection and exact success/failure output lines.
2. Added integration tests for broken-link failure, pass case, and system-scope remediation behavior.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/roadmap.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_roadmap_validate.py

Verification:
- uv run pytest -q
  - 105 passed

Outcome:
- status: done
- summary: Added project-only `ph roadmap validate` with contract-aligned link rules and integration tests for broken-link failure/success.

Next task:
- CLI-0471

Blockers (if blocked):
- (none)

## 2026-01-14 20:43 UTC — CLI-0461 — Implement ph roadmap create and show

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0461)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/reset_manager.py
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/roadmap_manager.py

Goal:
- Implement project-only `ph roadmap create` and `ph roadmap show` (reset template + extracted view) with integration tests and exact error/remediation lines.

Work performed (ordered):
1. Added `ph roadmap` command group with project-only scope enforcement and exact remediation line for system scope.
2. Implemented `ph roadmap create` using the v0 reset template content for `roadmap/now-next-later.md`.
3. Implemented `ph roadmap show` extracted view (v0 headings + section grouping) with integration tests.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/roadmap.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_roadmap_create_show.py

Verification:
- uv run pytest -q
  - 103 passed

Outcome:
- status: done
- summary: Added project-only `ph roadmap create` and `ph roadmap show` with exact error/remediation lines and integration tests.

Next task:
- CLI-0462

Blockers (if blocked):
- (none)

## 2026-01-14 20:42 UTC — CLI-0453 — Implement ph parking promote default target later

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0453)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/parking_lot_manager.py

Goal:
- Implement `ph parking promote` as a v0 behavioral port with default target=later, project-only roadmap writes, and deterministic integration tests.

Work performed (ordered):
1. Implemented `ph parking promote` with default `--target later`, copying the item into `roadmap/<target>/` and removing the original parking-lot directory (v0 behavior).
2. Added integration tests for default target behavior and the exact system-scope rejection message/exit code.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_parking_promote.py

Verification:
- uv run pytest -q
  - 101 passed

Outcome:
- status: done
- summary: Implemented `ph parking promote` (default target=later) with deterministic tests and an exact system-scope rejection line.

Next task:
- CLI-0461

Blockers (if blocked):
- (none)

## 2026-01-14 20:39 UTC — CLI-0452 — Implement ph parking list and ph parking review

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0452)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/parking_lot_manager.py

Goal:
- Implement `ph parking list` and `ph parking review` as v0 behavioral ports (including index auto-generation) with deterministic integration tests.

Work performed (ordered):
1. Ported v0 parking list/review behavior (including JSON/table formats and review instruction block) and ensured JSON output is parseable (no index refresh banner).
2. Added deterministic integration tests covering list (json/table), review headings, and system-scope list output.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/parking_lot_manager.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_parking_list_review.py

Verification:
- uv run pytest -q
  - 99 passed

Outcome:
- status: done
- summary: Implemented `ph parking list` and `ph parking review` with deterministic integration tests, including JSON output that is cleanly parseable.

Next task:
- CLI-0453

Blockers (if blocked):
- (none)

## 2026-01-14 20:34 UTC — CLI-0451 — Implement ph parking add + index maintenance + hints

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0451)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/parking_lot_manager.py
- /Users/spensermcconnell/__Active_Code/project-handbook/Makefile

Goal:
- Implement `ph parking add` as a v0 behavioral port (scope-local data root, v0 templates/indexing, project-only hint block) with deterministic integration tests.

Work performed (ordered):
1. Ported v0 parking-lot item creation + indexing into the installed CLI (scope-local under `PH_DATA_ROOT/parking-lot/`).
2. Wired `ph parking add` into the CLI parser/dispatch and added the contract hint block (project scope only).
3. Added deterministic integration test asserting item creation, index maintenance, and hint block behavior (project + system).

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/parking.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/parking_lot_manager.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_parking_add.py

Verification:
- uv run pytest -q
  - 97 passed

Outcome:
- status: done
- summary: Implemented `ph parking add` as a v0-style port with deterministic integration tests and a project-only hint block.

Next task:
- CLI-0452

Blockers (if blocked):
- (none)

## 2026-01-14 20:02 UTC — CLI-0445 — Implement `ph backlog rubric` and `ph backlog stats`

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/v0_make/MAKE_CONTRACT.md
- cli_plan/tasks.json (task CLI-0445)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/backlog_manager.py

Goal:
- Implement `ph backlog rubric` and `ph backlog stats` as v0 behavioral ports with deterministic integration tests.

Work performed (ordered):
1. Wired `ph backlog rubric` and `ph backlog stats` into the CLI parser/dispatch.
2. Ported v0 rubric and stats outputs into the installed CLI (scope-local).
3. Added deterministic integration tests asserting the exact headers and total issue count for a fixed fixture.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/backlog.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/backlog_manager.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_backlog_rubric_stats.py

Verification:
- uv run pytest -q
  - 95 passed

Outcome:
- status: done
- summary: Implemented `ph backlog rubric` and `ph backlog stats` as v0-style ports with deterministic tests (headers + total issue count).

Next task:
- CLI-0451

Blockers (if blocked):
- (none)

## 2026-01-14 19:57 UTC — CLI-0444 — Implement `ph backlog assign` (default sprint=current)

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/v0_make/MAKE_CONTRACT.md
- cli_plan/tasks.json (task CLI-0444)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/backlog_manager.py

Goal:
- Implement `ph backlog assign` (default sprint=current) by porting v0 sprint resolution + front-matter update ordering, with deterministic integration tests.

Work performed (ordered):
1. Added `ph backlog assign` subcommand wiring (argparse + dispatch), defaulting `--sprint` to `current`.
2. Ported v0 assignment behavior (sprint resolution + ordered front-matter update + index refresh) with `ph` substitutions in the printed next steps.
3. Added deterministic integration tests for assignment success (project + system) and missing-current-sprint failure output.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/backlog.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/backlog_manager.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_backlog_assign.py

Verification:
- uv run pytest -q
  - 92 passed

Outcome:
- status: done
- summary: Implemented `ph backlog assign` (default `--sprint current`) with v0-style outputs, ordered front-matter edits, and deterministic tests (project + system).

Next task:
- CLI-0445

Blockers (if blocked):
- (none)

## 2026-01-14 19:54 UTC — CLI-0443 — Implement `ph backlog triage`

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/v0_make/MAKE_CONTRACT.md
- cli_plan/tasks.json (task CLI-0443)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/backlog_manager.py

Goal:
- Implement `ph backlog triage` as a v0 behavioral port (P0 template generation + display) with deterministic integration tests.

Work performed (ordered):
1. Added `ph backlog triage` subcommand wiring (argparse + dispatch).
2. Ported v0 triage behavior into the installed CLI (display existing triage.md; generate template for missing P0 triage.md).
3. Added deterministic integration tests for generation, display, and not-found error handling.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/backlog.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/backlog_manager.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_backlog_triage.py

Verification:
- uv run pytest -q
  - 89 passed

Outcome:
- status: done
- summary: Implemented `ph backlog triage` with v0-style output and deterministic tests (P0 regeneration + display; exact not-found message).

Next task:
- CLI-0444

Blockers (if blocked):
- (none)

## 2026-01-14 19:49 UTC — CLI-0442 — Implement `ph backlog list`

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/v0_make/MAKE_CONTRACT.md
- cli_plan/tasks.json (task CLI-0442)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/backlog_manager.py

Goal:
- Implement `ph backlog list` (table/json output + filters) as a v0 behavioral port with deterministic integration tests.

Work performed (ordered):
1. Added `ph backlog list` (table/json output + filters) and wired it into the CLI parser/dispatch.
2. Ported v0 listing output (headings/grouping) while ensuring `--format json` prints pure JSON (quiet index refresh).
3. Added deterministic integration tests for json output and filter behavior (project + system).

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/backlog.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/backlog_manager.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_backlog_list.py

Verification:
- uv run pytest -q
  - 87 passed

Outcome:
- status: done
- summary: Implemented `ph backlog list` with `table|json` output + filters, plus deterministic integration tests and pure-JSON stdout for `--format json`.

Next task:
- CLI-0443

Blockers (if blocked):
- (none)

## 2026-01-14 19:43 UTC — CLI-0441 — Implement `ph backlog add` + index maintenance + hints

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/v0_make/MAKE_CONTRACT.md
- cli_plan/tasks.json (task CLI-0441)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/backlog_manager.py

Goal:
- Implement `ph backlog add` as a v0 behavioral port (dir layout + templates + index) and append the exact project-scope hint block.

Work performed (ordered):
1. Wired `ph backlog add` into the CLI parser/dispatch.
2. Ported v0 backlog creation logic (README + P0 triage template + index update) into the installed CLI, using scope-local `<PH_DATA_ROOT>/backlog`.
3. Added deterministic integration tests (project + system) verifying ID format, index updates, and the project-only hint block.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/backlog.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/backlog_manager.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_backlog_add.py

Verification:
- uv run pytest -q
  - 85 passed

Outcome:
- status: done
- summary: Implemented `ph backlog add` with v0 templates/output, scope-local index maintenance, and deterministic tests (project hint block appended; system suppresses it).

Next task:
- CLI-0442

Blockers (if blocked):
- (none)

## 2026-01-14 19:16 UTC — CLI-0434 — Implement `ph feature archive`

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0434)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/feature_manager.py

Goal:
- Implement `ph feature archive` as a v0 behavioral port (stage gate + completeness checks + move), with deterministic tests (project + system).

Work performed (ordered):
1. Ported v0 `archive_feature(...)` logic into the installed CLI (stage gate, completeness audits, and scope-local move).
2. Substituted `force=true` wording with `--force` in refusal + completeness messaging while preserving v0 headings/structure.
3. Added deterministic integration tests for success, stage-blocked, and forced-archive behaviors (project + system).

Commands executed (exact):
- uv run ruff check --fix src/ph/cli.py src/ph/feature_archive.py
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/feature_archive.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_feature_archive.py

Verification:
- uv run pytest -q
  - 82 passed

Outcome:
- status: done
- summary: Implemented `ph feature archive` (stage gate + completeness checks + scope-local move) with deterministic tests and v0-style messaging (`--force` substitution).

Next task:
- CLI-0441

Blockers (if blocked):
- (none)

## 2026-01-14 19:10 UTC — CLI-0433 — Implement `ph feature update-status` and `ph feature summary`

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0433)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/feature_status_updater.py

Goal:
- Implement `ph feature update-status` and `ph feature summary` by porting v0 feature auto-status computation; add deterministic tests for both scopes.

Work performed (ordered):
1. Ported v0 `feature_status_updater.py` into the installed CLI with scope-local sprint scanning (active + archived).
2. Added `ph feature update-status` (auto section rewrite) and `ph feature summary` (v0 header + formatting).
3. Added deterministic integration tests verifying auto section replacement and summary output for project + system scopes.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/feature_status_updater.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_feature_update_status_and_summary.py

Verification:
- uv run pytest -q
  - 78 passed

Outcome:
- status: done
- summary: Implemented `ph feature update-status` and `ph feature summary` as v0 behavioral ports with deterministic integration tests in both scopes.

Next task:
- CLI-0434

Blockers (if blocked):
- (none)

## 2026-01-14 19:05 UTC — CLI-0432 — Implement `ph feature status`

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0432)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/feature_manager.py

Goal:
- Implement `ph feature status` (v0 stage update + date update) and add deterministic tests for project + system scopes.

Work performed (ordered):
1. Added `ph feature status` subcommand wiring and preserved v0 success/not-found messages.
2. Ported v0 stage + front-matter date update behavior into the installed CLI (scope-local).
3. Added deterministic integration tests for success + not-found behavior in both scopes.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/feature.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_feature_status.py

Verification:
- uv run pytest -q
  - 76 passed

Outcome:
- status: done
- summary: Implemented `ph feature status` with v0-compatible stage/date updates and deterministic tests for both scopes.

Next task:
- CLI-0433

Blockers (if blocked):
- (none)

## 2026-01-14 19:00 UTC — CLI-0431 — Implement `ph feature create` + `ph feature list` + guardrails + hints

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0431)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/feature_manager.py
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/data_root.py
- /Users/spensermcconnell/__Active_Code/project-handbook/Makefile

Goal:
- Implement `ph feature create` + `ph feature list` with v0 templates, scope guardrail, and hint blocks; add deterministic integration tests for both scopes.

Work performed (ordered):
1. Added `ph feature create` and `ph feature list` command wiring to the installed CLI.
2. Ported v0 feature scaffolding templates with deterministic dates and appended the scope-correct hint block (Make-era guidance rewritten to `ph`).
3. Implemented project-scope guardrail for system-scoped feature names based on routing rules.
4. Added deterministic integration tests for create/list and guardrail in both scopes.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/feature.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_feature_create_list.py

Verification:
- uv run pytest -q
  - 72 passed

Outcome:
- status: done
- summary: Implemented `ph feature create/list` with v0 templates + outputs, scope-aware hint block, and deterministic tests (including system-name guardrail).

Next task:
- CLI-0432

Blockers (if blocked):
- (none)

## 2026-01-14 18:52 UTC — CLI-0423 — Implement `ph task status` updates

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0423)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/task_manager.py
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/work_item_archiver.py
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/data_root.py

Goal:
- Implement `ph task status` (dependency enforcement + archiving) + integration tests for both scopes.

Work performed (ordered):
1. Added `ph task status` subcommand and dispatcher wiring with `--force` dependency override behavior.
2. Ported v0 work-item archiving into the installed CLI (scope-local), including backlog + parking-lot index refresh.
3. Added deterministic integration tests covering dependency failure, forced transition, and archiving for project + system scopes.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/backlog_manager.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/parking_lot_manager.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/task_status.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/work_item_archiver.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_task_status.py

Verification:
- uv run pytest -q
  - 69 passed

Outcome:
- status: done
- summary: Implemented `ph task status` with v0-style dependency enforcement + scope-local work-item archiving, plus deterministic integration tests.

Next task:
- CLI-0431

Blockers (if blocked):
- (none)

## 2026-01-14 17:52 UTC — CLI-0412 — Implement `ph sprint status` and `ph sprint tasks`

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0412)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/sprint_manager.py
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/task_manager.py

Goal:
- Implement `ph sprint status` and `ph sprint tasks` for both scopes with v0-style stdout ordering (Make-era command references rewritten to `ph`).

Work performed (ordered):
1. Ported `sprint_manager.py --status` output into `ph.sprint_status.run_sprint_status` (scope-aware, uses `sprints/current` and sprint plan metadata).
2. Ported `task_manager.py --list` output into `ph.sprint_tasks.run_sprint_tasks` and wired both into `ph sprint`.
3. Updated `ph dashboard` to invoke the new internal sprint status implementation and added integration tests that seed a sprint + task in both scopes.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/dashboard.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/sprint_status.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/sprint_tasks.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_sprint_status_and_tasks.py

Verification:
- uv run pytest -q
  - 56 passed

Outcome:
- status: done
- summary: Added `ph sprint status` and `ph sprint tasks` with scope-aware v0-style outputs, plus integration tests for both scopes.

Next task:
- CLI-0413

Blockers (if blocked):
- (none)

## 2026-01-14 17:47 UTC — CLI-0411 — Implement `ph sprint plan` and `ph sprint open`

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0411)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/sprint_manager.py

Goal:
- Implement `ph sprint plan` and `ph sprint open` with scope-aware outputs and contract-correct hint blocks.

Work performed (ordered):
1. Ported sprint plan template + symlink behavior into `ph.sprint` / `ph.sprint_commands` (scope-aware under `PH_DATA_ROOT`).
2. Added CLI wiring for `ph sprint plan [--sprint] [--force]` and `ph sprint open --sprint <id>`.
3. Added integration tests for plan/open in both project and system scopes (including the exact hint blocks and system release-context exclusions).

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/sprint.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/sprint_commands.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_sprint_plan_open.py

Verification:
- uv run pytest -q
  - 54 passed

Outcome:
- status: done
- summary: Added `ph sprint plan/open` with scope-aware skeleton creation and exact hint blocks, plus integration tests.

Next task:
- CLI-0412

Blockers (if blocked):
- (none)

## 2026-01-14 17:43 UTC — CLI-0403 — Implement `ph dashboard`

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0403)
- /Users/spensermcconnell/__Active_Code/project-handbook/Makefile (dashboard targets)

Goal:
- Implement `ph dashboard` with exact banner lines and daily listing rules.

Work performed (ordered):
1. Implemented `ph dashboard` with exact project/system banners and Make-parity daily listing rules (`status/daily/*.md`, non-recursive).
2. Added an internal sprint status implementation hook (`ph.sprint_status`) and invoked the existing `ph validate` implementation (no shelling out).
3. Added integration tests for banner parity and daily listing (last-3 and empty state).

Commands executed (exact):
- uv run ruff check . --fix
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/dashboard.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/sprint_status.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_dashboard.py

Verification:
- uv run pytest -q
  - 52 passed

Outcome:
- status: done
- summary: Added `ph dashboard` with exact banners and daily listing behavior, plus integration tests.

Next task:
- CLI-0411

Blockers (if blocked):
- (none)

## 2026-01-14 17:38 UTC — CLI-0402 — Implement `ph status`

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0402)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/generate_project_status.py

Goal:
- Implement `ph status` with scope-aware outputs and exact stdout framing.

Work performed (ordered):
1. Added a `ph status` command that writes `<PH_DATA_ROOT>/status/current.json` and `<PH_DATA_ROOT>/status/current_summary.md`.
2. Implemented the exact `Generated:`/`Updated:` stdout lines (absolute paths) and summary wrapper framing.
3. Added integration tests validating outputs for both project and system scopes.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/status.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_status.py

Verification:
- uv run pytest -q
  - 49 passed

Outcome:
- status: done
- summary: Added `ph status` with scope-aware output paths and exact stdout framing.

Next task:
- CLI-0403

Blockers (if blocked):
- (none)

## 2026-01-14 17:29 UTC — CLI-0401 — Implement `ph daily`

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0401)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/daily_status_check.py

Goal:
- Implement `ph daily generate|check` with weekend skipping and scope-aware output paths.

Work performed (ordered):
1. Ported `daily_status_check.py` into `ph.daily` using `PH_ROOT` + scope-aware `PH_DATA_ROOT`.
2. Added deterministic clock helpers (`ph.clock`) and fixed argparse global option handling so `--root/--scope` work before or after subcommands.
3. Added integration tests covering weekend skip vs `--force` and project/system output paths.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/clock.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/daily.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_daily.py

Verification:
- uv run pytest -q
  - 47 passed

Outcome:
- status: done
- summary: Added `ph daily` generate/check with scope-aware outputs and deterministic tests.

Next task:
- CLI-0402

Blockers (if blocked):
- (none)

## 2026-01-14 15:42 UTC — CLI-0204 — Implement post-command hook pipeline

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0204)

Goal:
- Implement the centralized post-command hook pipeline (history + validate-quick) with all skip rules and flags per contract.

Work performed (ordered):
1. Added a centralized post-command hook planner + runner (`ph.hooks`) implementing all skip rules (validate/reset/reset-smoke, flags, and `PH_SKIP_POST_HOOK`).
2. Wired the hook runner into `ph` dispatch so history is appended on success/failure, and validate-quick runs only after successful non-validate commands.
3. Updated and added tests to cover the skip matrix and validate side effects.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q
- uv run ruff format . && uv run ruff check . && uv run pytest -q
- uv run pytest -q
- make validate-quick

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/hooks.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_history.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_hooks_plan.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_post_hook_integration.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_root_detection.py

Verification:
- uv run pytest -q
  - 33 passed
- make validate-quick
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: Implemented the centralized post-command hook pipeline (history + validate-quick) with full skip/flag coverage and tests.

Next task:
- CLI-0301

Blockers (if blocked):
- (none)

## 2026-01-14 15:49 UTC — CLI-0301 — Implement `ph help` + help topics

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0301)
- /Users/spensermcconnell/__Active_Code/project-handbook/Makefile (help targets)

Goal:
- Implement `ph help` and `ph help <topic>` output by transforming v0 Makefile help targets per the contract rules.

Work performed (ordered):
1. Ported the v0 Makefile help target output into `ph help` / `ph help <topic>` using contract-correct `ph` command examples.
2. Added a required `roadmap` help topic (CLI improvement) with minimal command synopsis.
3. Added tests covering topic availability, unknown-topic failure, and the `--scope system` hint requirement.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q
- make validate-quick

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/help_text.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_help_topics.py

Verification:
- uv run pytest -q
  - 36 passed
- make validate-quick
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: Implemented `ph help` and all required topics using transformed v0 Make help output, with tests.

Next task:
- CLI-0302

Blockers (if blocked):
- (none)

## 2026-01-14 15:58 UTC — CLI-0302 — Implement onboarding commands

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0302)
- /Users/spensermcconnell/__Active_Code/project-handbook/ONBOARDING.md
- /Users/spensermcconnell/__Active_Code/project-handbook/process/sessions/templates/

Goal:
- Implement onboarding renderers: `ph onboarding` and `ph onboarding session ...` with deterministic listing and remediation behavior.

Work performed (ordered):
1. Implemented `ph onboarding` to render `<PH_ROOT>/ONBOARDING.md`.
2. Implemented `ph onboarding session list` to discover templates and print deterministic, lexicographically sorted topics.
3. Implemented `ph onboarding session <topic>` and `continue-session` with the required remediation behavior.
4. Added tests covering list ordering, rendering, unknown topics, and missing latest_summary remediation.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q
- uv run pytest -q
- make validate-quick

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/onboarding.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_onboarding.py

Verification:
- uv run pytest -q
  - 41 passed
- make validate-quick
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: Added the onboarding command group and session template renderer behavior with deterministic listing and tests.

Next task:
- CLI-0303

Blockers (if blocked):
- (none)

## 2026-01-14 16:03 UTC — CLI-0303 — Implement utilities: `ph clean`

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0303)

Goal:
- Implement `ph clean` to remove Python cache artifacts (`*.pyc`, `__pycache__/`) under PH_ROOT with tests.

Work performed (ordered):
1. Implemented `ph clean` to remove `*.pyc` and `__pycache__/` under PH_ROOT (matching Make parity).
2. Added a deterministic test fixture asserting cache artifacts are removed.

Commands executed (exact):
- uv run ruff check --fix src/ph/cli.py
- uv run ruff format . && uv run ruff check . && uv run pytest -q
- make validate-quick

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/clean.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_clean.py

Verification:
- uv run pytest -q
  - 42 passed
- make validate-quick
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: Added `ph clean` with parity behavior and a unit test.

Next task:
- CLI-0304

Blockers (if blocked):
- (none)

## 2026-01-14 16:07 UTC — CLI-0304 — Implement utilities: `ph hooks install`

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0304)

Goal:
- Implement `ph hooks install` to write `.git/hooks/post-commit` and `.git/hooks/pre-push` with exact contents and executable bits, with tests.

Work performed (ordered):
1. Implemented `ph hooks install` to write `.git/hooks/post-commit` and `.git/hooks/pre-push` with contract-correct commands and executable bits.
2. Added a unit test asserting exact file contents and executable permissions.

Commands executed (exact):
- uv run ruff check --fix src/ph/git_hooks.py
- uv run ruff format . && uv run ruff check . && uv run pytest -q
- make validate-quick

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/git_hooks.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_hooks_install.py

Verification:
- uv run pytest -q
  - 43 passed
- make validate-quick
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: Added `ph hooks install` (git hook installer) with deterministic contents and tests.

Next task:
- CLI-0306

Blockers (if blocked):
- (none)

## 2026-01-14 16:09 UTC — CLI-0306 — Implement `ph end-session` (skip-codex mode) by porting v0 summarizer

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0306)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/session_summary.py
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/rollout_parser.py
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/project_config.py

Goal:
- Implement `ph end-session --skip-codex` to parse a rollout log, render a summary markdown, write latest + dated summary files, and update manifest.json.

Work performed (ordered):
1. Vendored a rollout parser and implemented `ph end-session` argument parsing (including non-exercised flags for parity).
2. Implemented `--skip-codex` mode to render a front-matter summary, write a dated summary + `latest_summary.md`, and update `manifest.json`.
3. Added an integration test that generates the required two-object rollout fixture and asserts outputs + manifest update.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q
- uv run pytest -q
- make validate-quick

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/end_session.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/rollout_parser.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_end_session_skip_codex.py

Verification:
- uv run pytest -q
  - 44 passed
- make validate-quick
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: Added `ph end-session --skip-codex` (rollout parsing, summary/manifest outputs) with an integration test.

Next task:
- CLI-0307

Blockers (if blocked):
- (none)

## 2026-01-14 16:18 UTC — CLI-0307 — Implement `ph end-session` codex integration + session-end artifacts

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0307)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/session_summary.py

Goal:
- Complete `ph end-session` by adding (1) session_end artifacts + index updates, and (2) non-skip codex mode support (manual verification, no tests invoking codex).

Work performed (ordered):
1. Extended `ph end-session --skip-codex` to generate session_end artifacts and update `process/sessions/session_end/session_end_index.json`.
2. Implemented non-`--skip-codex` codex-mode summarization via `codex exec` (manual verification documented in CLI repo README).
3. Added an integration test (no codex) asserting session_end artifacts and index updates are created in `continue-task` mode.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q
- make validate-quick

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/README.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/end_session.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_end_session_session_end_artifacts.py

Verification:
- uv run pytest -q
  - 45 passed
- make validate-quick
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: Completed `ph end-session` with session_end artifacts + codex-mode support, with tests that avoid calling codex.

Next task:
- CLI-0401

Blockers (if blocked):
- (none)

## 2026-01-14 15:28 UTC — CLI-0203 — Implement validation engine (ph validate)

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0203)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/checks/validate_docs.py
- /Users/spensermcconnell/__Active_Code/project-handbook/process/checks/validation_rules.json

Goal:
- Vendor the validator logic into the CLI and expose it as `ph validate` with the required flags and tests.

Work performed (ordered):
1. Vendored the repo validator logic into the CLI package and parameterized it on PH_ROOT + scope data root.
2. Implemented `ph validate` with `--quick` and `--silent-success` flags and correct report output paths per scope.
3. Added integration tests for project and system scope output locations and silent-success stdout behavior.
4. Verified via ruff + pytest.
5. Committed and pushed to `Spenquatch/project-handbook-cli`.

Commands executed (exact):
- uv run ruff format .
- uv run ruff check .
- uv run pytest -q
- git add src/ph/cli.py src/ph/validate_docs.py tests/test_validate.py
- git commit -m "Implement ph validate command"
- git push
- make validate-quick

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/validate_docs.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_validate.py

Verification:
- uv run ruff check .
  - All checks passed!
- uv run pytest -q
  - 21 passed
- make validate-quick
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: Added `ph validate` (vendored validator) with correct scope outputs, flags, and integration tests.

Next task:
- CLI-0204

Blockers (if blocked):
- (none)

## 2026-01-14 15:24 UTC — CLI-0202 — Implement history logging to .project-handbook/history.log

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0202)

Goal:
- Implement history logging per contract (timestamp + entry format) with skip flags and tests.

Work performed (ordered):
1. Implemented history appender writing to `PH_ROOT/.project-handbook/history.log` with `%Y-%m-%d %H:%M:%S | <entry>` format.
2. Integrated history logging into the CLI execution pipeline for success + failure.
3. Added `--no-history` and `--no-post-hook` skip flags (post-hook disables history).
4. Added tests for default entry `(default)`, skip flags, and failure logging.
5. Verified via ruff + pytest.
6. Committed and pushed to `Spenquatch/project-handbook-cli`.

Commands executed (exact):
- uv run ruff format .
- uv run ruff check .
- uv run pytest -q
- git add src/ph/cli.py src/ph/history.py tests/test_history.py
- git commit -m "Add history logging and skip flags"
- git push
- make validate-quick

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/history.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_history.py

Verification:
- uv run ruff check .
  - All checks passed!
- uv run pytest -q
  - 19 passed
- make validate-quick
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: Added history logging with correct timestamp/entry format, skip flags, and tests.

Next task:
- CLI-0203

Blockers (if blocked):
- (none)

## 2026-01-14 15:22 UTC — CLI-0201 — Implement scope selection and PH_DATA_ROOT

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0201)

Goal:
- Add `--scope` selection, derive PH_DATA_ROOT, and enforce system-scope roadmap/releases exclusions.

Work performed (ordered):
1. Added `--scope project|system` global flag and scope resolution (default project).
2. Introduced a context object carrying PH_ROOT + scope + PH_DATA_ROOT.
3. Implemented system-scope guardrails rejecting roadmap/releases operations.
4. Added unit tests for project/system data root selection and guardrails.
5. Verified via ruff + pytest.
6. Committed and pushed to `Spenquatch/project-handbook-cli`.

Commands executed (exact):
- uv run ruff format .
- uv run ruff check .
- uv run pytest -q
- git add src/ph/cli.py src/ph/context.py tests/test_scope.py
- git commit -m "Add scope selection and data root context"
- git push
- make validate-quick

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/context.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_scope.py

Verification:
- uv run ruff check .
  - All checks passed!
- uv run pytest -q
  - 14 passed
- make validate-quick
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: Implemented `--scope` selection and PH_DATA_ROOT context with system-scope guardrails and tests.

Next task:
- CLI-0202

Blockers (if blocked):
- (none)

## 2026-01-14 15:18 UTC — CLI-0103 — Implement ph doctor

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0103)

Goal:
- Implement `ph doctor` output + exit codes per contract, with tests.

Work performed (ordered):
1. Implemented `ph doctor` to report PH_ROOT, config schema/version, installed version, and required asset existence checks.
2. Added required-asset checks per contract and exit codes (0 ok, 2 config mismatch, 3 missing assets).
3. Added tests for ok / schema mismatch / missing assets.
4. Verified via ruff + pytest.
5. Committed and pushed to `Spenquatch/project-handbook-cli`.

Commands executed (exact):
- uv run ruff format .
- uv run ruff check .
- uv run pytest -q
- git add src/ph/cli.py src/ph/config.py src/ph/doctor.py tests/test_doctor.py
- git commit -m "Add ph doctor diagnostics"
- git push
- make validate-quick

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/config.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/doctor.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_doctor.py

Verification:
- uv run ruff check .
  - All checks passed!
- uv run pytest -q
  - 10 passed
- make validate-quick
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: Added `ph doctor` with contract exit codes and required-asset checks, plus tests.

Next task:
- CLI-0201

Blockers (if blocked):
- (none)

## 2026-01-14 15:15 UTC — CLI-0102 — Load and validate cli_plan/project_handbook.config.json

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0102)

Goal:
- Enforce handbook schema + CLI version compatibility from `cli_plan/project_handbook.config.json`.

Work performed (ordered):
1. Implemented config loading + validation for schema version and `requires_ph_version`.
2. Integrated config validation into the CLI entrypoint (after PH_ROOT discovery).
3. Added tests for schema mismatch and version mismatch (remediation includes `uv tool install project-handbook-cli`).
4. Verified via ruff + pytest.
5. Committed and pushed to `Spenquatch/project-handbook-cli`.

Commands executed (exact):
- uv run ruff format .
- uv run ruff check .
- uv run pytest -q
- git add .gitignore pyproject.toml src/ph/cli.py src/ph/config.py tests/test_root_detection.py tests/test_config_validation.py
- git commit -m "Validate handbook config schema and version"
- git push
- make validate-quick

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/.gitignore
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/pyproject.toml
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/config.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_config_validation.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_root_detection.py

Verification:
- uv run ruff check .
  - All checks passed!
- uv run pytest -q
  - 7 passed
- make validate-quick
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: Added handbook config schema/version enforcement with remediation and tests.

Next task:
- CLI-0103

Blockers (if blocked):
- (none)

## 2026-01-14 15:04 UTC — CLI-0101 — Implement PH_ROOT detection using the root marker

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0101)

Goal:
- Implement PH_ROOT detection via the `cli_plan/project_handbook.config.json` marker, and add unit tests.

Work performed (ordered):
1. Implemented `src/ph/root.py` to resolve PH_ROOT via `--root` override or upward directory walk for the marker file.
2. Integrated PH_ROOT resolution into the CLI entrypoint (non-`version` invocations).
3. Added tests covering in-repo, nested subdir, outside-repo failure remediation, and `--root` override.
4. Verified via ruff + pytest.
5. Committed and pushed to `Spenquatch/project-handbook-cli`.

Commands executed (exact):
- uv run ruff format .
- uv run ruff check .
- uv run pytest -q
- git add src/ph/cli.py src/ph/root.py tests/test_root_detection.py
- git commit -m "Implement PH_ROOT discovery"
- git push
- make validate-quick

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/root.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_root_detection.py

Verification:
- uv run ruff check .
  - All checks passed!
- uv run pytest -q
  - 5 passed
- make validate-quick
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: Added PH_ROOT discovery and tests (in-repo/subdir/outside failure + `--root` override).

Next task:
- CLI-0102

Blockers (if blocked):
- (none)

## 2026-01-14 15:02 UTC — CLI-0004 — Add release/versioning workflow (PEP 440 + tags)

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0004)

Goal:
- Add a single source-of-truth `__version__`, implement `ph version`, and document the exact release steps.

Work performed (ordered):
1. Added `__version__ = "0.1.0"` as the sole content of `src/ph/__init__.py`.
2. Implemented `ph version` to print `__version__` and exit 0.
3. Documented the exact release procedure steps in the CLI README.
4. Verified `ph version`, ruff, and pytest.
5. Committed and pushed to `Spenquatch/project-handbook-cli`.

Commands executed (exact):
- uv pip install -e ".[dev]"
- . .venv/bin/activate && ph version
- uv run ruff format .
- uv run ruff check .
- uv run pytest -q
- git add README.md src/ph/__init__.py src/ph/cli.py
- git commit -m "Add version constant and ph version command"
- git push
- make validate-quick

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/README.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/__init__.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py

Verification:
- . .venv/bin/activate && ph version
  - prints: 0.1.0
- uv run ruff check .
  - All checks passed!
- uv run pytest -q
  - 1 passed
- make validate-quick
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: Added `__version__` source-of-truth and `ph version`, and documented the exact release procedure.

Next task:
- CLI-0101

Blockers (if blocked):
- (none)

## 2026-01-14 14:58 UTC — CLI-0003 — Add required dev tooling: ruff + pytest

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0003)

Goal:
- Add ruff + pytest tooling and a smoke test, and document the exact verification commands.

Work performed (ordered):
1. Added `ruff` + `pytest` under `[project.optional-dependencies] dev` and configured ruff in `pyproject.toml`.
2. Added `tests/test_cli_help.py` smoke test to run `ph --help`.
3. Documented the exact verification commands in the CLI README.
4. Ran the verification commands and fixed a ruff import-order issue.
5. Committed and pushed to `Spenquatch/project-handbook-cli`.

Commands executed (exact):
- uv pip install -e ".[dev]"
- uv run ruff format .
- uv run ruff check .
- uv run ruff check . --fix
- uv run ruff format .
- uv run ruff check .
- uv run pytest -q
- git add README.md pyproject.toml src/ph/__main__.py tests
- git commit -m "Add ruff and pytest tooling"
- git push
- make validate-quick

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/README.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/pyproject.toml
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/__main__.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_cli_help.py

Verification:
- uv run ruff format .
  - 2 files reformatted, 2 files left unchanged
- uv run ruff check .
  - (initially failed with I001; fixed with `--fix`)
- uv run ruff check .
  - All checks passed!
- uv run pytest -q
  - 1 passed
- make validate-quick
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: Added ruff/pytest dev tooling and a smoke test; documented and verified format/lint/test commands.

Next task:
- CLI-0004

Blockers (if blocked):
- (none)

## 2026-01-14 14:54 UTC — CLI-0002 — Add packaging skeleton and ph console script

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0002)

Goal:
- Add an installable Python package skeleton providing the `ph` console script.

Work performed (ordered):
1. Added packaging skeleton (`pyproject.toml`, `src/ph/**`) using hatchling + src-layout.
2. Implemented a minimal `ph` argparse entrypoint and `python -m ph` support.
3. Documented the required local install verification commands in the CLI README.
4. Verified editable install and `ph --help` output from the venv.
5. Committed and pushed to `Spenquatch/project-handbook-cli`.

Commands executed (exact):
- uv venv
- uv pip install -e .
- ph --help
- . .venv/bin/activate && ph --help
- git add README.md pyproject.toml src
- git commit -m "Add packaging skeleton and ph entrypoint"
- git rm -r --cached src/ph/__pycache__ && rm -rf src/ph/__pycache__
- git add .gitignore
- git commit --amend --no-edit
- git push --force-with-lease
- make validate-quick

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/.gitignore
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/README.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/pyproject.toml
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/__init__.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/__main__.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py

Verification:
- uv venv
  - Created virtual environment at: .venv
- uv pip install -e .
  - Installed project-handbook-cli==0.1.0 (editable)
- ph --help
  - (initially not found until venv activated)
- . .venv/bin/activate && ph --help
  - exits 0 and prints argparse help
- make validate-quick
  - validation: 0 error(s), 0 warning(s), report: /Users/spensermcconnell/__Active_Code/project-handbook/status/validation.json

Outcome:
- status: done
- summary: Added an installable `project-handbook-cli` package skeleton providing the `ph` console script.

Next task:
- CLI-0003

Blockers (if blocked):
- (none)

## 2026-01-14 18:10 UTC — CLI-0413 — Implement `ph sprint burndown` and `ph sprint capacity`

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0413)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/sprint_manager.py

Goal:
- Implement `ph sprint burndown` and `ph sprint capacity` for both scopes and ensure burndown writes `burndown.md` under the active sprint directory.

Work performed (ordered):
1. Ported `sprint_manager.py --burndown` into `ph sprint burndown`, including a scope-local `burndown.md` artifact.
2. Ported `sprint_manager.py --capacity` into `ph sprint capacity`, including bounded vs timeboxed output modes and backlog pressure signal.
3. Added integration tests for both scopes that create a sprint, run burndown, and assert the sprint-local `burndown.md` exists.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/sprint_burndown.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/sprint_capacity.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_sprint_burndown_capacity.py

Verification:
- uv run pytest -q
  - 58 passed

Outcome:
- status: done
- summary: Added `ph sprint burndown` (writes `burndown.md`) and `ph sprint capacity` for both scopes, plus integration tests.

Next task:
- CLI-0414

Blockers (if blocked):
- (none)

## 2026-01-14 18:18 UTC — CLI-0414 — Implement `ph sprint archive`

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0414)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/sprint_manager.py

Goal:
- Implement `ph sprint archive` for both scopes and ensure the sprint directory is moved into `sprints/archive/<year>/<SPRINT-...>/` within the selected scope.

Work performed (ordered):
1. Ported `sprint_manager.py --archive` into `ph sprint archive` with scope-local archive paths (no repo-local subprocesses).
2. Recorded a sprint archive entry under `<scope>/sprints/archive/index.json`.
3. Added integration tests that create a sprint and assert `ph sprint archive` moves it into the expected scope-local archive path.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/sprint_archive.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_sprint_archive.py

Verification:
- uv run pytest -q
  - 60 passed

Outcome:
- status: done
- summary: Added `ph sprint archive` for both scopes, including archive index tracking and integration tests.

Next task:
- CLI-0415

Blockers (if blocked):
- (none)

## 2026-01-14 18:22 UTC — CLI-0415 — Implement `ph sprint close`

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0415)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/sprint_manager.py

Goal:
- Implement `ph sprint close` for both scopes: create retrospective artifacts, archive the sprint into `<scope>/sprints/archive/...`, rewrite `sprints/current/tasks/...` links, and print the exact project-scope hint block.

Work performed (ordered):
1. Ported `sprint_manager.py --close` into `ph sprint close` (retrospective generation + sprint velocity output + archive).
2. Implemented scope-local link rewriting for `sprints/current/tasks/...` references in `features/`, `status/evidence/`, and `adr/`.
3. Added integration tests asserting the exact project hint block and that system scope does not print the hint block.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/sprint_archive.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/sprint_close.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_sprint_close.py

Verification:
- uv run pytest -q
  - 62 passed

Outcome:
- status: done
- summary: Added `ph sprint close` (retrospective + archive + link rewrite) with contract-correct project hints and integration tests.

Next task:
- CLI-0421

Blockers (if blocked):
- (none)

## 2026-01-14 18:27 UTC — CLI-0421 — Implement `ph task create` scaffolding + hints + guardrails

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0421)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/task_manager.py
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/data_root.py
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/system_scope_config.json

Goal:
- Implement `ph task create` for both scopes with v0 scaffolding templates (Make-era commands rewritten to `ph`), lane guardrails, and contract-correct hint blocks.

Work performed (ordered):
1. Implemented `ph task create` (scope-aware) by porting v0 `task_manager.py` scaffolding + id allocation + decision linking into `ph.task_create`.
2. Added the project-scope system-lane guardrail driven by `process/automation/system_scope_config.json` with the exact remediation string.
3. Added deterministic integration tests for project/system create and the guardrail failure, asserting file creation + exact hint blocks.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/task_create.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_task_create.py

Verification:
- uv run pytest -q
  - 65 passed

Outcome:
- status: done
- summary: Added `ph task create` with v0-style scaffolding and scope-correct hints/guardrails, plus integration tests.

Next task:
- CLI-0422

Blockers (if blocked):
- (none)

## 2026-01-14 18:38 UTC — CLI-0422 — Implement `ph task list` and `ph task show`

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0422)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/task_manager.py

Goal:
- Implement `ph task list` and `ph task show` (both scopes) with v0-compatible formatting and deterministic integration tests.

Work performed (ordered):
1. Implemented `ph task list` with v0 emoji/status mapping and optional segment formatting driven by `task.yaml`.
2. Implemented `ph task show --id <TASK-###>` with v0 field ordering, exit codes, and scope-correct location strings.
3. Added integration tests (project + system) asserting exact list output, show output, and not-found behavior.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/task_view.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_task_list_show.py

Verification:
- uv run pytest -q
  - 67 passed

Outcome:
- status: done
- summary: Added `ph task list` and `ph task show` for both scopes with integration tests and v0-compatible outputs.

Next task:
- CLI-0423

Blockers (if blocked):
- (none)

## 2026-01-14 20:57 UTC — CLI-0471 — Implement ph release plan (default version=next) + symlink + hints

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0471)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/release_manager.py

Goal:
- Implement `ph release plan` (project-only) with v0-parity templates, symlink, and the exact 4-line hint block.

Work performed (ordered):
1. Added `ph release plan` parsing + dispatch plumbing.
2. Ported v0 release plan templates and `releases/current` symlink behavior into `project-handbook-cli`.
3. Added deterministic integration tests for file creation, symlink target, hint lines, and system-scope rejection.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/release.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_release_plan.py

Verification:
- uv run pytest -q
  - 107 passed

Outcome:
- status: done
- summary: Implemented `ph release plan` (project-only) with v0 templates, `releases/current` symlink management, and the exact 4-line hint block.

Next task:
- CLI-0472

Blockers (if blocked):
- (none)

## 2026-01-14 21:05 UTC — CLI-0472 — Implement ph release list and status

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0472)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/release_manager.py

Goal:
- Implement `ph release list` and `ph release status` (project-only) with v0-parity output and deterministic integration tests.

Work performed (ordered):
1. Implemented `ph release list` and `ph release status` command wiring (project-only).
2. Ported v0 release list/status output with semantic sorting, `(current)` marker, and Make-era remediation rewritten to `ph`.
3. Added deterministic integration tests for list ordering/current marker, missing-current failure, and system-scope rejection.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/release.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_release_list_status.py

Verification:
- uv run pytest -q
  - 110 passed

Outcome:
- status: done
- summary: Added `ph release list` and `ph release status` with v0-style outputs, semantic ordering, and deterministic integration tests.

Next task:
- CLI-0473

Blockers (if blocked):
- (none)

## 2026-01-14 21:10 UTC — CLI-0473 — Implement ph release add-feature and suggest

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0473)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/release_manager.py

Goal:
- Implement `ph release add-feature` and `ph release suggest` (project-only) with v0-parity behavior and deterministic integration tests.

Work performed (ordered):
1. Implemented `ph release add-feature` with a conservative YAML block upsert (preserves existing blocks and order).
2. Implemented `ph release suggest` with v0 header/formatting and `Stage:`-based recommendations.
3. Added deterministic integration tests for YAML updates, suggest output, and system-scope rejection.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/release.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_release_add_feature_suggest.py

Verification:
- uv run pytest -q
  - 112 passed

Outcome:
- status: done
- summary: Added `ph release add-feature` and `ph release suggest` with v0-style outputs and deterministic integration tests.

Next task:
- CLI-0474

Blockers (if blocked):
- (none)

## 2026-01-14 21:14 UTC — CLI-0474 — Implement ph release close

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0474)
- /Users/spensermcconnell/__Active_Code/project-handbook/process/automation/release_manager.py

Goal:
- Implement `ph release close` (project-only) with v0 delivered metadata updates, changelog generation, and deterministic integration tests.

Work performed (ordered):
1. Implemented `ph release close` to generate `changelog.md` and update `plan.md` delivered metadata + release status note.
2. Wired `ph release close` into the CLI command tree with project-only scope enforcement.
3. Added deterministic integration tests covering delivered metadata, changelog creation, and system-scope rejection.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/release.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_release_close.py

Verification:
- uv run pytest -q
  - 114 passed

Outcome:
- status: done
- summary: Added `ph release close` with v0-style changelog generation + plan delivered metadata updates and deterministic integration tests.

Next task:
- CLI-0305

Blockers (if blocked):
- (none)

## 2026-01-14 21:20 UTC — CLI-0305 — Implement ph check-all and ph test system orchestration

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: /Users/spensermcconnell/__Active_Code/project-handbook
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0001-ph-cli-migration.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/tasks.json (task CLI-0305)

Goal:
- Implement `ph check-all` and `ph test system` orchestration with contract-defined ordering and tests asserting internal sequencing without double-running hooks.

Work performed (ordered):
1. Implemented `ph check-all` and `ph test system` orchestration using a reusable command runner abstraction.
2. Wired both orchestration commands into the CLI command tree with exact contract ordering and project-only remediation.
3. Added pytest unit tests with a fake runner to assert the exact internal invocation sequence and that sub-steps run without hooks.

Commands executed (exact):
- uv run ruff format . && uv run ruff check . && uv run pytest -q

Files changed (exact paths):
- cli_plan/tasks.json
- cli_plan/session_logs.md
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/cli.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/src/ph/orchestration.py
- /Users/spensermcconnell/__Active_Code/project-handbook-cli/tests/test_orchestration.py

Verification:
- uv run pytest -q
  - 117 passed

Outcome:
- status: done
- summary: Added `ph check-all` and `ph test system` orchestration with contract-ordered internal steps and tests proving the exact sequence and no sub-step hooks.

Next task:
- CLI-0501

Blockers (if blocked):
- (none)

## 2026-01-17 21:35 UTC — DD-0103 — backlog-archive-wildcards contract

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0103)
- cli_plan/ph_spec/CONTRACT_TEMPLATE.md
- cli_plan/ph_spec/ph/backlog/archive/contract.md
- cli_plan/ph_spec/ph/backlog/archive/bugs/contract.md
- cli_plan/ph_spec/ph/backlog/archive/wildcards/contract.md
- cli_plan/ph_spec/ph/backlog/archive/wildcards/examples/WILD-P2-20260101-2107/README.md

Goal:
- Complete `cli_plan/ph_spec/ph/backlog/archive/wildcards/contract.md` with a full, unambiguous directory contract and reconcile it with examples.

Work performed (ordered):
1. Reviewed the existing contract stub and the archived wildcard example fixture.
2. Updated the contract to fully specify purpose, creation/mutation rules, required files, schema requirements, invariants, and validation expectations.

Commands executed (exact):
- sed -n '1,200p' cli_plan/ph_spec/ph/backlog/archive/wildcards/contract.md
- find cli_plan/ph_spec/ph/backlog/archive/wildcards/examples -maxdepth 3 -type f -print
- sed -n '1,200p' cli_plan/ph_spec/ph/backlog/archive/wildcards/examples/WILD-P2-20260101-2107/README.md
- sed -n '1,200p' cli_plan/ph_spec/CONTRACT_TEMPLATE.md
- sed -n '1,220p' cli_plan/ph_spec/ph/backlog/archive/contract.md
- sed -n '1,260p' cli_plan/ph_spec/ph/backlog/archive/bugs/contract.md
- rg -n '\\(TBD\\)|TBD' cli_plan/ph_spec/ph/backlog/archive/wildcards/contract.md || true

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/backlog/archive/wildcards/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and matches the example’s front matter shape/archival fields.

Outcome:
- status: done
- summary: Completed the archive wildcards directory contract and reconciled it against the example fixture.

Next task:
- DD-0104

Blockers (if blocked):
- (none)

## 2026-01-17 21:37 UTC — DD-0104 — backlog-archive-work-items contract

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0104)
- cli_plan/ph_spec/CONTRACT_TEMPLATE.md
- cli_plan/ph_spec/ph/backlog/archive/contract.md
- cli_plan/ph_spec/ph/backlog/archive/bugs/contract.md
- cli_plan/ph_spec/ph/backlog/archive/work-items/contract.md
- cli_plan/ph_spec/ph/backlog/archive/work-items/examples/WORK-P4-20260104-1919/README.md

Goal:
- Complete `cli_plan/ph_spec/ph/backlog/archive/work-items/contract.md` with a full, unambiguous directory contract and reconcile it with examples.

Work performed (ordered):
1. Reviewed the existing contract stub and the archived work-item example fixture.
2. Updated the contract to fully specify purpose, creation/mutation rules, required files, schema requirements (including optional `input_type`), invariants, and validation expectations.

Commands executed (exact):
- sed -n '1,240p' cli_plan/ph_spec/ph/backlog/archive/work-items/contract.md
- find cli_plan/ph_spec/ph/backlog/archive/work-items/examples -maxdepth 3 -type f -print
- sed -n '1,220p' cli_plan/ph_spec/ph/backlog/archive/work-items/examples/WORK-P4-20260104-1919/README.md
- sed -n '1,200p' cli_plan/ph_spec/CONTRACT_TEMPLATE.md
- sed -n '1,220p' cli_plan/ph_spec/ph/backlog/archive/contract.md
- sed -n '1,260p' cli_plan/ph_spec/ph/backlog/archive/bugs/contract.md
- rg -n '\\(TBD\\)|TBD' cli_plan/ph_spec/ph/backlog/archive/work-items/contract.md || true

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/backlog/archive/work-items/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and matches the example’s front matter shape/archival fields.

Outcome:
- status: done
- summary: Completed the archive work-items directory contract and reconciled it against the example fixture.

Next task:
- DD-0105

Blockers (if blocked):
- (none)

## 2026-01-17 21:38 UTC — DD-0105 — backlog-bugs contract

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0105)
- cli_plan/ph_spec/CONTRACT_TEMPLATE.md
- cli_plan/ph_spec/ph/backlog/contract.md
- cli_plan/ph_spec/ph/backlog/archive/bugs/contract.md
- cli_plan/ph_spec/ph/backlog/bugs/contract.md
- cli_plan/ph_spec/ph/backlog/bugs/examples/EXAMPLE-BUG-P0-20250922-1144/README.md
- cli_plan/ph_spec/ph/backlog/bugs/examples/EXAMPLE-BUG-P0-20250922-1144/triage.md

Goal:
- Complete `cli_plan/ph_spec/ph/backlog/bugs/contract.md` with a full, unambiguous directory contract and reconcile it with examples.

Work performed (ordered):
1. Reviewed the existing contract stub and the bug example fixture (README + triage template).
2. Updated the contract to define the directory purpose, creation/mutation commands, required layout, README front matter schema, and validation rules (including P0 triage guidance).
3. Updated the bug example fixture to remove archive-only metadata fields so it matches the non-archive contract.

Commands executed (exact):
- sed -n '1,260p' cli_plan/ph_spec/ph/backlog/bugs/contract.md
- find cli_plan/ph_spec/ph/backlog/bugs/examples -maxdepth 3 -type f -print
- sed -n '1,200p' cli_plan/ph_spec/ph/backlog/bugs/examples/EXAMPLE-BUG-P0-20250922-1144/README.md
- sed -n '1,160p' cli_plan/ph_spec/ph/backlog/bugs/examples/EXAMPLE-BUG-P0-20250922-1144/triage.md
- sed -n '1,200p' cli_plan/ph_spec/CONTRACT_TEMPLATE.md
- sed -n '1,320p' cli_plan/ph_spec/ph/backlog/contract.md
- sed -n '1,260p' cli_plan/ph_spec/ph/backlog/archive/bugs/contract.md
- python - <<'PY'
  from pathlib import Path
  text = Path('cli_plan/ph_spec/ph/backlog/bugs/examples/EXAMPLE-BUG-P0-20250922-1144/README.md').read_text()
  front = text.split('---', 2)[1]
  for k in ['archived_at', 'archived_by_task', 'archived_by_sprint']:
      print(k, k in front)
  PY
- rg -n '\\(TBD\\)|TBD' cli_plan/ph_spec/ph/backlog/bugs/contract.md || true

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/backlog/bugs/contract.md
- cli_plan/ph_spec/ph/backlog/bugs/examples/EXAMPLE-BUG-P0-20250922-1144/README.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the example fixture no longer includes archive-only keys.

Outcome:
- status: done
- summary: Completed the backlog bugs directory contract and reconciled it against the examples.

Next task:
- DD-0106

Blockers (if blocked):
- (none)

## 2026-01-17 21:40 UTC — DD-0106 — backlog-root contract

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0106)
- cli_plan/ph_spec/CONTRACT_TEMPLATE.md
- cli_plan/ph_spec/ph/backlog/contract.md
- cli_plan/ph_spec/ph/backlog/archive/contract.md
- cli_plan/ph_spec/ph/backlog/examples/bugs/EXAMPLE-BUG-P0-20250922-1144/README.md
- cli_plan/ph_spec/ph/backlog/examples/work-items/WORK-P2-20260106-213751/README.md
- cli_plan/ph_spec/ph/backlog/examples/wildcards/WILD-P2-20260103-2109/README.md

Goal:
- Complete `cli_plan/ph_spec/ph/backlog/contract.md` with a full, unambiguous directory contract and reconcile it with examples (including the derived `index.json` catalog).

Work performed (ordered):
1. Reviewed the existing contract stub and backlog example fixtures (bugs, wildcards, work-items).
2. Updated the contract to fully specify the backlog directory purpose, required subdirectories, and the derived `index.json` schema/constraints.
3. Updated the bug example fixture to remove archive-only metadata keys so it matches the non-archive backlog contracts.

Commands executed (exact):
- sed -n '1,320p' cli_plan/ph_spec/ph/backlog/contract.md
- find cli_plan/ph_spec/ph/backlog/examples -maxdepth 3 -type f -print
- sed -n '1,220p' cli_plan/ph_spec/ph/backlog/examples/wildcards/WILD-P2-20260103-2109/README.md
- sed -n '1,200p' cli_plan/ph_spec/ph/backlog/examples/work-items/WORK-P2-20260106-213751/README.md
- sed -n '1,200p' cli_plan/ph_spec/ph/backlog/examples/bugs/EXAMPLE-BUG-P0-20250922-1144/README.md
- sed -n '1,220p' cli_plan/ph_spec/ph/backlog/archive/contract.md
- rg -n '\\(TBD\\)|TBD' cli_plan/ph_spec/ph/backlog/contract.md || true

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/backlog/contract.md
- cli_plan/ph_spec/ph/backlog/examples/bugs/EXAMPLE-BUG-P0-20250922-1144/README.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the example fixtures match the documented README/front matter expectations.

Outcome:
- status: done
- summary: Completed the backlog root directory contract including an explicit `index.json` schema and reconciled the example fixtures.

Next task:
- DD-0107

Blockers (if blocked):
- (none)

## 2026-01-17 21:43 UTC — DD-0107 — backlog-wildcards contract

Agent: GPT-5.2 (Codex CLI)
Environment: approval_policy=never; sandbox_mode=danger-full-access; network_access=enabled; shell=zsh
Handbook instance repo: (not used; due-diligence only)
CLI repo: /Users/spensermcconnell/__Active_Code/project-handbook-cli

Inputs reviewed:
- cli_plan/v1_cli/ADR-CLI-0003-ph-project-layout.md
- cli_plan/v1_cli/CLI_CONTRACT.md
- cli_plan/due-diligence.json (task DD-0107)
- cli_plan/ph_spec/CONTRACT_TEMPLATE.md
- cli_plan/ph_spec/ph/backlog/contract.md
- cli_plan/ph_spec/ph/backlog/archive/wildcards/contract.md
- cli_plan/ph_spec/ph/backlog/wildcards/contract.md
- cli_plan/ph_spec/ph/backlog/wildcards/examples/WILD-P2-20260103-2109/README.md

Goal:
- Complete `cli_plan/ph_spec/ph/backlog/wildcards/contract.md` with a full, unambiguous directory contract and reconcile it with examples.

Work performed (ordered):
1. Reviewed the existing contract stub and the wildcard example fixture.
2. Updated the contract to define purpose, creation/mutation commands, required layout, README front matter schema, and validation rules.

Commands executed (exact):
- sed -n '1,220p' cli_plan/ph_spec/ph/backlog/wildcards/contract.md
- find cli_plan/ph_spec/ph/backlog/wildcards/examples -maxdepth 3 -type f -print
- sed -n '1,220p' cli_plan/ph_spec/ph/backlog/wildcards/examples/WILD-P2-20260103-2109/README.md
- sed -n '1,320p' cli_plan/ph_spec/ph/backlog/contract.md
- sed -n '1,200p' cli_plan/ph_spec/ph/backlog/archive/wildcards/contract.md
- rg -n '\\(TBD\\)|TBD' cli_plan/ph_spec/ph/backlog/wildcards/contract.md || true

Files changed (exact paths):
- cli_plan/due-diligence.json
- cli_plan/session_logs.md
- cli_plan/ph_spec/ph/backlog/wildcards/contract.md

Verification:
- Confirmed the contract has no remaining `(TBD)` placeholders and the example fixture matches the documented README/front matter expectations.

Outcome:
- status: done
- summary: Completed the backlog wildcards directory contract and reconciled it against the examples.

Next task:
- DD-0108

Blockers (if blocked):
- (none)
