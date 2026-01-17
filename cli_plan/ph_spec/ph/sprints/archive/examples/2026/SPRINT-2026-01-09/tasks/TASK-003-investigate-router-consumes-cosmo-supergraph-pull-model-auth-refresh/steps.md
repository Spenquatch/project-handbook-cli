---
title: Investigate: Router consumes Cosmo supergraph (pull model + auth + refresh) - Implementation Steps
type: implementation
date: 2026-01-09
task_id: TASK-003
tags: [implementation]
links: []
---

# Implementation Steps: Investigate: Router consumes Cosmo supergraph (pull model + auth + refresh)

## Overview
This is a `session=research-discovery` task. The deliverable is a completed Decision Register entry (`DR-0005`) plus an execution-ready Router consumption plan for the owning feature.

## Prerequisites
- `TASK-005` is `done` (evidence conventions exist at `project-handbook/status/evidence/TASK-005/README.md`)

## Step 1 — Read constraints (ADR + feature docs + DR)
Read:
- `project-handbook/adr/0015-tribuence-mini-v2-cosmo-minio-and-schema-publishing.md`
- `project-handbook/adr/0021-v2-schema-harvester-service.md`
- `project-handbook/features/v2_schema-publishing-and-composition/overview.md`
- `project-handbook/features/v2_schema-publishing-and-composition/implementation/IMPLEMENTATION.md`
- `project-handbook/decision-register/DR-0005-router-supergraph-consumption-from-cosmo.md`

Start `project-handbook/status/evidence/TASK-003/index.md` and list what each evidence artefact proves.

## Step 2 — Document current v2 Router supergraph wiring (baseline)
Goal: make the “current state” explicit so the change plan can name exact files.
- Inspect:
  - `v2/infra/compose/docker-compose.v2.yml` (how Router is started and how the supergraph file is mounted)
  - `v2/infra/compose/graphql/router.v2.yaml` (Router runtime config)
  - `v2/infra/vault/templates/router.env.tpl` (supergraph path env)
- Do not capture the full `supergraph-local.graphql` as evidence (it is very large). Capture:
  - file size and a hash,
  - the compose mount line(s) that reference it,
  - and a short header excerpt if needed.

Evidence to capture:
- `project-handbook/status/evidence/TASK-003/router-supergraph-wiring.txt`
- `project-handbook/status/evidence/TASK-003/supergraph-local-stats.txt`

## Step 3 — Define two viable consumption options (A/B)
Update `DR-0005` with exactly two options:
- **Option A** — Router pulls the supergraph directly from Cosmo (startup + periodic refresh).
- **Option B** — Harvester pulls from Cosmo; Router consumes a local artifact file.

Each option must specify:
- auth material and where it lives (Vault KV + rendered env),
- refresh/rotation model (polling, TTL, restart triggers),
- failure modes and required smoke probes,
- exact v2 files that will be updated during implementation.

## Step 4 — Complete `DR-0005` (with evidence + recommendation)
1. Replace all “Pending research…” placeholders in:
   - `project-handbook/decision-register/DR-0005-router-supergraph-consumption-from-cosmo.md`
2. Add links to evidence files under `project-handbook/status/evidence/TASK-003/`.
3. End the DR with recommendation + operator approval request (keep status `Proposed`).

## Step 5 — Update feature implementation doc (execution-ready plan)
Update:
- `project-handbook/features/v2_schema-publishing-and-composition/implementation/IMPLEMENTATION.md`

Include:
- recommended consumption model (pending approval),
- exact v2 config file paths that will change,
- required secrets and how they are rendered (high-level; reference `TASK-002`/`DR-0004` if needed),
- smoke probes to prove Router is serving the Cosmo-produced supergraph.

## Step 6 — Validate handbook + wrap for review
1. Run `pnpm -C project-handbook make -- validate`.
2. Complete `validation.md` and `checklist.md`.
3. Set task status to `review`.
