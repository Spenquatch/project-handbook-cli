# Quick Start

## IMPORTANT: Don’t point `ph` at the legacy repo

Do **not** use `../project-handbook/` or `legacy-reference/project-handbook/` as your working handbook instance when developing `project-handbook-cli`. That legacy repo is reference-only and will cause muddy/contradictory behavior during the transition.

## Install

Pick one:

- `uv tool install project-handbook-cli`
- `pipx install project-handbook-cli`
- `pip install project-handbook-cli`

Verify:

- `ph --help`

## Point `ph` at a handbook instance repo

`ph` discovers the handbook root by searching upward from `cwd` for `.ph/config.json`.

If you are starting a new handbook instance repo directory, initialize the root marker first:

- `ph init`

Then verify required assets:

- `ph doctor`

From anywhere inside your handbook repo:

- `ph doctor`

Or explicitly:

- `ph --root /path/to/project-handbook doctor`

Tip: when developing inside a mono-repo or when your shell `cwd` is not inside the target project, prefer `--root` to avoid accidentally operating on the wrong repo.

Note: this repo contains `legacy-reference/project-handbook/` for reference only; it is gitignored and may contain Make-era command examples. Prefer v1 `ph ...` commands when following docs/specs.

## Run a few commands

- `ph validate --quick`
- `ph status`
- `ph sprint plan`
