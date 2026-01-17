---
id: ADR-0007
title: Tribuence Mini v2 (Federated GraphQL + Context Service)
type: adr
status: draft
date: 2025-12-22
supersedes: null
superseded_by: null
tags: [tribuence-mini, v2, graphql, federation, apollo-router, context]
links:
  - ../../v2/ARCHITECTURE.md
  - ../features/tribuence-mini-v2/overview.md
  - ../contracts/tribuence-mini-v2/supergraph-router.md
  - ../contracts/tribuence-mini-v2/context-subgraph.md
---

# Context

Tribuence Mini v2 requires consolidating multiple upstream systems (Twenty CRM and AnythingLLM) into a single, stable application surface with:

- consistent auth/secrets bootstrapping,
- a single contract for the UI,
- a “context layer” that adds workspaces, reference IDs, and metadata that do not exist upstream.

The repository already carries baseline infrastructure patterns (Traefik, Vault, Keycloak, Postgres) and an existing UI seed (`apps/tribuence-mini`) that should be reused for v2.

# Decision

1. **Promote Twenty CRM and AnythingLLM to core services** in the v2 compose stack (not optional overlays).
2. Replace ad-hoc REST proxies with a **federated GraphQL supergraph** behind **Apollo Router**:
   - Twenty subgraph (upstream GraphQL),
   - Tribuence Context subgraph (new),
   - AnythingLLM subgraph (full API surface via wrapper if needed).
3. Add a **Tribuence Context Service** to own:
   - workspaces,
   - reference IDs,
   - document/chat metadata,
   - GraphQL resolvers for the context subgraph.
4. Standardize secrets via **Vault dev + agent**, rendering env for Router, Context service, Next UI, and AnythingLLM.
5. Preserve upstream forks under `oss-forks/*` as **read-only** (no edits); use images/config only.

# Consequences

## Positive
- UI depends on a single contract (GraphQL) and can evolve without per-service REST glue.
- Context layer becomes the clear integration point for cross-system workflows (workspace/reference → Twenty entities → AnythingLLM ingestion/chat).
- Vault standardization reduces configuration drift across services.

## Tradeoffs / Risks
- Federation adds operational and schema composition complexity.
- AnythingLLM may require a wrapper layer to expose a GraphQL surface cleanly.
- Auth alignment across Router/Next/Keycloak and upstream services needs careful sequencing.

# Rollout

1. Stand up `v2/` compose skeleton (Traefik + Vault + Postgres + Keycloak).
2. Add Apollo Router and federate Twenty first (baseline supergraph).
3. Add Context service and federate its subgraph.
4. Add AnythingLLM and federate its subgraph.
5. Migrate UI (`v2/apps/tribuence-mini`) to GraphQL-only.
6. Add `make v2-smoke` to validate federation, CRUD probes, doc upload, and chat.

# Acceptance Criteria

This ADR is satisfied when the acceptance criteria in `v2/ARCHITECTURE.md` are met (compose bring-up, federation, context layer, secrets bootstrap, smoke testing, and documentation).
