# Quick Start

## Install

Pick one:

- `uv tool install project-handbook-cli`
- `pipx install project-handbook-cli`
- `pip install project-handbook-cli`

Verify:

- `ph --help`

## Point `ph` at a handbook instance repo

`ph` discovers the handbook root by searching upward from `cwd` for `project_handbook.config.json`.

If you are starting a new handbook instance repo directory, initialize the root marker first:

- `ph init`

Then verify required assets:

- `ph doctor`

From anywhere inside your handbook repo:

- `ph doctor`

Or explicitly:

- `ph --root /path/to/project-handbook doctor`

## Run a few commands

- `ph validate --quick`
- `ph status`
- `ph sprint plan`

## Scope selection

Project scope (default):

- `ph feature list`

System scope:

- `ph --scope system feature list`
