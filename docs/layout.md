# Handbook Layout

This page describes how `ph` lays out a handbook instance repo on disk.

## Key paths

- `PH_ROOT/` is the directory containing `.project-handbook/config.json`.
- Project scope data root (default): `PH_ROOT/.project-handbook/`
- System scope data root: `PH_ROOT/.project-handbook/system/`

In other words: `ph` is designed to keep almost all handbook artifacts under `.project-handbook/` so they’re easy to find, version, and validate.

## What `ph init` creates

`ph init` is safe and idempotent. It creates the marker and seeds required assets without overwriting existing content.

At a high level (project scope):

```text
.project-handbook/
  config.json
  .gitkeep
  ONBOARDING.md
  AGENT.md
  adr/
  assets/
  backlog/
    bugs/  wildcards/  work-items/
    archive/
    index.json
  contracts/
  decision-register/
  docs/logs/
  features/
    implemented/
  parking-lot/
    features/  technical-debt/  research/  external-requests/
    archive/
    index.json
  process/
    AI_AGENT_START_HERE.md
    automation/reset_spec.json
    checks/validation_rules.json
    playbooks/
    sessions/
      templates/
      logs/
        .gitkeep
        latest_summary.md
      session_end/session_end_index.json
  releases/
    planning/
    delivered/
  roadmap/now-next-later.md
  sprints/
    archive/index.json
    current -> (symlink to an active sprint dir)
  status/
    current.json
    current_summary.md
    daily/
    evidence/
    exports/
    questions/
  tools/
```

System scope is the same shape, but rooted at `.project-handbook/system/` and intentionally excludes `roadmap/` and `releases/`.

## What to commit

In most teams, you should commit `.project-handbook/` so the handbook is versioned.

By default, `ph init` also updates `.gitignore` with recommended ignores (so you don’t accidentally commit logs/exports):

- `.project-handbook/history.log`
- `.project-handbook/process/sessions/logs/*` (keeps `.gitkeep`)
- `.project-handbook/status/exports`

## “Internal” vs “content”

Practically:

- treat everything under `.project-handbook/` as the handbook content and system state that `ph` operates on
- prefer generating/scaffolding with `ph` commands so the system stays deterministic and passes validation

If you need to refresh seeded playbooks/templates after upgrades, use `ph process refresh`.

