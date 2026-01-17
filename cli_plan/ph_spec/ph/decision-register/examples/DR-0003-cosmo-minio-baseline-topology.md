---
title: DR-0003 — Cosmo + S3 Artifact Store Baseline Topology (v2 Default Stack)
type: decision-register
date: 2026-01-09
tags: [decision-register, cosmo, minio, seaweedfs, rustfs, v2, infra]
links:
  - ../releases/current/plan.md
  - ../adr/0015-tribuence-mini-v2-cosmo-minio-and-schema-publishing.md
  - ../features/v2_registry-cosmo-minio-required/overview.md
---

# Decision Register Entry

### DR-0003 — Cosmo + S3 Artifact Store Baseline Topology (v2 Default Stack)

**Decision owner(s):** @spenser  
**Date:** 2026-01-09  
**Status:** Accepted  
**Related docs:** `ADR-0015`, `v2_registry-cosmo-minio-required`, `TASK-001`

**Problem / Context**
- This DR ID was reserved during sprint planning to enable a `session=research-discovery` task; it must be completed in `TASK-001` and requires operator/user approval before being marked `Accepted`.
- We need a deterministic, internal-only Cosmo baseline in the default v2 stack that is stable across local/dev and supports downstream publish/composition/codegen workflows.
- We need an S3-compatible artifact store for Cosmo. ADR-0015 names MinIO, but operator input indicates the MinIO community posture/support may be degrading; we should consider an S3 drop-in replacement if it reduces long-term risk.
- Key unknowns that can change scope/effort:
  - which Cosmo components are required and which upstream “extras” we can avoid,
  - how we wire Cosmo into v2 Postgres/Vault while preserving “no Traefik exposure”, and
  - whether we keep MinIO or swap to a different S3-compatible store (SeaweedFS or RustFS).
- Evidence for this decision lives under `ph/status/evidence/TASK-001/` (start at `index.md`).
- Legacy note: we have a known-good reference implementation in `modular-oss-saas/infra/compose/*` and `modular-oss-saas/scripts/infra/*` (DB bootstrap, migrations, bucket init, and Cosmo Keycloak realm), and should reuse that shape where it aligns with v2 conventions (evidence: `ph/status/evidence/TASK-001/legacy-modular-cosmo-minio-snippets.txt`).
- Replacement candidates:
  - SeaweedFS: documented single-node S3 gateway via `weed server -s3` / `weed mini` (S3 endpoint `:8333`) (evidence: `ph/status/evidence/TASK-001/seaweedfs-readme-snippets.txt`).
  - RustFS: “MinIO-like” ops but currently `1.0.0-alpha.*` and its S3 test harness filters out some feature suites (evidence: `ph/status/evidence/TASK-001/rustfs-s3tests-snippets.txt`, `ph/status/evidence/TASK-001/rustfs-dockerhub-tags.txt`).

**Option A — SeaweedFS S3 gateway as the Cosmo artifact store (strict internal-only, no host binds)**
- **Pros:**
  - Avoids betting the baseline on MinIO’s community posture while staying S3-compatible for Cosmo.
  - SeaweedFS documents a single-node S3 setup (`weed server -s3` / `weed mini`) with an S3 endpoint on `:8333` (evidence: `ph/status/evidence/TASK-001/seaweedfs-readme-snippets.txt`).
  - Uses stable release tags on Docker Hub (evidence: `ph/status/evidence/TASK-001/seaweedfs-dockerhub-tags.txt`).
- **Cons:**
  - SeaweedFS itself notes MinIO is more ideal for close AWS S3 parity and that SeaweedFS is “trying to catch up” (evidence: `ph/status/evidence/TASK-001/seaweedfs-readme-snippets.txt`).
  - Introduces a new storage system to v2; even in single-node mode it has more concepts than MinIO.
  - Requires ADR update/superseding decision because ADR-0015 currently names MinIO explicitly.
- **Cascading implications:**
  - v2 compose gains a Cosmo + SeaweedFS “infra cluster” that downstream tasks rely on (`TASK-003`, `TASK-004`).
  - Secrets contract must be extended to cover SeaweedFS S3 gateway credentials (SeaweedFS docs show `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`) stored in Vault and rendered to an env file (evidence: `ph/status/evidence/TASK-001/seaweedfs-readme-snippets.txt`).
- **Risks:**
  - Compatibility surprises only show up when Cosmo starts writing/reading artifacts; mitigate with an early “Cosmo artifact write/read” smoke probe.
- **Unlocks:**
  - Removes MinIO dependency while keeping an S3-compatible contract.
- **Quick wins / low-hanging fruit:**
  - Stand up SeaweedFS S3 in single-node mode (`weed server -s3`) on the v2 network and wire Cosmo `S3_STORAGE_URL` to `http://<access>:<secret>@seaweedfs:8333/<bucket>`.
  - Use a generic S3 client (e.g. `amazon/aws-cli`) for bucket init so we’re not coupled to MinIO tooling.

  **Service inventory (proposed)**
  - Reuse existing v2 services:
    - `postgres` (`pgvector/pgvector:pg15`) for Cosmo controlplane DB
    - `vault` + `vault-agent` for secrets rendering
  - Add to v2 compose (all internal-only, attached to `tribuence-v2-net`, no `ports:`):
    - `seaweedfs` — `chrislusf/seaweedfs:4.05` running `weed server -s3` (S3 endpoint `:8333`)
    - Cosmo dependencies + services:
      - `cosmo-clickhouse` — `clickhouse/clickhouse-server:24.12`
      - `cosmo-redis` — `redis:7.2.4-alpine`
      - `cosmo-nats` — `nats:2.10.6`
      - `cosmo-keycloak` — `ghcr.io/wundergraph/cosmo/keycloak@sha256:660b4b95810751cf052ac90273c9ccfe2d2d7e61275377e3ac6176ef87010f58`
      - `cosmo-cdn` — `ghcr.io/wundergraph/cosmo/cdn@sha256:0d8fcbc3784206511ddcd27ede4eb6585ed89520c466521a9ada2f6b22af8d3b`
      - `cosmo-controlplane` — `ghcr.io/wundergraph/cosmo/controlplane@sha256:f31a50a2230c182673272983c8ccb89dc7d060c3094d8b929b4366d4617d741d`
      - `cosmo-studio` — `ghcr.io/wundergraph/cosmo/studio@sha256:4d9aa4d6633ea535b1a50a77fd3b6dc41df7a70c5aabb9479ce903e099b77a18`
    - One-shot jobs:
      - `cosmo-postgres-bootstrap` (reuse known-good modular script shape)
      - `cosmo-db-migration` / `cosmo-clickhouse-migration`
      - `artifact-bucket-init` — `amazon/aws-cli` (S3 bucket create idempotently against `http://seaweedfs:8333`)
      - `cosmo-seed` (profile-gated)

  **Persistent volumes (proposed)**
  - `seaweedfs-data-v2` (SeaweedFS data dir)
  - `cosmo-clickhouse-data-v2` (ClickHouse)
  - `cosmo-redis-data-v2` (Redis)
  - `postgres-data-v2` (existing; shared Postgres)

  **Vault + env rendering (high-level; detailed in DR-0004/TASK-002)**
  - KV paths:
    - `kv/data/tribuence/v2/artifacts` (S3 endpoint + creds + bucket)
    - `kv/data/tribuence/v2/cosmo`
  - Rendered env files:
    - `/secrets/artifacts.env` (used by `seaweedfs` and `artifact-bucket-init`)
    - `/secrets/cosmo.env` (used by Cosmo services + migrations/seed jobs)

  **Bootstrap + smoke probes (minimum)**
  - Smoke probes:
    - `cosmo-controlplane`: `GET /health` (container-local)
    - artifact store: S3 bucket list/create via a client against `http://seaweedfs:8333` (container-local)
    - Negative exposure check: host access to Cosmo/artifact-store ports should fail (no host binds), and Traefik config must not contain Cosmo/artifact-store routers.

**Option B — Keep MinIO now (known-good) and plan SeaweedFS migration later (explicit tech debt)**
- **Pros:**
  - Lowest execution risk now: MinIO is already proven in the legacy modular compose + bootstrap scripts (bucket init, migrations, wiring) (evidence: `ph/status/evidence/TASK-001/legacy-modular-cosmo-minio-snippets.txt`).
  - Aligns with ADR-0015 as written (MinIO explicitly named), avoiding immediate ADR churn.
  - Unblocks the v0.5.0 registry pipeline quickly.
- **Cons:**
  - Accepts tech debt: if MinIO support posture degrades, migration happens later under time pressure.
  - Migration work still needs to happen later (SeaweedFS wiring + compatibility validation).
- **Cascading implications:**
  - Implement MinIO wiring in a store-agnostic way so migration is bounded:
    - use `amazon/aws-cli` for bucket init (not `minio/mc`),
    - centralize endpoint/creds/bucket in one rendered env file for Cosmo to consume, and
    - add a “Cosmo artifact write/read” smoke probe that will be reused for SeaweedFS.
- **Risks:**
  - If we leak MinIO-specific assumptions into wiring, migration cost grows (mitigate by the store-agnostic steps above).
- **Unlocks:**
  - Keeps the fastest path to a working baseline while preserving an evidence-backed migration target (SeaweedFS).
- **Quick wins / low-hanging fruit:**
  - Implement MinIO now using pinned images and generic bucket init tooling, then create a follow-up migration decision task.

**Recommendation**
- **Recommended:** Option B — Keep MinIO now (known-good) and plan SeaweedFS migration later (explicit tech debt)
- **Rationale:** Between RustFS and SeaweedFS, SeaweedFS appears more mature and has documented single-node S3 wiring; however, SeaweedFS itself notes it is still catching up to MinIO’s S3 parity. To minimize near-term risk and unblock v0.5.0, keep MinIO now (proven wiring + matches ADR-0015) and immediately queue a SeaweedFS replacement sprint/series so this does not become “silent tech debt”. Implementation stays store-agnostic from day one (generic bucket init + reusable “Cosmo artifact write/read” probe) so the cutover is bounded and measurable.

**Follow-up tasks (explicit)**
- After operator/user approval (required before moving this DR to `Accepted`):
  - Create execution tasks for `v2_registry-cosmo-minio-required` to:
    - add the Cosmo services + volumes + healthchecks to `v2/infra/compose/docker-compose.v2.yml`,
    - add the selected S3 artifact store service (MinIO now; SeaweedFS if Option A is selected) + bucket init job,
    - implement Vault seeding + template rendering for `/secrets/cosmo.env` plus an artifact-store env file (recommended: `/secrets/artifacts.env`) (align with `DR-0004`),
    - implement idempotent DB bootstrap + migrations + bucket init + Cosmo seed workflow, and
    - add smoke probes that enforce the “no Traefik exposure” posture.
  - If Option B is approved (MinIO now, replace immediately after baseline is green):
    - Create and schedule a bounded follow-up task series to replace MinIO with SeaweedFS, with explicit acceptance criteria:
      - SeaweedFS S3 gateway runs in the v2 network (internal-only).
      - Cosmo artifact write/read probe passes against SeaweedFS.
      - MinIO removed from the default v2 compose after successful cutover.
    - Create a follow-up decision/ADR to replace MinIO with SeaweedFS (and supersede/adjust ADR-0015 wording from “MinIO required” to “S3-compatible artifact store required”).

**Operator/user approval request**
- Approved: **Option B** — Keep MinIO now (known-good) and plan SeaweedFS migration later (immediately after baseline is green).
- Approved by: @spenser (2026-01-10)

## Notes
- Apple Silicon support: Cosmo version tags (e.g. `0.6.0`) are `linux/amd64` only; v2 pins Cosmo images by multi-arch digest so Docker pulls `linux/arm64` on Apple Silicon without emulation.
