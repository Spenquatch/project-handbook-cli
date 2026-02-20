# Quick Start

## IMPORTANT: Be explicit about `PH_ROOT` during development

When developing, prefer `ph --root /absolute/path/to/handbook` so you don’t accidentally operate on the wrong directory.

## Install

Pick one:

- `uv tool install project-handbook`
- `pipx install project-handbook`
- `pip install project-handbook`

Verify:

- `ph --help`

## Point `ph` at a handbook instance repo

`ph` discovers the handbook root by searching upward from `cwd` for `.project-handbook/config.json`.

If you are starting a new handbook instance repo directory, initialize the root marker first:

- `ph init`

`ph init` is safe and idempotent: it creates the root marker, required process assets, seeds onboarding/session templates, and scaffolds the canonical handbook directory tree (without overwriting existing files).

After `ph init`, most handbook content lives under:

- `.project-handbook/` (project scope)

Tip: `ph init` updates `.gitignore` by default with recommended ignores (history/log/export paths). Use `--no-gitignore` to skip.

Tip: commit `.project-handbook/` to your repo so planning/execution artifacts are versioned.

Then verify required assets:

- `ph doctor`

From anywhere inside your handbook repo:

- `ph doctor`

Or explicitly:

- `ph --root /path/to/project-handbook doctor`

Tip: when developing inside a mono-repo or when your shell `cwd` is not inside the target project, prefer `--root` to avoid accidentally operating on the wrong repo.

## Run a few commands

- `ph version`
- `ph next`
- `ph validate --quick`
- `ph status`
- `ph sprint plan`
