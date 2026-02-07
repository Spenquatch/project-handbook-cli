---
id: ADR-CLI-0001
title: Replace Makefile Targets with `ph` CLI
type: adr
status: superseded
date: 2026-01-13
tags: [handbook, cli, automation, ergonomics, reliability]
links:
  - ./ADR-CLI-0004-ph-root-layout.md
  - ./CLI_CONTRACT.md
  - ../archive/strict_parity_2026-02/v0_make/MAKE_CONTRACT.md
---

# Note (historical)

This ADR is **superseded** and kept for context only. Do not implement new behavior from this document:

- use `cli_plan/v1_cli/ADR-CLI-0004-ph-root-layout.md` and `cli_plan/v1_cli/CLI_CONTRACT.md` as the sources of truth

# Context

The handbook currently exposes workflows via `make` targets that shell out to Python scripts under `process/automation/*` and `process/checks/*`.

## Update (2026-01-15)

This ADR’s **packaging** motivations still hold, but its original assumptions about:

- the root marker location, and
- system-scope semantics

are superseded by `cli_plan/v1_cli/ADR-CLI-0004-ph-root-layout.md` (marker: `.project-handbook/config.json`, internals under `.project-handbook/**`).

This works well, but reliability issues repeatedly show up around:

- **Directory sensitivity**: running commands from different working directories can change relative-path behavior, especially when scripts spawn subprocesses and assume a `cwd`.
- **Hook duplication**: behavior like “append history” and “auto-run validate-quick unless skipped” is currently implemented as a `make`-level post hook (`process/automation/post_make_hook.py`) with additional exceptions encoded in the `Makefile`.
- **Historical scope split**: the v0 Make interface had a “system scope” via duplicated `hb-*` targets and `PH_SCOPE=system`. v1 removes system scope entirely.

We want a single CLI entrypoint that:

- runs from anywhere (stable repo root detection),
- runs hooks deterministically (history logging + validation) without Make,
- preserves the current “hints + next steps” UX because it is a major productivity multiplier.

Additionally, we want the CLI to be a **first-class installed tool**:
- installable via `uv` / `pip` / `poetry`,
- not dependent on repo-local Python files living inside the handbook instance.

Important constraints from the existing system:

- **Reset** is destructive and must be safe:
  - default: dry-run
  - execute: requires `confirm=RESET` and `force=true` (exact match)
- Validation rules currently live in `process/checks/validation_rules.json` in the legacy repo (ported into the installed CLI).

# Decision

Implement a first-class `ph` CLI (Python-based) that becomes the primary interface for all handbook operations.

## CLI principles (non-negotiable)

1. **Root-stable**: `ph` MUST resolve the handbook repo root regardless of `cwd`.
2. **Hook-stable**: `ph` MUST run pre/post behaviors centrally (no duplicated hook logic in wrappers).
3. **Hint-preserving**: `ph` MUST preserve the existing style of “Next steps” guidance after commands.
4. **Installed tool**: `ph` MUST be installable as a Python package and MUST NOT require executing repo-local Python scripts.

## Packaging and distribution (required)

`ph` MUST be distributed as an installable Python package:

- Distribution name (PyPI): `project-handbook`
- Console script: `ph`
- Supported installation mechanisms:
  - `uv tool install project-handbook`
  - `pipx install project-handbook`
  - `pip install project-handbook`
  - `poetry add project-handbook`

The Project Handbook repository remains viewable and editable (Markdown/JSON/etc) and becomes a “data + templates + planning” instance that the installed `ph` tool operates against.

## Repository marker + schema versioning (required)

The handbook root MUST contain `.project-handbook/config.json` and `ph` MUST treat its presence as the canonical root marker (independent of any repo-local Python scripts).

`.project-handbook/config.json` MUST contain:

- `handbook_schema_version`: integer, MUST be `1` for v1 CLI
- `requires_ph_version`: string, PEP 440 compatible specifier, MUST be `>=0.0.1,<0.1.0`
- `repo_root`: string, MUST be `"."`

On every invocation, `ph` MUST:
- read `.project-handbook/config.json`,
- refuse to run if `handbook_schema_version` is not supported,
- refuse to run if the installed `ph` version does not satisfy `requires_ph_version`,
- print a remediation message that includes the exact `uv tool install ...` command to resolve it.

## Implementation isolation (required)

The v1 CLI implementation MUST be developed in a **separate repository** (not inside the handbook instance repo):

- Repo: `project-handbook-cli` (source for the `project-handbook` distribution)

Rationale:
- the handbook instance repo remains “data only” (no executed Python required),
- the CLI can be versioned, released, and installed independently,
- parity can be validated by running `ph` against the handbook instance while Make remains authoritative.

## Root detection

`ph` resolves the handbook root using a deterministic search strategy:

1. If `--root <path>` is provided, use it (must contain `.project-handbook/config.json`).
2. Else, walk up from `cwd` looking for a directory that contains:
   - `.project-handbook/config.json`
3. If none found, exit with a fatal error that instructs how to run with `--root`.

This makes command behavior independent of the directory you run from.

## Command model

The `ph` CLI command tree mirrors the current Make targets and is defined in `cli_plan/v1_cli/CLI_CONTRACT.md`.

Examples:

- `make task-create ...` → `ph task create ...`

## Hook model

`ph` implements centralized hooks:

### Post-command hook (default enabled)

After a successful command:

1. Append history entry to `.project-handbook/history.log`
2. Run `ph validate --quick --silent-success` unless:
   - the command is `validate` itself, or
   - the command is `reset` / `reset-smoke`, or
   - user passed `--no-validate`.

### Pre-command hook (required for destructive commands)

For destructive commands (reset/migration):

- Enforce confirmation semantics exactly as the existing reset/migration scripts do.

## Implementation strategy

Phase 1: implement `ph` as a standalone engine that reads/writes the handbook instance files directly (no subprocess calls to repo-local Python scripts).

Phase 2: remove the Make interface entirely once parity is proven.

# Options considered

## Option A — Keep Make as primary interface

Pros:
- No migration effort.

Cons:
- `cwd` / subprocess reliability issues remain.
- Hook logic stays split between Makefile and scripts.
- Scope split remains duplicated (`hb-*`).

## Option B — Add CLI and keep Make as compatibility layer (historical; no longer desired)

Pros:
- CLI becomes the authoritative execution environment (root + hooks).
- Reduces friction for existing users while we validate the CLI.

Cons:
- Requires a careful contract and parity work.

## Option C — Replace automation scripts entirely

Pros:
- Clean architecture.

Cons:
- Too high-risk; unnecessary to get reliability improvements.

# Consequences

## Positive

- Commands become stable regardless of working directory.
- Hook behavior is unified and testable.
- Root detection + hook behavior are centralized and consistent.

## Negative / tradeoffs

- Requires maintaining CLI parity with Make targets during transition.
- Requires a clear contract for hints/outputs to avoid UX regression.

# Acceptance criteria

This ADR is complete and accepted when:

- The CLI contract exists and fully enumerates commands, flags, hooks, and outputs (`cli_plan/v1_cli/CLI_CONTRACT.md`).
- A `ph` CLI implementation can run from any subdirectory and produce the same results as running from repo root.
- The post-command hook behavior is centralized in the CLI.
