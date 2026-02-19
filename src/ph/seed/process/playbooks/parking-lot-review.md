---
title: Playbook - Parking Lot Review
type: process
date: {date}
tags: [process, playbook, parking-lot, review]
links:
  - ./roadmap-planning.md
---

# Playbook - Parking Lot Review

## Purpose
Review ideas and future work, then promote the right items to the roadmap (now/next/later).

## Commands
```bash
ph parking review
ph parking review --format json
ph parking list --category features
ph parking list --category research
ph parking list --category technical-debt
ph parking list --category external-requests

ph parking promote --item FEAT-... --target now
ph parking promote --item FEAT-... --target next
ph parking promote --item FEAT-... --target later
```

## Review flow
1. Run `ph parking review` to generate a non-interactive report of high-signal items.
2. For each item, decide:
   - promote to roadmap now/next/later, or
   - leave it in parking lot (needs refinement / not aligned yet).
3. After promotions, validate the roadmap:
```bash
ph roadmap validate
```
