---
title: Implement: v2 registry-backed codegen wiring (Cosmo fetch + drift gate + CI ordering) - Validation Guide
type: validation
date: 2026-01-10
task_id: TASK-010
tags: [validation]
links: []
---

# Validation Guide: Implement: v2 registry-backed codegen wiring (Cosmo fetch + drift gate + CI ordering)

## Automated Validation
```bash
ph validate
ph sprint status
```

## Manual Validation (copy/paste; pass/fail)

### 0) Evidence directory (required)
```bash
EVID_ROOT="ph/status/evidence/TASK-010"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-codegen-from-cosmo"
EVID_DIR="$EVID_ROOT/$RUN_ID"
mkdir -p "$EVID_DIR"
${EDITOR:-vi} "$EVID_DIR/index.md"
```

### 1) Codegen runs and fetches schema from Cosmo (success path)
```bash
make -C v2 v2-codegen | tee "$EVID_DIR/v2-codegen.txt"
```
Pass if:
- command exits `0`
- output shows a Cosmo fetch step occurred before codegen generation

### 2) Fetched schema file exists and is deterministic (no drift without changes)
```bash
FETCHED_SCHEMA_FILE="v2/.tmp/codegen/supergraph.graphql"
test -s "$FETCHED_SCHEMA_FILE"

shasum -a 256 "$FETCHED_SCHEMA_FILE" | tee "$EVID_DIR/supergraph.sha256"

# Immediately refetch; hash must match when no publish changes occurred.
make -C v2 v2-codegen >/dev/null
shasum -a 256 "$FETCHED_SCHEMA_FILE" | tee "$EVID_DIR/supergraph.sha256.2"
diff -u "$EVID_DIR/supergraph.sha256" "$EVID_DIR/supergraph.sha256.2" | tee "$EVID_DIR/supergraph.sha256.diff.txt"
```
Pass if:
- `v2/.tmp/codegen/supergraph.graphql` exists and is non-empty
- `supergraph.sha256.diff.txt` shows no changes (immediate re-fetch is stable)

### 3) Drift gate works (fails on uncommitted generated changes)
```bash
# Baseline: should pass when generated outputs are committed and up to date.
make -C v2 v2-codegen-check | tee "$EVID_DIR/v2-codegen-check.txt"

# Demonstrate failure once, then revert.
git -C v2 status --porcelain=v1 | tee "$EVID_DIR/v2-status-before-drift.txt"

DRIFT_FILE="v2/apps/tribuence-mini/src/generated/.drift-test"
mkdir -p "$(dirname "$DRIFT_FILE")"
printf "%s\n" "intentional drift for TASK-010 validation" >> "$DRIFT_FILE"

if make -C v2 v2-codegen-check >"$EVID_DIR/v2-codegen-check-expected-failure.txt" 2>&1; then
  echo "ERROR: expected v2-codegen-check to fail when repo is dirty" | tee "$EVID_DIR/expected-failure.txt"
  exit 2
fi

# Cleanup: `git checkout` does not remove untracked files, so explicitly remove the drift marker.
rm -f "$DRIFT_FILE"
git -C v2 checkout -- "apps/tribuence-mini/src/generated" || true
git -C v2 status --porcelain=v1 | tee "$EVID_DIR/v2-status-after-revert.txt"
```
Pass if:
- `v2-codegen-check.txt` exits `0` on a clean repo
- `v2-codegen-check-expected-failure.txt` exits non-zero with a clear “dirty diff” failure
- `v2-status-after-revert.txt` shows the repo is clean again (no uncommitted changes)

### 4) Ordering gate (publish/check → codegen → typecheck)
```bash
make -C v2 v2-publish | tee "$EVID_DIR/v2-publish.txt"
make -C v2 v2-codegen-check | tee "$EVID_DIR/v2-codegen-check-after-publish.txt"
pnpm -C v2/apps/tribuence-mini typecheck | tee "$EVID_DIR/typecheck.txt"
```
Pass if:
- pipeline succeeds in the above order and fails fast when `v2-publish` fails (do not proceed to codegen/typecheck on failure)

### 5) No secret leakage
```bash
rg -n "COSMO_API_KEY=|COSMO_API_TOKEN=|Bearer\\s+|Authorization:|eyJ[A-Za-z0-9_-]+\\.eyJ|sk-" \
  "$EVID_DIR" -S > "$EVID_DIR/token-scan-hits.txt" || true
wc -l "$EVID_DIR/token-scan-hits.txt" | tee "$EVID_DIR/token-scan-hits-count.txt"
```
Pass if:
- `token-scan-hits-count.txt` reports `0`

## Required evidence files (minimum)
- `ph/status/evidence/TASK-010/<run-id>/index.md`
- `ph/status/evidence/TASK-010/<run-id>/v2-codegen.txt`
- `ph/status/evidence/TASK-010/<run-id>/v2-codegen-check.txt`
- `ph/status/evidence/TASK-010/<run-id>/typecheck.txt`
- `ph/status/evidence/TASK-010/<run-id>/token-scan-hits-count.txt`

## Sign-off
- [ ] All validation steps completed
- [ ] Evidence documented above
- [ ] Ready to mark task as "done"

## Reviewer Decision (2026-01-11)
Decision: **APPROVE**

Reproduced:
- `ph validate`
- `make -C v2 v2-codegen`
- `make -C v2 v2-codegen-check` (clean pass + expected failure on injected drift)
- Ordering: `make -C v2 v2-publish` → `make -C v2 v2-codegen-check` → `pnpm -C v2/apps/tribuence-mini typecheck`
- Secret leakage scan per this doc (0 hits)

Evidence:
- `ph/status/evidence/TASK-010/20260111T085706Z-reviewer-rerun/`

Review fixes applied:
- Ensure drift test cleanup removes untracked drift marker.
- Add non-secret log lines so `v2-codegen` output shows a Cosmo fetch step occurred before generation.
