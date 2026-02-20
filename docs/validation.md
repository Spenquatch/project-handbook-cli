# Validation and Pre-exec

Validation is how `ph` keeps a handbook deterministic and safe to operate.

## `ph validate` vs `ph validate --quick`

- `ph validate` runs the full validation suite.
- `ph validate --quick` runs a faster subset suitable for frequent use.

Many mutating commands automatically run `validate --quick` after success via the post-command hook (unless disabled).

## `ph pre-exec lint`

Pre-exec lint is a strict gate intended to run before executing sprint tasks. It focuses on:

- sprint plan health and required structure
- task metadata correctness (including `task_type`)
- ambiguity gates (TBD/TODO/vague validation)
- sprint gate requirements (goal, exit criteria, evidence expectations)

## `ph pre-exec audit`

Pre-exec audit is a higher-assurance gate:

- captures an evidence bundle, then
- runs pre-exec lint

Use this when you want a reproducible record of checks and command output.

## Convenience commands

- `ph check-all` runs validate + status (project-scope only)
- `ph test system` runs a smoke suite (validation + status + daily checks + basic domain reads; project-scope only)

## Disabling hooks

If you need to suppress post-command behavior (history and/or validate):

- `--no-post-hook`
- `--no-history`
- `--no-validate`

