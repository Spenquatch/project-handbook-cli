---
title: Implement: v2 schema harvester publish/check + mirrors + report hardening (Option A) - Validation Guide
type: validation
date: 2026-01-10
task_id: TASK-009
tags: [validation]
links: []
---

# Validation Guide: Implement: v2 schema harvester publish/check + mirrors + report hardening (Option A)

## Automated Validation
```bash
ph validate
ph sprint status
```

## Manual Validation (copy/paste; pass/fail)

### 0) Evidence directory (required)
```bash
EVID_ROOT="ph/status/evidence/TASK-009"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-harvester-publish-check"
EVID_DIR="$EVID_ROOT/$RUN_ID"
mkdir -p "$EVID_DIR"
${EDITOR:-vi} "$EVID_DIR/index.md"
```

### 1) Harvester publish/check gate (success path)
```bash
make -C v2 v2-publish | tee "$EVID_DIR/v2-publish.txt"
```
Pass if:
- command exits `0`
- output does not contain secret-looking strings (see “No leakage” below)

### 2) Mirrors only update after success (atomic; success path)
```bash
# Snapshot mirror file hashes before publish
find v2/infra/compose/graphql/subgraphs -maxdepth 2 -type f -name 'schema.graphql' -print0 | sort -z | xargs -0 shasum -a 256 >"$EVID_DIR/mirrors-before.sha256"

# Run publish (should update mirrors on success)
make -C v2 v2-publish >/dev/null

# Snapshot mirror file hashes after publish
find v2/infra/compose/graphql/subgraphs -maxdepth 2 -type f -name 'schema.graphql' -print0 | sort -z | xargs -0 shasum -a 256 >"$EVID_DIR/mirrors-after.sha256"

diff -u "$EVID_DIR/mirrors-before.sha256" "$EVID_DIR/mirrors-after.sha256" | tee "$EVID_DIR/mirrors-diff.txt" || true

# Assert no empty mirror files and no harvester temp files remain
find v2/infra/compose/graphql/subgraphs -maxdepth 2 -type f -name 'schema.graphql' -size 0 -print | tee "$EVID_DIR/mirrors-empty.txt"
find v2/infra/compose/graphql/subgraphs -maxdepth 2 -type f -name '*.tmp' -print | tee "$EVID_DIR/mirrors-tempfiles.txt"
```
Pass if:
- mirrors only change after a successful publish/check run
- no empty mirror files exist post-run (`mirrors-empty.txt` is empty)
- no stray temp files exist post-run (`mirrors-tempfiles.txt` is empty)

### 3) Publish report exists, is deterministic, and is sanitized
```bash
REPORT_FILE="v2/.tmp/harvester/publish-report.json"

ls -la v2/.tmp/harvester 2>/dev/null | tee "$EVID_DIR/harvester-tmp-ls.txt" || true
test -s "$REPORT_FILE"

shasum -a 256 "$REPORT_FILE" | tee "$EVID_DIR/publish-report.sha256"

# Determinism check: run again; the report hash must match (no timestamps / stable ordering)
make -C v2 v2-publish >/dev/null
shasum -a 256 "$REPORT_FILE" | tee "$EVID_DIR/publish-report.sha256.2"
diff -u "$EVID_DIR/publish-report.sha256" "$EVID_DIR/publish-report.sha256.2" | tee "$EVID_DIR/publish-report.sha256.diff.txt"

# Coarse leakage scan (stdout + report file)
rg -n "COSMO_API_KEY=|COSMO_API_TOKEN=|Bearer\\s+|Authorization:|eyJ[A-Za-z0-9_-]+\\.eyJ|sk-" \
  "$EVID_DIR/v2-publish.txt" "$REPORT_FILE" -S >"$EVID_DIR/token-scan-hits.txt" || true
wc -l "$EVID_DIR/token-scan-hits.txt" | tee "$EVID_DIR/token-scan-hits-count.txt"
```
Pass if:
- report JSON exists and is non-empty at `v2/.tmp/harvester/publish-report.json`
- report hash is stable across consecutive runs (`publish-report.sha256.diff.txt` shows no changes)
- `token-scan-hits-count.txt` reports `0` (no secret-like patterns found)

### 4) Hard gate behavior (negative test: no mirror updates on failure)
This task must prove: if publish/check fails, mirrors do not change.

Implementation requirement (for testability):
- `make -C v2 v2-publish` must allow overriding Cosmo auth for a negative test by setting `COSMO_API_KEY=invalid` in the host env (do not print it; just pass it through to the harvester container).

```bash
EVID_DIR_FAIL="$EVID_DIR/failure-invalid-cosmo-key"
mkdir -p "$EVID_DIR_FAIL"

find v2/infra/compose/graphql/subgraphs -maxdepth 2 -type f -name 'schema.graphql' -print0 | sort -z | xargs -0 shasum -a 256 >"$EVID_DIR_FAIL/mirrors-before.sha256"

# Expect failure; do not proceed on success.
if COSMO_API_KEY="invalid" make -C v2 v2-publish >"$EVID_DIR_FAIL/v2-publish-failure.txt" 2>&1; then
  echo "ERROR: expected v2-publish to fail with invalid COSMO_API_KEY" | tee "$EVID_DIR_FAIL/expected-failure.txt"
  exit 2
fi

find v2/infra/compose/graphql/subgraphs -maxdepth 2 -type f -name 'schema.graphql' -print0 | sort -z | xargs -0 shasum -a 256 >"$EVID_DIR_FAIL/mirrors-after.sha256"
diff -u "$EVID_DIR_FAIL/mirrors-before.sha256" "$EVID_DIR_FAIL/mirrors-after.sha256" | tee "$EVID_DIR_FAIL/mirrors-diff.txt" || true
```
Pass if:
- `v2-publish-failure.txt` shows a clear error and exits non-zero
- `mirrors-diff.txt` is empty (no mirror changes)

## Required evidence files (minimum)
- `ph/status/evidence/TASK-009/<run-id>/index.md`
- `ph/status/evidence/TASK-009/<run-id>/v2-publish.txt`
- `ph/status/evidence/TASK-009/<run-id>/mirrors-before.sha256`
- `ph/status/evidence/TASK-009/<run-id>/mirrors-after.sha256`
- `ph/status/evidence/TASK-009/<run-id>/mirrors-diff.txt`
- `ph/status/evidence/TASK-009/<run-id>/publish-report.sha256`
- `ph/status/evidence/TASK-009/<run-id>/token-scan-hits-count.txt`

## Sign-off
- [ ] All validation steps completed
- [ ] Evidence documented above
- [ ] Ready to mark task as "done"
