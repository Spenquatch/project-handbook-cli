# Workflows

This page gives end-to-end usage patterns. For the full command surface, see `Commands` or run `ph --help`.

## Initialize a new handbook repo

```bash
ph init --root /absolute/path/to/handbook
ph --root /absolute/path/to/handbook doctor
ph --root /absolute/path/to/handbook onboarding
```

After `ph init`, most content lives under `.project-handbook/` inside your repo.

## Daily loop (snapshot + next actions)

```bash
ph dashboard
ph next
ph check-all
ph test system
ph daily generate
ph daily check --verbose
```

If you need a structured prompt, use:

```bash
ph onboarding session list
ph onboarding session sprint-planning
```

## Sprint lifecycle

Plan/open:

```bash
ph sprint plan
ph sprint status
ph sprint tasks
```

`ph sprint plan` scaffolds a required sprint gate task from Day 0 (expected to close last).

Gate before execution:

```bash
ph pre-exec lint
ph pre-exec audit
```

Track:

```bash
ph sprint burndown
ph sprint capacity
```

Close:

```bash
ph sprint close
```

`ph sprint close` prints a deterministic close checklist and may print a `ph release close --version ...` hint when closing a sprint completes the last planned release slot/timeline item.

## Tasks (taxonomy + gates)

Prefer `--type` so the CLI sets consistent task metadata + recommended sessions.

```bash
ph task create --title "Implement X" --feature foo --decision ADR-0001 --type implementation
ph task create --title "Discovery: Y" --feature foo --decision DR-0007 --type research-discovery
ph task create --title "Sprint Gate: ..." --feature foo --decision ADR-0001 --type sprint-gate
```

Release gates:

- `ph task create --gate` marks a task as a release gate (`release_gate: true`).

## Releases (draft → plan → execute → close)

Draft (local-only suggestion; no files written):

```bash
ph release draft --version next --sprints 3 --base latest-delivered --format text
```

Plan (writes a scaffold; optionally activate):

```bash
ph release plan --version next --sprints 3
ph release plan --version next --sprints 3 --activate
```

Assign features to slots:

```bash
ph release add-feature --release v1.2.0 --feature foo --slot 1 --commitment committed --intent deliver
```

Status/progress:

```bash
ph release status --release current
ph release show --release current
ph release progress --release current
```

Close:

```bash
ph release close --version v1.2.0
```

`ph release close` runs a preflight and blocks close when the release timeline isn’t complete (unfinished slots/sprints) or when any release gate tasks are not done.

## Decisions (DR → ADR/FDR)

Create a Decision Register entry first:

```bash
ph dr add --id DR-0001 --title "Decision needed: ..."
```

After direction is approved, formalize:

```bash
ph adr add --id ADR-0001 --title "..." --dr DR-0001 --status draft
ph fdr add --feature foo --id FDR-0001 --title "..." --dr DR-0001
```

## Evidence capture

Create an evidence folder:

```bash
ph evidence new --task TASK-123 --name manual
```

Capture a command (writes `stdout.txt`, `stderr.txt`, `meta.json`, etc.):

```bash
ph evidence run --task TASK-123 --name ruff -- uv run ruff check .
```

## “Question” escape hatch (operator input)

If you’re blocked outside of a workflow that is allowed to be interactive, record the operator question:

```bash
ph question add --title "Need approval for X" --severity blocking --q-scope sprint --sprint current --body "..."
ph question list
ph question answer --id Q-0001 --answer "Approved: ..." --by @you
```

## Upgrade workflow (refresh seeded templates/playbooks)

After upgrading `ph`, refresh seed-owned process assets:

```bash
ph process refresh --templates --playbooks
```
