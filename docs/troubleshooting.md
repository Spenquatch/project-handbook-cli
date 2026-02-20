# Troubleshooting

## “No Project Handbook root found”

`ph` can’t find `.project-handbook/config.json` by searching upward from your current directory.

Fix:

- run `ph init` in the target repo, or
- pass the root explicitly: `ph --root /absolute/path/to/handbook doctor`

## `ph doctor` reports missing assets

If `.project-handbook/process/checks/validation_rules.json` or `.project-handbook/process/sessions/templates/` are missing, many workflows will refuse to run.

Fix:

- `ph init` (safe and idempotent)
- `ph process refresh --templates --playbooks` (after upgrades)

## System scope errors

System scope is intentionally restricted. If you see errors about `roadmap` or `releases`:

- run those commands in project scope: `ph --scope project ...`

## Post-hook output interfering with scripts

If you are scripting `ph` and want predictable stdout:

- prefer commands that support `--format json`
- during debugging, disable hooks: `--no-post-hook` (or `--no-validate`)

## Evidence capture isn’t streaming output

By design, `ph evidence run` captures output to files instead of streaming to your terminal.

- open `.project-handbook/status/evidence/.../stdout.txt` and `stderr.txt`

## “Refusing to overwrite an existing evidence run capture”

If you re-run the same `--run-id` in the same directory, `ph evidence run` will refuse to overwrite `stdout.txt`/`stderr.txt`/`meta.json`.

Fix:

- use a new `--run-id`, or
- delete the existing evidence run files intentionally

## More help

- `ph help` and `ph help <topic>` for workflow-specific help text
- `ph --help` for the full CLI surface

