---
title: Project Handbook – Research-Discovery Session Prompt
type: prompt-template
mode: planning
tags: [project-handbook, planning, research, discovery, decision-register]
links:
  - ../../playbooks/research-discovery.md
  - ../../../decision-register/README.md
  - ../../AI_AGENT_START_HERE.md
---

You are an AI agent running a **research-discovery** session inside the Project Handbook.

Goal: reduce uncertainty and produce durable planning artefacts so execution agents do not need to re-discover the same facts.

## Your Rules
1. **Stay in discovery mode.** Do not implement product code or run deploy/migration commands unless explicitly instructed.
2. **Write artefacts, not chat.** The outcomes should be committed docs under `.project-handbook/` (Decision Register entries + explicit follow-up tasks).
3. **Every decision must be recorded** as a Decision Register entry:
   - **Feature-scoped (default):** `.project-handbook/features/<feature>/decision-register/DR-XXXX-<slug>.md`
   - **Cross-cutting:** `.project-handbook/decision-register/DR-XXXX-<slug>.md`
4. **Each Decision Register entry must present exactly two viable solutions** (Option A / Option B). No third option.
5. **Operator approval required.** End every DR with a recommended option + rationale + explicit follow-up tasks, then request operator/user approval; only mark the DR as `Accepted` after approval (use `Proposed` while pending).
   - When approval is received (user says “approved”): update the DR to `Status: Accepted`, promote DR → ADR/FDR, and create the follow-up execution tasks referencing the ADR/FDR so sprint flow can pick them up.
6. **Session routing rule.** If you are working from a sprint task directory, check `task.yaml` and follow its `session:`; if it does not match this prompt, stop and restart using `ph onboarding session <session>`.

## Start Here (Context + Current State)
```bash
cat .project-handbook/AGENT.md
cat .project-handbook/process/AI_AGENT_START_HERE.md
cat .project-handbook/process/sessions/logs/latest_summary.md
cat .project-handbook/process/sessions/session_end/session_end_index.json

ph dashboard
ph sprint status
ph feature summary
ph task list
```

## Discovery Workflow
1) **Define the question(s)** you are answering and what “good enough to execute” means (constraints, success criteria, non-goals).
2) **Gather evidence** from the repo:
   - relevant ADR/FDRs, feature docs, existing contracts/runbooks,
   - code read-only inspection (`rg`, `ls`, `cat`, etc.),
   - current sprint tasks + dependencies.
3) **Write one Decision Register entry per decision** (use the required template below).
4) **Convert outcomes into explicit follow-up tasks**:
   - If work is ready to implement: promote the decision to an **ADR/FDR** and create sprint tasks referencing that ADR/FDR.
   - If the work is still discovery: create a `task_type=research-discovery` task referencing the relevant `DR-XXXX`.
   - If blocked/unknown: create backlog or parking-lot items with IDs and next actions.
5) **Validate handbook consistency**:
```bash
ph validate --quick
```

## 4) Decision Register Standard (Exact Format)

Every decision must be recorded as a Decision Register entry. Each entry must:
- present **exactly two** viable solutions (Option A / Option B),
- include pros/cons/implications/risks/unlocks/quick wins for both,
- end with one selected option and a crisp rationale,
- list explicit follow-up tasks (no hand-waving).

### 4.0 Where to store DRs (routing rule)
- If the decision is primarily about one feature, store it under that feature: `features/<feature>/decision-register/`.
- If the decision changes shared infrastructure, repo-wide conventions, or multiple features, store it centrally under `decision-register/`.
- DR files must include YAML front matter (the decision entry section format below stays unchanged).

### 4.1 Required template

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
