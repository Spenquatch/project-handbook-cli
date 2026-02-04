from __future__ import annotations

DEFAULT_HELP = """Project Handbook quick help

Most-used flows:
  • Daily briefing          : make daily | make onboarding session continue-session
  • Sprint lifecycle        : make sprint-plan / sprint-status / sprint-close
  • Task execution          : make task-create / task-status
  • Feature + release work  : make feature-create / release-plan
  • Validation & status     : make validate-quick | make status

Need the full command list for a workflow?
  make help sprint      # sprint planning & health
  make help task        # sprint tasks
  make help feature     # feature lifecycle
  make help release     # release coordination
  make help backlog     # issue backlog & triage
  make help parking     # parking lot ideas
  make help validation  # validation / status / test
  make help utilities   # daily tools, onboarding, cleanup

Tip: most workflows print next-step guidance after they run.
"""


TOPICS: dict[str, str] = {
    "sprint": """Sprint workflow commands
  make sprint-plan      - Create a new sprint skeleton (auto-updates sprints/current)
  make sprint-open      - Switch sprints/current to an existing sprint
  make sprint-status    - Show day-of-sprint, health, and next suggested task
  make sprint-tasks     - List every task under the active sprint
  make burndown         - Generate an ASCII burndown chart and save to sprint dir
  make sprint-close     - Produce retrospective, archive sprint, summarize velocity
  make sprint-capacity  - Display sprint telemetry (points + lanes; not a scope cap)
  make sprint-archive   - Manually archive a specific sprint (reruns only)
""",
    "task": """Task workflow commands
  ph task create --title 'X' --feature foo --decision ADR-001 [--points 5] [--owner @alice] [--lane handbook/automation]
                        - Scaffold a new sprint task directory with docs/checklists
  ph task list        - Show all tasks in the current sprint
  ph task show --id TASK-### - Print task metadata + file locations
  ph task status --id TASK-### --status doing [--force]
                        - Update status with dependency validation
""",
    "feature": """Feature management commands
  ph feature list             - List features with owner, stage, and links
  ph feature create --name foo [--epic] [--owner @alice]
                                - Scaffold architecture/implementation/testing docs
  ph feature status --name foo --stage in_progress
  ph feature update-status    - Sync status.md files from sprint/task data
  ph feature summary          - Aggregate progress for reporting
  ph feature archive --name foo [--force]
                                - Completeness check + move to features/implemented/
""",
    "release": (
        "Release coordination commands\n"
        "  ph release plan [--version v1.2.0|next] [--bump patch|minor|major] [--sprints 3] "
        '[--sprint-ids "SPRINT-...,SPRINT-..."]\n'
        "                                - Generate plan.md with selected sprints/features\n"
        "  ph release status           - Summaries + health for current release\n"
        "  ph release add-feature --release v1.2.0 --feature auth [--epic] [--critical]\n"
        "  ph release suggest --version v1.2.0 - Recommend features based on status data\n"
        "  ph release list             - List every release folder + status\n"
        "  ph release close --version v1.2.0 - Close and document retro notes\n"
    ),
    "backlog": """Issue backlog + triage commands
  ph backlog add --type bug|wildcards|work-items --title 'X' --severity P1 --desc 'Y' [--owner @alice]
  ph backlog list [--severity P1] [--category ops] [--format table]
  ph backlog triage --issue BUG-001 - AI-assisted rubric + action items
  ph backlog assign --issue BUG-001 --sprint current
  ph backlog rubric            - Print P0-P4 criteria
  ph backlog stats             - Metrics grouped by severity/category
""",
    "parking": """Parking lot workflow commands
  ph parking add --type features --title 'Idea' --desc 'Y' [--owner @alice] [--tags 'foo,bar']
  ph parking list [--category labs] [--format table]
  ph parking review            - Guided quarterly review session
  ph parking promote --item FEAT-001 --target later
""",
    "validation": """Validation, status, and test commands
  ph validate --quick            - Fast lint (runs automatically after every ph)
  ph validate                  - Full validation suite
  ph status                    - Regenerate status/current_summary.md
  ph check-all                 - Convenience alias for validate + status
  ph test system               - Run validation + status + daily smoke checks
""",
    "utilities": """Utility + daily-use commands
  ph daily generate / daily generate --force / daily check --verbose - Manage daily status cadence
  ph onboarding                 - Root onboarding guide
  ph onboarding session <template> - Facilitated prompts (e.g., sprint-planning)
  ph onboarding session continue-session - Show latest Codex + command history summary
  ph end-session                - Generate session summary via headless Codex
  ph dashboard                  - Quick sprint + validation snapshot
  ph --scope system <command>   - System scope commands under .project-handbook/system (roadmap/releases excluded)
  ph reset                      - Dry-run project reset (execute requires --confirm RESET --force true)
  ph reset-smoke                - Prove reset preserves system scope
  ph init                       - Initialize a new handbook instance repo (root marker)
  ph clean                      - Remove Python caches
  ph hooks install              - Install repo git hooks
  ph test system                - Automation smoke test suite
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
