# project-handbook-cli

`project-handbook-cli` is an installable Python CLI distribution that provides the `ph` command.

Key principles:

- `ph` operates on a **handbook instance repo** (your Project Handbook repo) as data/templates/plans.
- The handbook root is detected by the presence of `.ph/config.json`.
- `ph` MUST NOT execute repo-local Python scripts at runtime.

Next: read `Quick Start` for installation + first commands.
