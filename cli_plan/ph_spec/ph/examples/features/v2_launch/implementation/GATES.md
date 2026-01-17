---
title: v2 Launch Gates (Runner Spec)
type: implementation-note
feature: v2_launch
date: 2026-01-07
tags: [launch, gates, validation]
links:
  - ../../status.md
  - ../../../adr/0028-v2-launch.md
---

# v2 Launch Gates (Runner Spec)

## Goal
Define the single “launch gate runner” entrypoint required by `ADR-0028`, including:
- gate ordering,
- pass/fail criteria,
- deterministic output,
- evidence capture conventions.

This document is the target output for `TASK-006` (and is validated by `TASK-007`).

## Runner Contract
The runner must:
- run gates in a deterministic order,
- fail fast with actionable output,
- emit a stable summary at the end (pass/fail per gate),
- support writing evidence artifacts under `project-handbook/status/evidence/<TASK-ID>/`.

## Runner Entrypoint (single command)

The canonical runner entrypoint is:

```bash
EVIDENCE_DIR="../project-handbook/status/evidence/<TASK-ID>" make -C v2 v2-launch-gates
```

Runner requirements:
- `EVIDENCE_DIR` is required (fail fast with an actionable error if missing).
- Evidence artifacts are written under `$EVIDENCE_DIR/` using deterministic filenames.
- The runner prints a stable per-gate PASS/FAIL summary.

## Gate Inventory (v0.4.1 / SPRINT-2026-01-07)

This sprint’s scope is intentionally minimal: scaffold the runner and validate the handbook + baseline v2 smoke.

| Gate | Command(s) | Success Criteria | Evidence |
|------|------------|------------------|----------|
| Handbook validation | `pnpm -C project-handbook make -- validate` | exits `0` | `$EVIDENCE_DIR/handbook-validate.txt` |
| v2 smoke (router mode) | `V2_SMOKE_MODE=router make -C v2 v2-smoke` | exits `0` | `$EVIDENCE_DIR/v2-smoke-router.txt` |
| onboarding E2E (Playwright) | `pnpm -C apps/tribuence-mini exec playwright test e2e/onboarding-workspace-create-harness.spec.ts --output "$(cd "$EVIDENCE_DIR" && pwd)/playwright"` | exits `0` | `$EVIDENCE_DIR/playwright-onboarding.txt` + `$EVIDENCE_DIR/playwright/` |

## Evidence Conventions
For any gate run (especially failures), capture:
- the exact command line(s),
- the relevant output (stdout/stderr),
- any stable identifiers (correlation ids, timestamps),
- minimal logs only (avoid secrets).

## Immediate Sprint Scope (v0.4.1)
This sprint’s integration gate (`TASK-007`) focuses on the three P1 fixes + baseline smoke evidence, and scaffolds the
runner so future gates can be added incrementally.

## Future Gates (post v0.4.1)

The full `ADR-0028` gate set is broader than this sprint’s runner scope; add additional gates incrementally as they
become execution-ready (each with concrete command(s), pass/fail criteria, and deterministic evidence artifacts).
