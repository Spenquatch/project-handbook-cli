---
title: Investigate: Vault seeding + secrets contract for Cosmo/MinIO (no leakage) - Implementation Steps
type: implementation
date: 2026-01-09
task_id: TASK-002
tags: [implementation]
links: []
---

# Implementation Steps: Investigate: Vault seeding + secrets contract for Cosmo/MinIO (no leakage)

## Overview
This is a `session=research-discovery` task. The deliverable is a completed Decision Register entry (`DR-0004`) plus an execution-ready secrets contract documented in the owning feature.

## Prerequisites
- `TASK-005` is `done` (evidence conventions exist at `project-handbook/status/evidence/TASK-005/README.md`)

## Step 1 — Read constraints (ADR + DR + current v2 Vault patterns)
Read:
- `project-handbook/adr/0015-tribuence-mini-v2-cosmo-minio-and-schema-publishing.md`
- `project-handbook/decision-register/DR-0004-vault-secrets-contract-cosmo-minio.md`
- `v2/scripts/vault/bootstrap-v2.sh`
- `v2/infra/vault/templates/*.tpl`

Start `project-handbook/status/evidence/TASK-002/index.md` and list what each evidence artefact proves.

## Step 2 — Inventory the existing v2 Vault contract (baseline)
Document the “current state” contract that Cosmo/MinIO must fit into:
- existing KV paths (today: `kv/data/tribuence/v2/{next,router,context,anythingllm}`)
- existing rendered outputs (today: `/secrets/{next.env,router.env,context.env,anythingllm.env}`)
- existing “no secrets printed” mechanisms in `bootstrap-v2.sh` (e.g. warnings that avoid printing values)

Evidence to capture:
- `project-handbook/status/evidence/TASK-002/v2-vault-kv-layout.txt`
- `project-handbook/status/evidence/TASK-002/v2-vault-templates-inventory.txt`
- `project-handbook/status/evidence/TASK-002/v2-vault-bootstrap-no-leakage-snippets.txt`

## Step 3 — Define two viable secrets contract options (A/B)
Update `DR-0004` with exactly two options (no third option):
- **Option A** — single KV layout + a small number of rendered env files for Cosmo/MinIO.
- **Option B** — per-service KV keys + per-service env templates (more granular).

Each option must specify, explicitly:
- KV paths and required fields (names, not values),
- which templates will exist under `v2/infra/vault/templates/` and which env files they produce,
- how bootstrap seeds required values idempotently without printing secrets,
- how to support Cosmo dependencies (e.g. DB creds, NATS, Redis, ClickHouse) without leaking.

## Step 4 — Complete `DR-0004` (with evidence + recommendation)
1. Replace all “Pending research…” placeholders in:
   - `project-handbook/decision-register/DR-0004-vault-secrets-contract-cosmo-minio.md`
2. Add links to evidence files under `project-handbook/status/evidence/TASK-002/`.
3. End the DR with a recommendation (A or B) and explicit operator approval request (keep status `Proposed`).

## Step 5 — Update feature implementation doc (execution-ready contract)
Update:
- `project-handbook/features/v2_registry-cosmo-minio-required/implementation/IMPLEMENTATION.md`

Include:
- exact KV path(s) + fields for Cosmo/MinIO (recommended option),
- rendered env files (exact filenames under `/secrets/`),
- a “no secrets printed” checklist for implementation agents (what not to log/capture; what to redact),
- exact v2 files that will change (bootstrap script + templates + compose env mounts).

## Step 6 — Validate handbook + wrap for review
1. Run `pnpm -C project-handbook make -- validate`.
2. Complete `validation.md` and `checklist.md`.
3. Set task status to `review`.
