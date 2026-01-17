---
title: Decision Register
type: process
date: 2026-01-08
tags: [decisions, decision-register]
links:
  - ../process/sessions/templates/research-discovery.md
  - ../adr/
  - ../features/
---

# Decision Register

This folder is the **cross-cutting** Decision Register (DR) index and storage for decisions that span multiple features or change shared infrastructure/conventions.

Feature-scoped DRs should live alongside the owning feature so execution work stays local and self-contained.

## Where DR entries live (routing rule)
- **Feature-scoped (default):** `project-handbook/features/<feature>/decision-register/DR-XXXX-<slug>.md`
- **Cross-cutting:** `project-handbook/decision-register/DR-XXXX-<slug>.md`

## Numbering
- Use a four-digit sequence (`DR-0001`, `DR-0002`, …).
- Pick the next available ID by scanning the relevant decision-register folder; do not reuse IDs.

## Relationship to ADR/FDR
- DR entries capture the tradeoff analysis (exactly two viable options).
- When a decision becomes durable architecture, follow-up tasks should typically promote it to:
  - **FDR** (feature-local) for feature-scoped decisions, or
  - **ADR** (global) for cross-cutting decisions.
  Link the resulting ADR/FDR in **Related docs** and keep the DR as the tradeoff record.

## How DRs are created (via tasks)
- DR entries are created and completed during `session=research-discovery` tasks.
- Sprint planning may reserve a `DR-XXXX` ID (to create an execution-ready research task), but the DR content must be completed in the research session and must not be marked `Accepted` without operator/user approval.
- After approval, promote the accepted decision into an **FDR** (feature-local) or **ADR** (cross-cutting) and create execution tasks that reference the ADR/FDR (not the DR).

## Required template (copy/paste)

Note: all Markdown under `project-handbook/` requires front matter. Keep the decision entry body in the **exact format** below, but add YAML front matter above it in the file.

Example file wrapper (do not change the decision entry format):
```md
---
title: DR-XXXX — <Decision Title>
type: decision-register
date: <YYYY-MM-DD>
tags: [decision-register]
links: []
---

# Decision Register Entry

<paste the exact entry format below>
```

```md
### DR-XXXX — <Decision Title>

**Decision owner(s):** <role/team>  
**Date:** <YYYY-MM-DD>  
**Status:** Proposed | Accepted | Superseded  
**Related docs:** <links>

**Problem / Context**
- <what is being decided and why now?>

**Option A — <name>**
- **Pros:** …
- **Cons:** …
- **Cascading implications:** …
- **Risks:** …
- **Unlocks:** …
- **Quick wins / low-hanging fruit:** …

**Option B — <name>**
- **Pros:** …
- **Cons:** …
- **Cascading implications:** …
- **Risks:** …
- **Unlocks:** …
- **Quick wins / low-hanging fruit:** …

**Recommendation**
- **Recommended:** Option <A|B> — <name>
- **Rationale:** <why this tradeoff wins>

**Follow-up tasks (explicit)**
- <concrete tasks/spec edits/tests/scripts>
```
