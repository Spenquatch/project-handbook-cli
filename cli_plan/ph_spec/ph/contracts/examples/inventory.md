---
title: Dashboard / Access Inventory (Host-Exposed)
type: inventory
date: 2026-01-11
tags: [contracts, inventory, access, dashboards, v2]
links:
  - ../process/sessions/templates/endpoint-contract-update.md
  - ../../v2/infra/compose/docker-compose.v2.yml
  - ../../v2/infra/compose/traefik/configs/traefik.v2.yml
---

# Dashboard / Access Inventory (Host-Exposed)

This is the **verified** list of URLs (or host+port) currently exposed for local access to dashboards/services.

Verification scope:
- v2 compose project: `tribuence-v2`
- Traefik entrypoint: `http://127.0.0.1:80` (Host-based routing)
- Verified on: 2026-01-11

## Hostname setup (browser)
For browser access, either add to `/etc/hosts`:
- `127.0.0.1 app.local router.local keycloak.local`

Or use `curl --resolve` in validation commands below.

## Exposed URLs (verified)

### v2 UI (Next.js)
- URL: `http://app.local/` (via Traefik `:80`)
- Verified:
  - `curl -sS -o /dev/null -w '%{http_code}\n' --resolve "app.local:80:127.0.0.1" http://app.local/` → `200`

### v2 Router (Apollo Router GraphQL)
- URL: `http://router.local/` (via Traefik `:80`)
- Verified:
  - `curl -sS --resolve "router.local:80:127.0.0.1" -H 'content-type: application/json' --data '{"query":"query Health { __typename }"}' http://router.local/ | jq -e '.data.__typename'`

### v2 Keycloak (auth UI)
- URL: `http://keycloak.local/` (via Traefik `:80`)
- Verified:
  - `curl -sS -o /dev/null -w '%{http_code}\n' --resolve "keycloak.local:80:127.0.0.1" http://keycloak.local/` → `302`

### Vault UI (dev)
- URL: `http://127.0.0.1:8200/ui/` (host-bound in `v2/infra/compose/docker-compose.v2.yml`)
- Verified:
  - `curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8200/ui/` → `200`

## Notes
- Port `:443` is mapped by Traefik, but no `websecure` routers are configured in `v2/infra/compose/traefik/configs/traefik.v2.yml`; `https://app.local/` and `https://router.local/` currently return `404` (verified).
