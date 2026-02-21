# Sprints

Sprints are a bounded execution window that groups tasks, telemetry, and a sprint plan.

## Where sprint files live

- `.project-handbook/sprints/<year>/<SPRINT-ID>/`
- `.project-handbook/sprints/current` (symlink/pointer to the active sprint directory)

## Sprint IDs

Most commands accept either:

- an explicit sprint id (for example `SPRINT-2026-01-11`), or
- `current` (by reading the `sprints/current` pointer)

## Planning a sprint

Create (or regenerate) a sprint plan template and set `sprints/current`:

```bash
ph sprint plan
```

If you need to regenerate an existing plan template:

```bash
ph sprint plan --force
```

Notes:

- `ph sprint plan` creates `plan.md` and a `tasks/` directory.
- When it writes/regenerates the plan, it also scaffolds a required sprint gate task (`task_type: sprint-gate`).

## Opening an existing sprint

```bash
ph sprint open --sprint SPRINT-2026-01-11
```

This updates `sprints/current` to point at an existing sprint directory.

## Day-to-day commands

```bash
ph sprint status
ph sprint tasks
ph sprint burndown
ph sprint capacity
```

## Closing a sprint

```bash
ph sprint close
```

`ph sprint close` prints a deterministic checklist and archives the sprint.
When closing the sprint completes the last planned release slot/timeline item, it may print a hint to run:

- `ph release close --version vX.Y.Z`

## Archiving

Manual archive (rerun only):

```bash
ph sprint archive --sprint SPRINT-2026-01-11
```
