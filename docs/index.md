# project-handbook-cli

`project-handbook` is an installable Python CLI distribution that provides the `ph` command.

Key principles:

- `ph` operates on a **handbook instance repo** (your Project Handbook repo) as data/templates/plans.
- The handbook root is detected by the presence of `.project-handbook/config.json` (created by `ph init`).
- `ph` MUST NOT execute repo-local Python scripts at runtime.
- Default scope is `--scope project`; `--scope system` routes data under `.project-handbook/system/**`.

Most handbook content lives under `.project-handbook/` (sprints, features, releases, status, process assets, etc.).

If you’re setting up a new repo, start with:

- `ph init`
- `ph doctor`
- `ph onboarding`

Next:

- `Quick Start` for installation + initialization
- `Concepts` for root/scope/layout/post-hooks
- `Workflows` for end-to-end usage patterns
