---
title: Process: fix session-end index paths
type: research
status: archived
created: 2025-12-30
owner: @spenser
tags: []
archived_at: 2026-01-04T23:09:09Z
archived_by_task: manual
archived_by_sprint: manual
---

# Process: fix session-end index paths

Continuity files are stale: process/sessions/session_end/session_end_index.json points to recap markdown files that are not present. Decide whether this repo should vendor session_end artifacts or regenerate index, and update process docs so 'latest recap' can be reliably loaded.

## Context

Session continuity templates require:
- `process/sessions/session_end/session_end_index.json` to exist, and
- any referenced recap/prompt paths to exist on disk.

In this repo, the index file was missing, causing the “continuity checkpoint” step to fail for new planning sessions.

## Potential Value

- Makes session onboarding deterministic (agents can always load continuity context).
- Avoids “missing file” failures in planning session templates.
- Keeps validation strict when populated, while allowing empty bootstraps.

## Considerations

- Index validation is already implemented in `project-handbook/process/checks/validate_docs.py`.
- The correct default is an empty index (records list), not a missing file.

## Resolution (2026-01-04)
- Added default empty index at `project-handbook/process/sessions/session_end/session_end_index.json`.
- Validation continues to enforce that any populated records reference existing repo-relative files.
