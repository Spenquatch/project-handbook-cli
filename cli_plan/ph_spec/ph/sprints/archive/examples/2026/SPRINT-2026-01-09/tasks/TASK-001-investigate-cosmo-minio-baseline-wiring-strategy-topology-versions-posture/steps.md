---
title: Investigate: Cosmo+MinIO baseline wiring strategy (topology, versions, posture) - Implementation Steps
type: implementation
date: 2026-01-09
task_id: TASK-001
tags: [implementation]
links: []
---

# Implementation Steps: Investigate: Cosmo+MinIO baseline wiring strategy (topology, versions, posture)

## Overview
This is a `session=research-discovery` task. The deliverable is a completed Decision Register entry (`DR-0003`) plus execution-ready feature documentation. No product code changes.

## Prerequisites
- `TASK-005` is `done` (evidence conventions exist at `project-handbook/status/evidence/TASK-005/README.md`)

## Step 1 — Ground truth the constraints (ADR + feature docs)
1. Read:
   - `project-handbook/adr/0015-tribuence-mini-v2-cosmo-minio-and-schema-publishing.md`
   - `project-handbook/features/v2_registry-cosmo-minio-required/overview.md`
   - `project-handbook/features/v2_registry-cosmo-minio-required/architecture/ARCHITECTURE.md`
   - `project-handbook/features/v2_registry-cosmo-minio-required/implementation/IMPLEMENTATION.md`
   - `project-handbook/decision-register/DR-0003-cosmo-minio-baseline-topology.md`
2. Extract (and write into the evidence index):
   - required Cosmo dependencies per ADR-0015 (ClickHouse, Redis, NATS, Cosmo Keycloak, etc),
   - posture rules: no Traefik exposure, and the DR must choose exactly one host-bind posture:
     - Option A: strict internal-only (no host port binds)
     - Option B: operator-only binds to `127.0.0.1` (localhost-only)

Evidence to capture:
- `project-handbook/status/evidence/TASK-001/index.md` (table-of-contents + “what each artefact proves”)

## Step 2 — Inventory current v2 wiring patterns (compose + Vault)
Goal: decide how Cosmo/MinIO should “fit” the existing v2 conventions.
1. Inspect current v2 compose baseline:
   - `v2/infra/compose/docker-compose.v2.yml` (networks, volumes, port posture, “internal-only” patterns)
   - `v2/infra/compose/traefik/configs/*` (what is exposed)
2. Inspect Vault patterns:
   - `v2/scripts/vault/bootstrap-v2.sh` (KV layout and seeding approach)
   - `v2/infra/vault/templates/*.tpl` (rendered `/secrets/*.env` conventions)

Evidence to capture (examples; follow TASK-005 conventions):
- `project-handbook/status/evidence/TASK-001/v2-compose-inventory.txt`
- `project-handbook/status/evidence/TASK-001/v2-vault-kv-layout-snippets.txt`
- `project-handbook/status/evidence/TASK-001/v2-vault-templates-inventory.txt`

## Step 3 — Define two viable topology options (A/B)
Update `DR-0003` with two options (no third option):
- **Option A** (minimal subset): the smallest Cosmo+MinIO+deps inventory that still satisfies ADR-0015’s guarantees.
- **Option B** (full inventory): vendor the upstream Cosmo compose inventory into v2, then lock down exposure per posture.

Each option must specify, explicitly:
- service inventory (Cosmo services + dependencies + MinIO),
- image tags (pin exact versions),
- persistent volumes/data paths,
- network wiring (no Traefik exposure; choose exactly one: no host binds (A) or localhost-only operator binds (B)),
- required Vault secrets (high-level only; detailed contract belongs in `TASK-002` / `DR-0004`),
- bootstrap and smoke probes needed to enforce posture.

## Step 4 — Complete `DR-0003` (with evidence + recommendation)
1. Replace all “Pending research…” placeholders in:
   - `project-handbook/decision-register/DR-0003-cosmo-minio-baseline-topology.md`
2. Add links to evidence files under `project-handbook/status/evidence/TASK-001/`.
3. End the DR with:
   - recommended option (A or B),
   - crisp rationale,
   - explicit operator approval request (keep status `Proposed`).

## Step 5 — Update feature docs to be execution-ready (pending approval)
Update these docs to reflect the **recommended** option (explicitly marked “pending operator approval”):
- `project-handbook/features/v2_registry-cosmo-minio-required/architecture/ARCHITECTURE.md`
- `project-handbook/features/v2_registry-cosmo-minio-required/implementation/IMPLEMENTATION.md`

Include:
- exact v2 files that will change to implement the topology,
- smoke probes to validate:
  - Cosmo is healthy,
  - MinIO buckets exist,
  - Cosmo/MinIO are not reachable via Traefik.

## Step 6 — Validate handbook + wrap for review
1. Run `pnpm -C project-handbook make -- validate`.
2. Complete `validation.md` and `checklist.md` requirements.
3. Set task status to `review`.
