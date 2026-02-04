---
title: PH Spec Contract — status/evidence/
type: contract
tags: [ph, spec]
---

# Contract

## Directory Purpose
- Path (handbook instance): `PH_ROOT/status/evidence/`
- Summary: Evidence bundles (logs, command outputs, screenshots, and supporting notes) captured during work so decisions and implementations are reviewable and reproducible.

## Ownership
- Owner: Project (human-directed).
- Content artifacts (project-owned; human/agent-authored, often scaffolded/filled via `ph` inputs):
  - `**/*` (arbitrary evidence files; may include Markdown, logs, screenshots, and other artifacts)
- Derived/internal artifacts (CLI-authored; safe to regenerate):
  - (none)
- Overwrite rules:
  - The CLI MUST NOT overwrite evidence artifacts without explicit `--force`.

## Creation
- Created/updated by:
  - `pnpm make -- pre-exec-audit` (creates a `PRE-EXEC/<sprint>/<date>/` evidence bundle by default)
  - Humans/agents create subdirectories and evidence artifacts as needed during work (typically alongside a `TASK-###`).
- Non-destructive:
  - The CLI MUST NOT overwrite evidence artifacts without explicit `--force`.

## Required Files and Directories
- None. This directory MAY be empty.

## Schemas
- Evidence directories are intentionally flexible; any file type is allowed.
- Recommended organization (not required):
  - `TASK-###/` (one directory per task)
    - `index.md` (optional; evidence index/summary for reviewers)
    - `*.log`, `*.txt`, `*.json`, `*.md`, etc.
  - `PRE-EXEC/<SPRINT-...>/<YYYY-MM-DD>/` (pre-execution audit bundles)
    - `EVIDENCE_DIR=...` is printed by the audit runner
    - commonly includes `handbook-validate.txt`, `sprint-status.txt`, `release-status.txt`, and `pre-exec-lint.txt`
- If `TASK-###/index.md` exists, it SHOULD be Markdown with YAML front matter containing at least:
  - `type: evidence`
  - `date: YYYY-MM-DD`
  - `task_id: TASK-###`
  - `tags: [evidence, task, ...]`
  - `links: [<relative path>, ...]`
- YAML front matter MAY include additional keys; unknown keys MUST be preserved.

## Invariants
- Evidence MUST NOT include secret values (credentials, tokens, private keys, unredacted `.env` contents).
- Evidence artifacts SHOULD prefer sanitized outputs (headers redacted, secrets masked) and reference source files/paths when possible.

## Validation Rules
- `ph validate` SHOULD treat evidence as best-effort:
  - it MAY ignore non-Markdown files entirely
  - it SHOULD enforce YAML front matter on any `*.md` evidence files (consistent with global front matter rules)

## Examples Mapping
- `examples/TASK-002/index.md` demonstrates an evidence index with front matter and reviewer-friendly links.
- `examples/TASK-002/*.log` and `examples/TASK-002/*.txt` demonstrate typical raw evidence artifacts captured alongside the index.
