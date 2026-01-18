---
title: Standardize task directory slugs (avoid ':' and parentheses)
type: technical-debt
status: parking-lot
created: 2026-01-02
owner: @spenser
tags: ["process", "tooling", "portability"]
---

# Standardize task directory slugs (avoid ':' and parentheses)

Current sprint task folder names can include special characters (e.g. ':' and parentheses), which forces shell quoting and may break tooling/automation. Update task slug generation (task-create + links) to produce safe, portable directory names and optionally migrate existing tasks with redirects/updated links.

## Context

Task directory names are derived from the task title. Previously this allowed punctuation like `:` and `()` which:
- forces shell quoting,
- breaks some tooling assumptions,
- and can make links/paths less portable across environments.

## Potential Value

- Portable task directories across shells and filesystems.
- More reliable automation (less path escaping/quoting).
- Cleaner, more predictable task URLs/paths.

## Considerations

- Slug normalization should be applied at creation time (no mass migration required).
- Existing “bad slug” directories may remain, but new tasks should be safe by default.

## Resolution (2026-01-04)
- Implemented `slugify()` for task directory names in the `ph` CLI task scaffolder.
- Added optional `lane` support to task creation (`ph task create ... --lane ...`) and lane-aware listing.
