---
title: CLI Plan – Backlog
type: backlog
date: 2026-02-05
tags: [cli, plan, backlog, tech-debt]
links:
  - ./AI_AGENT_START_HERE.md
  - ./session_logs.md
  - ./v1_cli/CLI_CONTRACT.md
---

# CLI Plan – Backlog

Backlog items that are **out of scope for strict-parity checkbox tasks**, but should be tracked for follow-up.

## Backlog items

### BL-0001 — Add first-class ADR commands + stronger ADR validation

Description:

Elevate ADRs to a first-class CLI surface by adding a dedicated `ph adr ...` command family (at minimum `ph adr add`) and strengthening ADR validation beyond the current minimal checks.

Scope:

- Add `ph adr add` to scaffold a new ADR Markdown file under `PH_ROOT/adr/` with correct filename/id alignment and required front matter.
- Add ADR-focused validation (either `ph adr validate` or expand `ph validate`) to enforce required headings/structure and stronger invariants (e.g. uniqueness, supersession consistency).

Notes:

- This conflicts with the current v1 ADR contract statement: humans create/edit ADRs directly and there are no `ph adr ...` commands.
- Implementation MUST preserve the v1 rule that `ph` does not execute repo-local code at runtime; ADR scaffolding/validation must be internal to the installed CLI.

Requires contract/spec changes: yes

Impacted sources of truth:

- `cli_plan/v1_cli/CLI_CONTRACT.md` (new `ph adr` surface)
- `cli_plan/ph_spec/ph/adr/contract.md` (creation/ownership/validation rules update)
- `cli_plan/archive/strict_parity_2026-02/v0_make/MAKE_CONTRACT.md` (parity note: v0 had no ADR target; this is a v1+ enhancement)

Acceptance criteria:

- `ph adr add --id ADR-#### --title <t> [--status draft] [--date YYYY-MM-DD] [--force]` creates a new ADR file that passes `ph validate`.
- Validation enforces at least: `type: adr`, allowed `status`, filename/id alignment, unique ADR ids, and recommended required headings (configurable if needed).
- CLI refuses to overwrite an existing ADR unless `--force` is provided.

### BL-0002 — Refactor CLI tests away from Make-era strict output parity

Description:

Now that Make-era parity has been achieved, reduce brittleness by refactoring tests to focus on functional behavior (files written, exit codes, key messages) rather than byte-for-byte stdout parity (especially preamble lines and legacy formatting quirks).

Scope:

- Rename tests and helper functions to remove `make`/`parity` wording where it no longer reflects intent.
- Replace full-stdout equality assertions with targeted assertions: key lines present, exit codes, and output file contents/paths.
- Keep a small number of intentional UX contract tests (e.g. `ph help` topics) if desired, but avoid coupling most tests to exact line wrapping/spacing.

Notes:

- Goal: keep coverage, reduce churn during future CLI improvements.
- If any commands intentionally guarantee a stable output format, document that expectation and keep strict output tests only for those commands.

Requires contract/spec changes: no

Impacted sources of truth:

- `tests/` (refactor assertions + naming)
- `cli_plan/backlog.md` (remove strict-parity assumptions if referenced)

Acceptance criteria:

- All tests still pass with `uv run pytest -q` and `uv run ruff check .`.
- At least one test per command family remains that asserts functional behavior (outputs written, state changes) without relying on exact preamble formatting.
- No remaining tests are named `*_matches_make_*` or assert Make-era command strings in stdout.

### BL-0003 — Define a CLI output-testing policy (what is stable vs flexible)

Description:

Write down what parts of CLI output are considered stable UX contract (and therefore tested strictly) vs flexible implementation detail (tested loosely). This prevents future work from re-introducing strict-parity brittleness unintentionally.

Scope:

- Add a short testing policy doc covering: stable outputs, flexible outputs, and recommended assertion style.
- Optionally introduce a small snapshot mechanism (no new deps required) for the subset of outputs that should remain stable.

Notes:

- This is intentionally lightweight; the goal is developer clarity, not process overhead.

Requires contract/spec changes: no

Impacted sources of truth:

- `cli_plan/README.md` (or a new `cli_plan/testing_policy.md`)
- `tests/` (align with policy)

Acceptance criteria:

- A single doc exists that engineers can follow when adding/changing CLI tests.
- Test suite follows the policy (strict output tests limited to the explicitly stable outputs).

## Tech debt

### TD-0001 — Post-hook validation changes exit code (parity vs “better” behavior)

Context:

- Legacy Make workflow runs quick validation in `process/automation/post_make_hook.py`, but the underlying validator (`process/checks/validate_docs.py`) returns `0` even when it prints `validation: N error(s) ...`, so the overall `pnpm make -- <target>` exit code stays `0` for commands like `task-status`.
- `ph` currently returns non-zero when post-hook validation finds errors (because `src/ph/validate_docs.py:run_validate()` returns `1` when errors > 0, and `src/ph/hooks.py:run_post_command_hook()` returns the validation exit code).
- This was observed during parity work for V1P-0024 and logged in `cli_plan/session_logs.md`.

Current choice (2026-02-05):

- Keep **strict parity** with the legacy Make workflow: post-hook quick validation MUST NOT change the command’s exit code.

Why this matters:

- Strict parity is not “conventionally correct” for CLIs/CI (it hides validation failures in exit status), but it matches Make-era behavior.

Options:

1. **Strict parity:** keep printing the validation summary + writing `status/validation.json`, but do **not** let post-hook validation change the command’s exit code.
2. **Intentional delta:** update `cli_plan/v1_cli/CLI_CONTRACT.md` to explicitly state that post-hook validation errors make the overall `ph` invocation fail, and update parity expectations accordingly.
3. **Configurable:** add a flag/env toggle (default TBD) that selects strict-parity vs strict-validation behavior.

Next steps:

- Decide which option is desired and record it in contract/ADR.
- If choosing strict parity: change `src/ph/hooks.py` to return the original command exit code (still printing validation output).

  {
  "id": "PHASE-N2",
  "order": 2,
  "title": "Task Templates + Pre-Exec Gate UX",
  "goals": [
  "Make `ph task create` output compatible with `ph pre-exec lint` expectations (evidence paths, secret-scan, task id references).",
  "Port legacy pre-exec patterns and ignore rules precisely where needed."
  ]
  }
