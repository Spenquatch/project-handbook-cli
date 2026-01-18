---
title: Process: fix session-end index paths
type: research
status: parking-lot
created: 2025-12-30
owner: @spenser
tags: []
---

# Process: fix session-end index paths

Legacy (v0) continuity files were stale: `process/sessions/session_end/session_end_index.json` pointed to recap markdown files that were not present. Decide whether continuity artifacts should be vendored or regenerated, and update docs so “latest recap” can be reliably loaded.

## Context

Legacy (v0) session continuity templates required:
- an index file to exist, and
- any referenced recap/prompt paths to exist on disk.

In this repo, the index file was missing, causing the “continuity checkpoint” step to fail for new planning sessions.

## Potential Value

- Makes session onboarding deterministic (agents can always load continuity context).
- Avoids “missing file” failures in planning session templates.
- Keeps validation strict when populated, while allowing empty bootstraps.

## Considerations

- Index validation existed in the legacy validator.
- The correct default is an empty index (records list), not a missing file.

## Resolution (2026-01-04)
- Added a default empty index file (records list) to unblock new sessions.
- Validation continues to enforce that any populated records reference existing repo-relative files.
