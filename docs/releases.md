# Releases

Releases coordinate multi-sprint delivery by planning sprint “slots”, assigning features, tracking gates, and producing status/progress artifacts.

Releases are project-scope only.

## Where release files live

- `.project-handbook/releases/<version>/`
- `.project-handbook/releases/current` (symlink/pointer)
- `.project-handbook/releases/current.txt` (tooling-friendly pointer)

## Draft a release (no files written)

`ph release draft` suggests a release composition from local handbook artifacts.

```bash
ph release draft --version next --sprints 3 --base latest-delivered --format text
```

Machine output:

```bash
ph release draft --format json
ph release draft --schema
```

## Plan a release (writes files)

Create a release plan scaffold:

```bash
ph release plan --version next --sprints 3
```

Optionally activate it as current:

```bash
ph release plan --version next --sprints 3 --activate
```

## Activate / clear

```bash
ph release activate --release v1.2.0
ph release clear
```

## Assign features to slots

```bash
ph release add-feature --release v1.2.0 --feature foo --slot 1 --commitment committed --intent deliver
```

## Status and progress

```bash
ph release status --release current
ph release show --release current
ph release progress --release current
ph release list
```

## Close a release (with preflight)

```bash
ph release close --version v1.2.0
```

`ph release close` runs a preflight and blocks close when:

- the release timeline isn’t complete (unfinished slots/sprints), or
- any `release_gate: true` tasks are not done

When closing the current release, it also clears the current release pointer.

## Slot format migration

If a repo has a legacy slot format, migrate it:

```bash
ph release migrate-slot-format --release v1.2.0 --diff
ph release migrate-slot-format --release v1.2.0 --write-back
```

