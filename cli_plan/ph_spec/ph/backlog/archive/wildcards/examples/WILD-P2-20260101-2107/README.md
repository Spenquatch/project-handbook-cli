---
title: v2 Vault bootstrap: deterministic AnythingLLM API key seeding strategy
type: wildcards
severity: P2
status: closed
created: 2026-01-01
owner: @spenser
archived_at: 2026-01-04T13:18:11Z
archived_by_task: manual
archived_by_sprint: manual
---

# 🟡 [P2] v2 Vault bootstrap: deterministic AnythingLLM API key seeding strategy

**Severity:** P2 - Medium  
**Action Required:** Queued in backlog

## Description

vault-secrets.md requires ANYLLM_API_KEY for AnythingLLM REST and wrapper. Decide the local/dev strategy: (a) seed from operator-provided env at bootstrap time, (b) derive by calling AnythingLLM admin endpoint during bootstrap, or (c) document a manual step. Ensure the choice does not require leaking the key to the browser and is compatible with make v2-up/v2-smoke.

## Impact

- Blocks AnythingLLM wrapper federation work because the wrapper cannot authenticate to AnythingLLM REST.
- Increases onboarding friction: developers must manually create keys inside the container unless a deterministic bootstrap exists.

## Workaround

- Manually mint an API key inside the AnythingLLM container and paste it into Vault KV at `kv/data/tribuence/v2/anythingllm` as `ANYLLM_API_KEY`.

## Root Cause Analysis

AnythingLLM API keys are minted/managed inside the service and are not trivially derivable from static config; the bootstrap workflow must either mint the key via the running container or accept an operator-provided key.

## Solution Options

### Option 1: Quick Fix
- Require an operator-provided `ANYLLM_API_KEY` at bootstrap time (env var), and fail fast with clear instructions when missing.

### Option 2: Proper Fix
- Adopt the proven local/dev approach from the prior system:
  - execute inside the running AnythingLLM container and call its API key minting logic to generate a new API key secret
  - write the generated secret into Vault KV (`kv/data/tribuence/v2/anythingllm`, key `ANYLLM_API_KEY`)

Reference (read-only source):
- `modular-oss-saas/scripts/vault/bootstrap-mini.sh` (`generate_anythingllm_api_key`)

Contract linkage:
- `project-handbook/contracts/tribuence-mini-v2/vault-bootstrap.md`
- `project-handbook/contracts/tribuence-mini-v2/vault-secrets.md`

## Investigation Notes

Findings (2026-01-02):
- The prior system mints an AnythingLLM API key by running a small Node script *inside* the container that calls `ApiKey.create()` and extracts the generated secret.
- This requires the AnythingLLM container to be running; therefore the v2 bootstrap workflow should be explicitly 2-phase (seed static keys first; mint service-derived keys after bring-up).

## Resolution (2026-01-02)
- Implemented via sprint task `project-handbook/sprints/archive/2026/SPRINT-2026-01-02/tasks/TASK-020-v2-anythingllm-api-key-bootstrap-strategy/`.
