---
title: v2 Launch Readiness Architecture
type: architecture
feature: v2_launch
date: 2026-01-07
tags: [architecture]
links:
  - ../../adr/0028-v2-launch.md
  - ../../features/v2_registry-cosmo-minio-required/overview.md
  - ../../features/v2_schema-publishing-and-composition/overview.md
  - ../../features/v2_codegen-from-registry/overview.md
  - ../../features/v2_ui-dev-harness-and-module-boundaries/overview.md
  - ../../features/v2_workspace-signup-onboarding/overview.md
---

# Architecture: v2 Launch Readiness

## Overview
v2 launch readiness is an explicit, automated set of gates that validate the platform baseline end-to-end:
infra baseline, schema lifecycle, codegen, authenticated UI harness, and workspace onboarding.

## Components
- **Infra baseline gates**: Cosmo + MinIO required and healthy.
- **Schema lifecycle gates**: publish + composition checks and Router supergraph validity.
- **Codegen gates**: types generated from registry and typecheck passes.
- **UI harness gates**: landing harness + Context-only gating.
- **Onboarding gates**: Keycloak login + workspace onboarding creates Context workspace and shows provisioning state.

## Data Flow
1) Bring up v2 stack and verify required services are healthy.
2) Publish schemas and confirm composition checks pass and Router serves the composed supergraph.
3) Run codegen from registry schemas and validate typecheck.
4) Run Playwright E2E through login → onboarding → landing harness and validate Context-driven gating.

## Dependencies
- All v2 baseline features listed in `v2_launch/overview.md`.
