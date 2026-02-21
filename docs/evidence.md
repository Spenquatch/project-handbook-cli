# Evidence

Evidence capture is a lightweight way to record command execution results (stdout/stderr, exit codes, timestamps) in a deterministic directory tree.

## Where evidence lives

- `.project-handbook/status/evidence/TASK-###/<RUN_ID>/`

## Create an evidence run directory

```bash
ph evidence new --task TASK-123 --name manual
```

This prints helpful environment-style outputs like `EVIDENCE_RUN_DIR=...` and seeds `index.md` in the run directory.

## Capture a command

```bash
ph evidence run --task TASK-123 --name ruff -- uv run ruff check .
```

Artifacts created per run:

- `index.md` (seeded if missing)
- `cmd.txt` (command line)
- `stdout.txt`
- `stderr.txt`
- `meta.json` (timestamps + exit code)

Notes:

- by default, `ph evidence run` does not stream output; it writes to files
- it refuses to overwrite an existing capture (use a new `--run-id` or delete existing files intentionally)
- do not capture secrets (tokens, API keys, `.env` dumps) into evidence
