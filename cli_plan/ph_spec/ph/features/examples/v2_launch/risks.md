---
title: v2 Launch Readiness Risks
type: risks
feature: v2_launch
date: 2026-01-07
tags: [risks]
links:
  - ../../adr/0028-v2-launch.md
---

# Risk Register: v2 Launch Readiness

## High Priority Risks
- **False green launch gates**  
  - Impact: High  
  - Probability: Low  
  - Mitigation: ensure gates validate real behavior (E2E, composition checks, codegen) not just service liveness.
- **Gates require manual secret steps**  
  - Impact: High  
  - Probability: Medium  
  - Mitigation: enforce deterministic bootstrap and forbid gates that require manual secret editing.
- **Evidence artifacts accidentally capture secrets**  
  - Impact: High  
  - Probability: Low  
  - Mitigation: follow evidence rules (`TASK-008`) and ensure gates redact/suppress sensitive values; treat this as a hard failure in `TASK-007`.

## Medium Priority Risks
- **Gates are slow and discourage local execution**  
  - Impact: Medium  
  - Probability: Medium  
  - Mitigation: keep a `validate-quick` path and run full gates in CI and pre-release.

## Risk Mitigation Strategies
- Prefer a small number of high-signal gates and keep them deterministic.
- Enforce a single runner entrypoint (`TASK-006`) and store evidence artifacts under `project-handbook/status/evidence/` for every failure mode.
