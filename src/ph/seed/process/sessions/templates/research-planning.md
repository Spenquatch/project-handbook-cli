---
title: Research Planning Session
type: prompt-template
mode: planning
tags: [research, planning]
---

You are planning a research effort for a feature or problem area.

Purpose:
- Produce a crisp research plan and the artifacts needed to turn outcomes into execution tasks.

Hard rules:
1) Do NOT implement code in this session.
2) Eliminate ambiguity: explicit deliverables, explicit timeboxes, explicit validation/evidence.
3) Keep terminology clean:
   - `task_type` is taxonomy (what kind of work)
   - `session` is the onboarding template key (how we run the work)

Mapping table (`task_type` → required/allowed `session`):
| `task_type` | `session` |
|---|---|
| `implementation` | `task-execution` |
| `research-discovery` | `research-discovery` |
| `feature-research-planning` | `research-planning` |

Checklist:
- Define the problem statement and success criteria.
- List research questions (what must be answered to de-risk execution).
- Define deliverables (Decision Register/ADR, updated contract/spec, and a list of execution tasks to create).
- Timebox the work and specify evidence locations under `status/evidence/...` when applicable.
