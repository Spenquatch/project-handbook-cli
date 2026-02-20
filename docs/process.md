# Process Assets (templates, playbooks, migrations)

`ph` seeds and maintains “process assets” under:

- `.project-handbook/process/`

This includes:

- validation rules: `process/checks/validation_rules.json`
- session templates: `process/sessions/templates/*.md`
- playbooks: `process/playbooks/*.md`

## Refreshing seeded assets

After upgrading `ph`, refresh seed-owned templates/playbooks:

```bash
ph process refresh
```

You can target one set:

```bash
ph process refresh --templates
ph process refresh --playbooks
```

Seed ownership and overwrite rules:

- by default, refresh only overwrites seed-owned files that are still unmodified
- if you edited a seeded file locally, refresh will skip it
- use `--force` to overwrite modified seed-owned files intentionally

## Disabling system-scope enforcement

Some repos may enable system-scope routing/enforcement via validation rules + a config file.
To disable enforcement in an existing repo:

```bash
ph process refresh --disable-system-scope-enforcement
```

This updates `process/checks/validation_rules.json` and deletes `process/automation/system_scope_config.json` if present.

## Task migration: drop deprecated `session:` (v0.0.24+)

As of `ph` v0.0.24, `task_type` is canonical and `session:` in `task.yaml` is deprecated.

To migrate current sprint tasks:

```bash
ph process refresh --migrate-tasks-drop-session
```

This removes `session:` from `task.yaml` (and `README.md` when present), and infers `task_type` from legacy `session` values when possible.

