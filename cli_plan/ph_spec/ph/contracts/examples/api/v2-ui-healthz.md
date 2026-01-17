---
title: v2 UI Healthz (Aggregate)
type: api
date: 2026-01-05
tags: [contracts, api, tribuence-mini-v2, health, nextjs]
links:
  - ../tribuence-mini-v2/README.md
  - ../../adr/0014-tribuence-mini-v2-auth-gated-ui-bff-and-security-posture.md
  - ../../sprints/archive/2026/SPRINT-2026-01-04-19/tasks/TASK-010-v2-ui-get-api-healthz-aggregate/README.md
---

# Contract: v2 UI Aggregate Health (`GET /api/healthz`)

## Purpose
Provide a single, operator-friendly endpoint on the v2 UI (`app.local`) that quickly answers:
- “Did Vault render the required env keys for the UI container?”
- “Is Apollo Router reachable and responding to GraphQL?”
- “Are optional integrations (AnythingLLM / Twenty) available?”

This endpoint is additive and does not replace the release gate (`make v2-smoke`).

## Endpoint
- Method: `GET`
- Path: `/api/healthz`
- Host: `app.local` (Traefik public host)

## Auth / Exposure
- Intended audience: operator / local bring-up diagnostics.
- Auth: **public** (even when `NEXT_PUBLIC_REQUIRE_AUTH=true`), but must never return secret values.

## Request
No query params, body, or headers required.

## Response (JSON)
### Top-level
- `status`: `ok | degraded | error`
- `generatedAt`: ISO timestamp
- `latencyMs`: time to compute the aggregate response
- `dependencies`: object containing per-check status + latency

### Dependency result shape
Each dependency returns:
- `status`: `ok | degraded | error | skipped`
- `latencyMs`: integer milliseconds
- `details` (optional): non-secret debug details

### Included checks
- `vaultEnv`
  - Confirms presence (not values) of required env keys rendered by Vault.
  - In auth-required mode, includes Keycloak env keys in the required set.
- `router`
  - GraphQL liveness probe using `query { __typename }` against `V2_GRAPHQL_URL`.
- `anythingllm`
  - Detects graph presence (snapshot/probe) and, when present, runs a lightweight query (`anythingWorkspaces { slug }`) without returning the data.
- `twenty`
  - Optional: skipped unless `TWENTY_API_KEY` is available.
  - When enabled, probes Twenty’s internal health endpoint (`http://twenty-server:3150/healthz` by default).

## Errors / Status codes
- Returns HTTP `200` when `status` is `ok` or `degraded`.
- Returns HTTP `503` when `status` is `error`.

## Caching
- `Cache-Control: no-store`

## Test Notes
Local bring-up:
```bash
make v2-up
curl -sS --resolve "app.local:80:127.0.0.1" "http://app.local/api/healthz" | jq
```
