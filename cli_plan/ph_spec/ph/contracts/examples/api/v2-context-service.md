---
title: API Contract - v2 Context Service (health + graphql)
type: api
date: 2026-01-02
tags: [contracts, api, tribuence-mini-v2, context]
links:
  - ../tribuence-mini-v2/context-subgraph.md
  - ../../sprints/archive/2025/SPRINT-2025-12-22/tasks/TASK-014-v2-context:-service-skeleton-+-health-graphql/README.md
---

# API Contract: v2 Context Service

## Audience
Internal-only (reachable on the v2 docker network as `http://context:4010`).

## GET `/health`

### Auth
None.

### Request
- Headers: none required

### Response (200)
- `application/json`
- Shape: `{ ok: boolean, service: string, ... }`

## POST `/graphql`

### Auth
None (local/dev). Router-propagated headers are consumed when implemented:
- `x-tenant-id` (optional)
- `x-workspace-id` (optional)

### Request
- Headers:
  - `content-type: application/json`
- Body:
  - `query: string`
  - `variables?: object`
  - `operationName?: string`

### Response (200)
- `application/json` GraphQL response envelope:
  - `data?: object`
  - `errors?: array`

### Notes
- Schema and header semantics: `ph/contracts/tribuence-mini-v2/context-subgraph.md`
