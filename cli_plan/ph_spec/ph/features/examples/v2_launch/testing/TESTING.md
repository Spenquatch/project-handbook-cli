---
title: v2 Launch Readiness Testing
type: testing
feature: v2_launch
date: 2026-01-07
tags: [testing]
links:
  - ../../adr/0028-v2-launch.md
---

# Testing: v2 Launch Readiness

## Test Strategy
- **Validation gates**: required `project-handbook` validation passes.
- **Infra**: required baseline services are healthy.
- **Schema**: publish + composition checks pass and Router serves composed supergraph.
- **UI**: Playwright E2E validates onboarding + landing harness gating driven by Context state.

## Test Cases
1) Run handbook validation and confirm 0 errors and 0 warnings.
2) Run v2 infra baseline health checks and confirm required services are `ok`.
3) Run v2 observability baseline health checks and confirm required services are `ok`.
4) Run schema publish + composition checks and confirm success.
5) Run codegen from registry and confirm UI typecheck passes.
6) Run Playwright E2E for login → onboarding → landing harness gating.

## Acceptance Criteria
- [ ] `ph validate` passes.
- [ ] v2 baseline services are healthy (Cosmo + MinIO required).
- [ ] v2 observability baseline services are healthy (Prometheus + Grafana + Loki + Alertmanager).
- [ ] Schema publishing + composition checks pass and Router serves the composed supergraph.
- [ ] Codegen runs from registry schemas and typecheck passes.
- [ ] Playwright E2E validates onboarding and Context-driven gating.
