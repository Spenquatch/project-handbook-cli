# project-handbook-cli

Installed Python CLI distribution: `project-handbook-cli`

Console script: `ph`

Handbook root marker (v1):
- `.ph/config.json`

Rule: `ph` MUST NOT execute repo-local Python scripts at runtime.

## IMPORTANT: Do not use the legacy handbook repo for CLI development

Do **not** use `../project-handbook/` or `legacy-reference/project-handbook/` as a dev target (PH_ROOT) while working on `project-handbook-cli`.

- `legacy-reference/project-handbook/` is a reference snapshot only (gitignored).
- v1 docs/specs assume `.ph/config.json` + `.ph/**` (internals) + `ph/**` (content) and **no system scope**.
- The current CLI implementation is not yet fully aligned with the v1 marker/scope, so running `ph` against the legacy repo will be misleading.

## Repo layout (this repo)

- `src/ph/**`: CLI implementation
- `cli_plan/**`: authoritative v1 contract + spec + planning
- `docs/**`: rendered docs (MkDocs)
- `legacy-reference/project-handbook/**`: legacy repo snapshot for reference only (ignored by git; do not treat as v1 `PH_ROOT`)

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
