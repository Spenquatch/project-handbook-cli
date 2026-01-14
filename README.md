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

## End-session (manual verification)

Non-`--skip-codex` mode requires the `codex` CLI on your `PATH` (e.g. `npm i -g @openai/codex`).

Example:
- `ph end-session --log ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl --root /path/to/project-handbook`

## Release (exact steps)

1) update `src/ph/__init__.py` `__version__`
2) run `uv run ruff format .` then `uv run ruff check .` then `uv run pytest -q`
3) create git tag `v<__version__>`
4) build with `python -m build`
5) verify artifacts exist in `dist/`.
