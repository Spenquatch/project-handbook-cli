---
title: Quality Gate Session
type: session-template
date: 2025-09-24
tags: [quality, testing, validation]
links: []
---

# Quality Gate Session Template

## Objectives
- Confirm validation passes (`ph validate`).
- Ensure regression tests, smoke tests, and manual QA steps are complete.
- Capture outstanding risks, mitigations, and owners.
- No waivers or “we think it’s fine” judgments: when uncertainty exists, stop and create a `task_type=research-discovery` task + DR entry for operator/user approval.

## Guardrails
- **Session routing rule.** If you are working from a sprint task directory, check `task.yaml task_type:`. Session template is derived from `task_type`. If the derived session does not match this template, stop and restart using `ph onboarding session <derived-session>` (or run `ph task show --id TASK-XXX` to see the derived session).
- **Reject ambiguity.** Do not sign off when acceptance/evidence is missing or unclear; unresolved choices must become `task_type=research-discovery` tasks with a `DR-XXXX` and operator/user approval.

## Agenda
1. **Context Review**
   - Current sprint/feature scope
   - Outstanding blockers or waivers
2. **Automation Checklist**
   - `ph validate`
   - `ph status` (review `status/current_summary.md`)
   - Environment-specific tests
3. **Manual Verification**
   - Functional test notes
   - UX/Accessibility checks
4. **Sign-off / Next Steps**
   - Who signs off?
   - Follow-up tasks / bugs

## Notes Template
```
### Environment
- Branch / commit:
- Deployment target:

### Automated Results
- Validation:
- Tests:

### Manual Findings
- [ ] Item 1
- [ ] Item 2

### Risks / Waivers
- Risk:
- Mitigation:

### Decision
- ✅ / ⛔
```
