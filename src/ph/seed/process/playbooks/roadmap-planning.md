---
title: Playbook - Roadmap Planning
type: process
date: {date}
tags: [process, playbook, roadmap, planning]
links:
  - ./parking-lot-review.md
  - ./release-planning.md
---

# Playbook - Roadmap Planning

## Purpose
Maintain a Now/Next/Later roadmap that aligns releases and sprint work to long-term direction.

## Commands
```bash
ph roadmap show
ph roadmap create
ph roadmap validate
ph parking review
ph parking promote --item FEAT-... --target next
```

## Roadmap planning flow
1. Review current roadmap:
   - `ph roadmap show`
2. Review parking lot candidates:
   - `ph parking review`
3. Promote items that are ready:
   - `ph parking promote --item ... --target now|next|later`
4. Edit `.project-handbook/roadmap/now-next-later.md` to ensure:
   - clear themes per section,
   - links to feature docs where applicable,
   - explicit scope boundaries (what is not included).
5. Validate links:
   - `ph roadmap validate`
