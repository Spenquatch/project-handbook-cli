from __future__ import annotations

DEFAULT_HELP = """Project Handbook quick help

Most-used flows:
  • Daily briefing          : ph daily generate | ph onboarding session continue-session
  • Sprint lifecycle        : ph sprint plan / ph sprint status / ph sprint close
  • Task execution          : ph task create / ph task status
  • Feature + release work  : ph feature create / ph release plan
  • Validation & status     : ph validate --quick | ph status

Need the full command list for a workflow?
  ph help sprint      # sprint planning & health
  ph help task        # sprint tasks
  ph help feature     # feature lifecycle
  ph help release     # release coordination
  ph help backlog     # issue backlog & triage
  ph help parking     # parking lot ideas
  ph help validation  # validation / status / test
  ph help utilities   # daily tools, onboarding, cleanup

Tip: most workflows print next-step guidance after they run.
"""


TOPICS: dict[str, str] = {
    "sprint": """Sprint workflow commands
  ph sprint plan      - Create a new sprint skeleton (auto-updates sprints/current; scaffolds a sprint gate)
  ph sprint open      - Switch sprints/current to an existing sprint
  ph sprint status    - Show day-of-sprint, health, and next suggested task
  ph sprint tasks     - List every task under the active sprint
  ph sprint burndown  - Generate an ASCII burndown chart and save to sprint dir
  ph sprint close     - Produce retrospective, archive sprint, summarize velocity
  ph sprint capacity  - Display sprint telemetry (points + lanes; not a scope cap)
  ph sprint archive   - Manually archive a specific sprint (reruns only)

Notes:
  - Sprint gate must exist from Day 0; it is expected to close last.
""",
    "task": (
        "Task workflow commands\n"
        "  ph task create --title 'X' --feature foo --decision ADR-001 [--points 5] [--owner @alice] "
        "[--lane handbook/automation] [--type implementation|research-discovery|feature-research-planning|"
        "task-docs-deep-dive|sprint-gate] [--session <template>] [--release current|vX.Y.Z] [--gate]\n"
        "                        - Scaffold a new sprint task directory with docs/checklists\n"
        "\n"
        "  Notes:\n"
        "    --type sets task taxonomy + recommended session template.\n"
        "      implementation           -> session task-execution\n"
        "      research-discovery       -> session research-discovery\n"
        "      feature-research-planning-> session feature-research-planning\n"
        "      task-docs-deep-dive      -> session task-docs-deep-dive\n"
        "      sprint-gate              -> session sprint-gate\n"
        "    If you pass both --type and --session, they must agree.\n"
        "  ph task list        - Show all tasks in the current sprint\n"
        "  ph task show --id TASK-### - Print task metadata + file locations\n"
        "  ph task status --id TASK-### --status doing [--force]\n"
        "                        - Update status with dependency validation\n"
    ),
    "feature": """Feature management commands
  ph feature list              - List features with owner, stage, and links
  ph feature create --name foo [--epic] [--owner @alice] [--stage in_progress]
                                - Scaffold architecture/implementation/testing docs
  ph feature status --name foo --stage in_progress
  ph feature update-status     - Sync status.md files from sprint/task data
  ph feature summary           - Aggregate progress for reporting
  ph feature archive --name foo [--force]
                                - Completeness check + move to features/implemented/
""",
    "release": (
        "Release coordination commands\n"
        "  ph release plan [--version v1.2.0|next] [--bump patch|minor|major] [--sprints 3] "
        '[--sprint-ids "SPRINT-...,SPRINT-..."] [--activate]\n'
        "                                - Generate a release plan scaffold (optionally activate)\n"
        "  ph release draft [--version v1.2.0|next] [--sprints 3] [--base latest-delivered|current|vX.Y.Z] "
        "[--format text|json]\n"
        "                                - Suggest a release composition from local handbook artefacts (no files)\n"
        "\n"
        "  JSON output (draft):\n"
        "    ph release draft --format json\n"
        "    ph release draft --schema\n"
        "    keys: type, schema_version, version, planned_sprints, base_release, excluded_base_features,\n"
        "          candidate_features, suggested_features, operator_questions, commands\n"
        "    example:\n"
        '      {"type":"release-draft","schema_version":1,"version":"v1.2.3","planned_sprints":3,"commands":{...}}\n'
        "  ph release activate --release v1.2.0\n"
        "                                - Set releases/current to an existing release\n"
        "  ph release clear              - Unset current release pointer\n"
        "  ph release status [--release current|vX.Y.Z]\n"
        "                                - Summaries + health for current (or specified) release\n"
        "  ph release show [--release current|vX.Y.Z]\n"
        "                                - Print releases/<release>/plan.md + computed status "
        "(best for sprint planning/closing)\n"
        "  ph release progress [--release current|vX.Y.Z]\n"
        "                                - Refresh releases/<release>/progress.md "
        "(auto-generated; no need to edit manually)\n"
        "  ph release add-feature --release v1.2.0 --feature auth --slot 1 --commitment committed --intent deliver "
        "[--priority P1] [--epic] [--critical]\n"
        "  ph release suggest --version v1.2.0 - Recommend features based on status data\n"
        "  ph release list               - List every release folder + status\n"
        "  ph release close --version v1.2.0 - Close and document retro notes\n"
        "  ph release migrate-slot-format --release v1.2.0 [--diff] [--write-back]\n"
    ),
    "backlog": """Issue backlog + triage commands
  ph backlog add --type bug|wildcards|work-items --title 'X' --severity P1 --desc 'Y' [--owner @alice]
  ph backlog list [--severity P1] [--category ops] [--format table]
  ph backlog triage --issue BUG-001 - AI-assisted rubric + action items
  ph backlog assign --issue BUG-001 [--sprint current]
  ph backlog rubric            - Print P0-P4 criteria
  ph backlog stats             - Metrics grouped by severity/category
""",
    "parking": """Parking lot workflow commands
  ph parking add --type features --title 'Idea' [--desc 'Y'] [--owner @alice] [--tags 'foo,bar']
  ph parking list [--category labs] [--format table]
  ph parking review [--format text|json] - Non-interactive review report (no prompts)
  ph parking promote --item FEAT-001 [--target later]
""",
    "validation": """Validation, status, and test commands
  ph validate --quick            - Fast lint (runs automatically after every command unless skipped)
  ph validate                    - Full validation suite
  ph pre-exec lint               - Strict sprint task lint (session/purpose + ambiguity gate)
  ph pre-exec audit              - Full pre-exec audit (captures evidence + runs pre-exec lint)
  ph status                      - Regenerate status/current_summary.md
  ph check-all                   - Convenience alias for validate + status
  ph test system                 - Run validation + status + daily smoke checks
""",
    "utilities": """Utility + daily-use commands
  ph daily generate / ph daily check - Manage daily status cadence
  ph onboarding                  - Root onboarding guide
  ph onboarding session <template> - Facilitated prompts (e.g., sprint-planning)
  ph onboarding session continue-session - Show latest Codex + command history summary
  ph end-session                 - Generate session summary via headless Codex
  ph dashboard                   - Quick sprint + validation snapshot
  ph process refresh             - Refresh seed templates/playbooks after upgrades
  ph question add|list|show|answer|close - Escape hatch for required operator answers
  ph clean                       - Remove Python caches
  ph hooks install               - Install repo git hooks
  ph test system                 - Automation smoke test suite
""",
    "roadmap": """Roadmap workflow commands
  ph roadmap show     - Show roadmap now/next/later
  ph roadmap create   - Create roadmap/now-next-later.md template
  ph roadmap validate - Validate roadmap links
""",
}


def get_help_text(topic: str | None) -> str | None:
    if topic is None:
        return DEFAULT_HELP
    return TOPICS.get(topic)
