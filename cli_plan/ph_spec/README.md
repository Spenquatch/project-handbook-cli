# `ph_spec/` notes

This folder contains the directory-by-directory spec for the v1 `ph` layout (`.ph/**` internals + `ph/**` content), plus example artifacts.

## About `examples/`

- `examples/` fixtures are copied from real projects when possible, but they live under `cli_plan/ph_spec/**/examples/` for documentation purposes.
- As a result, **internal relative links may not resolve** from within the `examples/` location (because the examples are nested deeper than real `ph/**` content).
- Some example content may still include **legacy Make-era commands** (e.g. `make ...` or `pnpm -C project-handbook make -- ...`). Treat those as historical phrasing and convert them to v1 `ph` equivalents when implementing or generating templates.

Preferred guidance for v1:

- Use `ph ...` commands (not `make ...` targets) in new templates and examples.
- Prefer `ph --root <path> ...` when running inside a mono-repo or when `cwd` is ambiguous.
