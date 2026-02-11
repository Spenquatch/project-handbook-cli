---
title: Playbook - Research / Discovery
type: process
date: {date}
tags: [process, playbook, research, discovery, decision-register]
links:
  - ../sessions/templates/research-discovery.md
---

# Playbook - Research / Discovery

## Purpose
Reduce uncertainty by producing durable decision artifacts and deterministic follow-on work.

## Core rules
- Every discovery task produces or updates a Decision Register entry (`DR-XXXX`) with exactly two options (A/B) and a recommendation.
- After approval: promote DR → ADR/FDR and create execution tasks referencing ADR/FDR.

## Commands
```bash
# Create the DR first
ph dr add --id DR-0001 --title "<decision title>" --feature feature-name

# Create the discovery task
ph sprint plan
ph task create \
  --title "Discovery: <decision>" \
  --feature feature-name \
  --decision DR-0001 \
  --type research-discovery \
  --points 3 \
  --lane "product/research"

# After approval
ph adr add --id ADR-0001 --title "<decision title>" --dr DR-0001
# or
ph fdr add --feature feature-name --id FDR-0001 --title "<decision title>" --dr DR-0001
```

## Validate
```bash
ph validate --quick
```
