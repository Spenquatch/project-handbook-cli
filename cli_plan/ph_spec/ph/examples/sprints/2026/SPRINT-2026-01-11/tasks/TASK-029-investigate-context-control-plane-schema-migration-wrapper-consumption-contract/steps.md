---
title: Investigate: Context control plane schema migration + wrapper consumption contract - Implementation Steps
type: implementation
date: 2026-01-11
task_id: TASK-029
tags: [implementation]
links: []
---

# Implementation Steps: Investigate: Context control plane schema migration + wrapper consumption contract

## Overview
This is a `session=research-discovery` task. The deliverable is a completed feature-local DR (`DR-0001`) plus execution-ready feature documentation. No product code changes.

## Prerequisites
- `TASK-025` is `done`.

## Step 1 — Ground truth constraints (ADR + feature docs)
1. Read:
   - `ph/adr/0027-v2-context-control-plane-schema.md`
   - `ph/features/v2_context-control-plane-schema/architecture/ARCHITECTURE.md`
   - `ph/features/v2_context-control-plane-schema/implementation/IMPLEMENTATION.md`
2. Create an evidence index at `ph/status/evidence/TASK-029/index.md`.
3. Create the DR file for this task:
   - `ph/features/v2_context-control-plane-schema/decision-register/DR-0001-context-control-plane-migration-and-consumption-contract.md`

## Step 2 — Inventory current Context surfaces (repo inspection only)
Goal: define an additive migration plan, grounded in what Context already has.
1. Inspect the current Context service structure and schema (read-only):
   - `v2/services/context/` (schema sources, resolvers, migrations)
2. Capture evidence:
   - current GraphQL schema surface related to workspaces/capabilities,
   - current DB migration layout and any existing tables that overlap with ADR-0027 concepts.

Evidence to capture (examples; adjust to match repo reality):
- `ph/status/evidence/TASK-029/context-schema-notes.txt`
- `ph/status/evidence/TASK-029/context-migrations-inventory.txt`

## Step 3 — Define two viable migration/consumption approaches (A/B)
Update DR-0001 with exactly two viable options:
- **Option A**: additive expansion in the existing Context service with one canonical snapshot query; UI + wrappers consume directly.
- **Option B**: dedicated control-plane subgraph (Context writes; consumers read from the control-plane graph).

Each option must specify:
- the canonical snapshot query name + inputs + response shape (types and key fields),
- wrapper/UI consumption contract (required headers, caching posture, timeout/fallback semantics),
- federation approach (if any) and how wrappers call it deterministically,
- rollout sequencing (what ships first, backwards compatibility, deprecation plan),
- invariants enforcement (no provider secrets stored/returned; idempotency keys).

## Step 4 — Complete DR-0001 + update feature docs
1. Fill in DR-0001 (replace placeholders, add evidence references).
2. Update:
   - `ph/features/v2_context-control-plane-schema/architecture/ARCHITECTURE.md`
   - `ph/features/v2_context-control-plane-schema/implementation/IMPLEMENTATION.md`
3. End with an explicit operator approval request and keep DR status `Proposed` until approval.

## Step 5 — Validate handbook + wrap for review
1. Run `ph validate`.
2. Update `validation.md` and `checklist.md` with the evidence file list.
3. Set task status to `review`.
