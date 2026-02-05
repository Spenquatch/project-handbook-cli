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

## Tech debt

### TD-0001 — Post-hook validation changes exit code (parity vs “better” behavior)

Context:
- Legacy Make workflow runs quick validation in `process/automation/post_make_hook.py`, but the underlying validator (`process/checks/validate_docs.py`) returns `0` even when it prints `validation: N error(s) ...`, so the overall `pnpm make -- <target>` exit code stays `0` for commands like `task-status`.
- `ph` currently returns non-zero when post-hook validation finds errors (because `src/ph/validate_docs.py:run_validate()` returns `1` when errors > 0, and `src/ph/hooks.py:run_post_command_hook()` returns the validation exit code).
- This was observed during parity work for V1P-0024 and logged in `cli_plan/session_logs.md`.

Current choice (2026-02-05):
- Keep the `ph` behavior (non-zero exit on post-hook validation errors) for now.

Why this matters:
- It’s more CI-friendly (fails fast when repo state is invalid), but it is a behavioral drift from Make-era parity.

Options:
1. **Strict parity:** keep printing the validation summary + writing `status/validation.json`, but do **not** let post-hook validation change the command’s exit code.
2. **Intentional delta:** update `cli_plan/v1_cli/CLI_CONTRACT.md` to explicitly state that post-hook validation errors make the overall `ph` invocation fail, and update parity expectations accordingly.
3. **Configurable:** add a flag/env toggle (default TBD) that selects strict-parity vs strict-validation behavior.

Next steps:
- Decide which option is desired and record it in contract/ADR.
- If choosing strict parity: change `src/ph/hooks.py` to return the original command exit code (still printing validation output).
