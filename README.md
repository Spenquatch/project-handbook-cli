# project-handbook-cli

Installed Python CLI distribution: `project-handbook-cli`

Console script: `ph`

Handbook root marker (v1):
- `cli_plan/project_handbook.config.json`

Rule: `ph` MUST NOT execute repo-local Python scripts at runtime.

## Local install verification (exact commands)

1) `uv venv`
2) `uv pip install -e .`
3) `ph --help`

If `ph` is not found, activate the venv first: `. .venv/bin/activate`.

## Dev verification (exact commands)

- `uv pip install -e ".[dev]"`
- `uv run ruff format .`
- `uv run ruff check .`
- `uv run pytest -q`
