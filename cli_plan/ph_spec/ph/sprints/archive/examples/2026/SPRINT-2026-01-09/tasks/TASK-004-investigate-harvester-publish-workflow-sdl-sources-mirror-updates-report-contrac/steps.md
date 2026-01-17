---
title: Investigate: Harvester publish workflow (SDL sources, mirror updates, report contract) + codegen wiring - Implementation Steps
type: implementation
date: 2026-01-09
task_id: TASK-004
tags: [implementation]
links: []
---

# Implementation Steps: Investigate: Harvester publish workflow (SDL sources, mirror updates, report contract) + codegen wiring

## Overview
This is a `session=research-discovery` task. The deliverable is a completed Decision Register entry (`DR-0006`) plus execution-ready harvester/codegen workflow documentation.

## Prerequisites
- `TASK-005` is `done` (evidence conventions exist at `project-handbook/status/evidence/TASK-005/README.md`)

## Step 1 — Read constraints (ADRs + feature docs + DR)
Read:
- `project-handbook/adr/0021-v2-schema-harvester-service.md`
- `project-handbook/adr/0019-v2-codegen-from-registry.md`
- `project-handbook/decision-register/DR-0006-harvester-publish-and-codegen-workflow.md`
- `project-handbook/features/v2_schema-harvester-service/implementation/IMPLEMENTATION.md`
- `project-handbook/features/v2_codegen-from-registry/implementation/IMPLEMENTATION.md`

Start `project-handbook/status/evidence/TASK-004/index.md` and list what each evidence artefact proves.

## Step 2 — Inventory current SDL mirror layout (baseline)
Goal: make “current state” explicit so mirror update rules are concrete.
Inspect:
- `v2/infra/compose/graphql/subgraphs.yaml` (declares subgraphs and schema files)
- `v2/infra/compose/graphql/subgraphs/*/schema.graphql` (mirrors exist today)
- `v2/infra/compose/graphql/supergraph-local.graphql` (local composed artifact; do not copy into evidence)

Evidence to capture:
- `project-handbook/status/evidence/TASK-004/subgraphs-yaml.txt`
- `project-handbook/status/evidence/TASK-004/subgraphs-schema-files.txt`
- `project-handbook/status/evidence/TASK-004/supergraph-local-stats.txt`

## Step 3 — Inventory existing v2 smoke/gate expectations (inputs to publish/check)
Inspect:
- `v2/scripts/v2-smoke.sh` (what is currently validated; where composition assumptions live)
- any existing references to “publish” or “codegen” in the repo (likely in ADRs/features only).

Evidence to capture:
- `project-handbook/status/evidence/TASK-004/v2-smoke-schema-hooks.txt`
- `project-handbook/status/evidence/TASK-004/rg-codegen.txt`

## Step 4 — Define two viable workflow options (A/B)
Update `DR-0006` with exactly two options:
- **Option A** — Harvester introspects running subgraphs; codegen pulls schemas directly from Cosmo.
- **Option B** — Harvester uses repo contract SDL (or hybrid); codegen reads mirrors that are derived from Cosmo.

Each option must specify:
- inputs per subgraph (introspection endpoint vs file),
- publish sequencing and composition check triggers,
- mirror update rules (atomic, only after success),
- report contract (JSON schema / fields) and sanitization rules,
- codegen wiring (local command + CI gate ordering).

## Step 5 — Complete `DR-0006` (with evidence + recommendation)
1. Replace all “Pending research…” placeholders in:
   - `project-handbook/decision-register/DR-0006-harvester-publish-and-codegen-workflow.md`
2. Add links to evidence files under `project-handbook/status/evidence/TASK-004/`.
3. End the DR with recommendation + operator approval request (keep status `Proposed`).

## Step 6 — Update feature implementation docs (execution-ready plan)
Update:
- `project-handbook/features/v2_schema-harvester-service/implementation/IMPLEMENTATION.md`
- `project-handbook/features/v2_codegen-from-registry/implementation/IMPLEMENTATION.md`

Include:
- exact v2 files that will be added/changed to implement the workflow (harvester service, scripts, Vault keys, CI steps),
- the canonical publish/check command and the canonical codegen command,
- explicit dependency ordering: publish/check must run before codegen/typecheck.

## Step 7 — Validate handbook + wrap for review
1. Run `pnpm -C project-handbook make -- validate`.
2. Complete `validation.md` and `checklist.md`.
3. Set task status to `review`.
