# Commands

This is a practical overview of common commands. For authoritative behavior/mapping, refer to the handbook instance repo’s `cli_plan/v1_cli/CLI_CONTRACT.md`.

## Diagnostics

- `ph doctor`
- `ph help [topic]`

## Validation + status

- `ph validate [--quick]`
- `ph status`
- `ph dashboard`
- `ph check-all`

## Sprint

- `ph sprint plan [--sprint SPRINT-YYYY-MM-DD-XX]`
- `ph sprint open --sprint SPRINT-...`
- `ph sprint status`
- `ph sprint tasks`
- `ph sprint burndown`
- `ph sprint capacity`
- `ph sprint archive [--sprint SPRINT-...]`
- `ph sprint close`

## Work items

- `ph feature list`
- `ph feature create --name <name>`
- `ph task create --title "..." --feature <name> --decision ADR-0000 [--lane ops]`

## Roadmap + releases (project-scope only)

- `ph roadmap <show|create|validate>`
- `ph release <plan|status|list|add-feature|suggest|close>`

## Destructive operations

- `ph reset` (dry-run)
- `ph reset --confirm RESET --force true` (execute)
- `ph reset-smoke` (destructive to project scope)
- `ph migrate system-scope --confirm RESET --force true`

