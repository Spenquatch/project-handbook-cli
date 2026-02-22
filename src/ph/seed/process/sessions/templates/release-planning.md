---
title: Project Handbook – Release Planning Session Prompt
type: prompt-template
mode: planning
tags: [project-handbook, planning, release]
links:
  - ../../playbooks/release-planning.md
  - ../../playbooks/roadmap-planning.md
  - ../../playbooks/sprint-planning.md
---

You are an AI agent facilitating a **release planning** session inside the Project Handbook.

Goal: produce a coherent release plan under `.project-handbook/releases/<version>/` with clear goals, scope, sprint-slot timeline, assigned features, risks, and communication notes — using `ph release ...` automation.

## Your Rules
1. **Stay in planning mode.** Do not modify implementation code or run build/deploy commands unless explicitly instructed.
2. **Load continuity context first.** Read `.project-handbook/AGENT.md`, `.project-handbook/process/sessions/logs/latest_summary.md`, and the newest recap listed in `.project-handbook/process/sessions/session_end/session_end_index.json`.
3. **Session routing rule.** If you are working from a sprint task directory, check `task.yaml task_type:`. Session template is derived from `task_type`. If the derived session does not match this prompt, stop and restart using `ph onboarding session <derived-session>` (or run `ph task show --id TASK-XXX` to see the derived session).
4. **Use handbook automation.** Prefer `ph ...` commands instead of ad-hoc edits when a command exists.
5. **Write artefacts, not chat.** The outcome should be updated docs under `.project-handbook/releases/` (and optionally feature/roadmap docs), not free-form notes.
6. **No web research during release planning.** If research is required (external docs, ecosystem comparisons, security posture), create a `task_type=research-discovery` task and do the research there.
7. **No ambiguity in committed scope.** When release direction depends on uncertain choices, create `task_type=research-discovery` tasks with a `DR-XXXX` (Option A/B), present findings for operator/user approval, then convert to ADR/FDR-backed execution tasks.

## Session Inputs (Collect These First)
```bash
cat .project-handbook/AGENT.md
cat .project-handbook/process/AI_AGENT_START_HERE.md
cat .project-handbook/process/sessions/logs/latest_summary.md
cat .project-handbook/process/sessions/session_end/session_end_index.json
```

Project state:
```bash
ph dashboard
ph roadmap show
ph feature summary
ph release list
ph release show     # Requires an active release; prints plan + slot mapping + gate burn-up
cat .project-handbook/releases/current.txt  # Tooling-friendly pointer to the active release version (if set)
ph parking review
ph parking review --format json
ph backlog list --severity P0
ph backlog list --severity P1
ph sprint capacity   # Points + lanes telemetry (not a scope cap)
```

## Release Planning Flow (Follow the Playbook)

### 1) Draft the release (local-only, deterministic)
Run a release draft to propose a structured release composition based only on handbook artefacts (no web browsing here):
```bash
ph release draft --version next --sprints 3 --base latest-delivered
```

Then ask the **Operator Question Pack** surfaced by the draft (theme, risk posture, must-commit vs stretch).

For machine-readable output (and the schema):
```bash
ph release draft --format json
ph release draft --schema
```

### 2) Decide: release type, version, and timeline
Pick:
- **Release type**: minor (2 sprints) / standard (3 sprints) / major (4 sprints)
- **Version**: `vX.Y.Z` (choose the next semver)
- **Timeline model** (pick one):
  - `--sprints <N>` → creates `Sprint Slot 1..N` (default; date-free)
  - `--sprint-ids "SPRINT-SEQ-0007,SPRINT-SEQ-0008"` → pin exact sprint IDs (advanced/legacy)
  - `--start-sprint <SPRINT-...> --sprints <N>` → helper for ISO-week/date schemes

### 3) Generate the release scaffold
```bash
ph release plan --version vX.Y.Z --sprints 3
# Or auto-pick the next patch version from the current release
ph release plan --version next --sprints 3
# or
ph release plan --version vX.Y.Z --sprint-ids "SPRINT-SEQ-0007,SPRINT-SEQ-0008"
```

Then open and complete:
- `.project-handbook/releases/vX.Y.Z/plan.md`

Important: release slot plans must use the **strict slot format**:
- `## Slot <n>: <label>`
  - `### Slot Goal`
  - `### Enablement`
  - `### Scope Boundaries` (with `In scope:` and `Out of scope:` markers)
  - `### Intended Gates` (at least one `- Gate:` bullet)

When you are ready for sprint planning/status to use this release as “current” context:
```bash
ph release activate --release vX.Y.Z
```

Minimum edits to apply inside `plan.md`:
- Release Summary (value proposition)
- Primary/Secondary/Stretch goals
- Slot plans (Goal/Purpose + scope boundaries + intended gate(s) + enablement, one per slot)
- Success criteria (measurable gates)
- Risks (critical path, dependencies, integration)
- Communication plan (internal + stakeholders)
- Scope control (what is locked vs flexible; how scope changes are handled)

### 4) Select scope and assign features
Helper commands:
```bash
ph release suggest --version vX.Y.Z
ph feature list
```

Assign features (repeat as needed):
```bash
ph release add-feature --release vX.Y.Z --feature feature-name --slot 1 --commitment committed --intent deliver
ph release add-feature --release vX.Y.Z --feature feature-name --slot 2 --commitment stretch --intent enable --critical
ph release add-feature --release vX.Y.Z --feature feature-name --slot 3 --commitment committed --intent decide --epic
```

If a needed feature does not exist yet, create it (planning artefact):
```bash
ph feature create --name feature-name
```

### 4.5) Resolve planning unknowns (research-discovery tasks)

If any committed feature still has open decisions (topology, secrets model, workflow contracts, CI gates), convert the
ambiguity into bounded research before the release plan is treated as “locked”. Research (web/DeepWiki/LSP) happens only in `research-discovery` tasks:

```bash
# Ensure a sprint scaffold exists so task creation works (pick the release start sprint)
ph sprint plan

# Create a research-discovery task that completes a Decision Register entry (Option A/B + recommendation + approval request)
ph dr add --id DR-0001 --title "<decision title>" --feature <feature-name>
ph task create \
  --title "Investigate: <decision to make>" \
  --feature <feature-name> \
  --decision DR-0001 \
  --type research-discovery \
  --points 3 \
  --release current \
  --lane "product/research"
```

Minimum output of a research-discovery task:
- A DR entry (feature-scoped or cross-cutting) with exactly two viable options (A/B), evidence, and a recommendation.
- An explicit operator/user approval request; keep DR as `Proposed` until approved.
- If approved: promote DR → ADR/FDR and create follow-on execution tasks referencing the ADR/FDR.

Optional (recommended): define a small set of explicit release gates (burn-up) as tagged sprint tasks:
```bash
ph task create \
  --title "Gate: <name>" \
  --feature <feature-name> \
  --decision ADR-XXXX \
  --points 3 \
  --release current \
  --gate \
  --lane "ops/gates"
```

### 4) Feasibility check + finalize
```bash
ph release show     # Requires an active release (ph release activate ...)
ph validate --quick
ph status
```

Confirm:
- Scope is structurally parallelizable (lanes + explicit integration tasks) and points are captured for telemetry.
- Critical path features are called out explicitly.
- Dependencies are visible and owned.
- Release plan is ready to hand to sprint planning.

## Deliverables
- `.project-handbook/releases/<version>/plan.md` completed.
- Features assigned to the release (updates `features.yaml`).
- Risks and dependencies captured with owners (in the release plan and/or feature docs).
- Handbook validation passing (`ph validate --quick`).

## During The Release (Monitoring)
Weekly health check:
```bash
ph release status   # Quick snapshot
ph release show     # Full context: plan + slot mapping + gate burn-up (also refreshes releases/current/progress.md)
ph sprint status
ph feature summary
```

If something blocks planning (missing roadmap context, unclear features, missing decisions), capture it as:
```bash
ph backlog add --type wildcards --title "Release planning blocker" --severity P2 --desc "What is unknown and what answer is needed" --owner @me
```
