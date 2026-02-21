# project-handbook-cli

Installed Python CLI distribution: `project-handbook`

Console script: `ph`

Handbook root marker (v1):
- `.project-handbook/config.json`

Rule: `ph` MUST NOT execute repo-local Python scripts at runtime.

## IMPORTANT: Be explicit about `PH_ROOT` during development

When developing, prefer `ph --root /absolute/path/to/handbook` so you don’t accidentally operate on the wrong directory.

v1 contract summary:
- Handbook data root (project scope): `PH_ROOT/.project-handbook/**` (sprints, features, releases, status, process, etc.)
  (All handbook data is stored under this root.)

## Repo layout (this repo)

- `src/ph/**`: CLI implementation
- `cli_plan/**`: authoritative v1 contract + spec + planning
- `docs/**`: rendered docs (MkDocs)

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

## Docs (MkDocs)

- `uv pip install -e ".[dev]"`
- `uv run mkdocs serve`

Docs source lives in `docs/` and is rendered via `mkdocs.yml`.

## End-session (manual verification)

Non-`--skip-codex` mode requires the `codex` CLI on your `PATH` (e.g. `npm i -g @openai/codex`).

Example:
- `ph end-session --log ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl --root /path/to/project-handbook`

## Release (exact steps)

1) update `pyproject.toml` `project.version` and `src/ph/__init__.py` `__version__` (must match)
2) run `uv run ruff check .` then `uv run pytest -q`
3) create git tag `v<version>` and push
4) GitHub Actions publishes to PyPI on tag push (see `.github/workflows/release.yml`)
   - PyPI Trusted Publishing (OIDC)
