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
    "task": (
        "Task workflow commands\n"
        "  make task-create title='X' feature=foo decision=ADR-001 [points=5] [owner=@alice] "
        "[lane=handbook/automation] [release=current|vX.Y.Z] [gate=true]\n"
        "                        - Scaffold a new sprint task directory with docs/checklists\n"
        "  make task-list        - Show all tasks in the current sprint\n"
        "  make task-show id=TASK-### - Print task metadata + file locations\n"
        "  make task-status id=TASK-### status=doing [force=true]\n"
        "                        - Update status with dependency validation\n"
    ),
    "feature": """Feature management commands
  make feature-list             - List features with owner, stage, and links
  make feature-create name=foo [epic=true] [owner=@alice]
                                - Scaffold architecture/implementation/testing docs
  make feature-status name=foo stage=in_progress
  make feature-update-status    - Sync status.md files from sprint/task data
  make feature-summary          - Aggregate progress for reporting
  make feature-archive name=foo [force=true]
                                - Completeness check + move to features/implemented/
""",
    "release": (
        "Release coordination commands\n"
        "  make release-plan [version=v1.2.0|version=next] [bump=patch|minor|major] [sprints=3] "
        '[sprint_ids="SPRINT-...,SPRINT-..."] [activate=true]\n'
        "                                - Generate a release plan scaffold (optionally activate)\n"
        "  make release-activate release=v1.2.0\n"
        "                                - Set releases/current to an existing release\n"
        "  make release-clear             - Unset current release pointer\n"
        "  make release-status           - Summaries + health for current release\n"
        "  make release-show             - Print releases/current/plan.md + computed status "
        "(best for sprint planning/closing)\n"
        "  make release-progress         - Refresh releases/current/progress.md "
        "(auto-generated; no need to edit manually)\n"
        "  make release-add-feature release=v1.2.0 feature=auth [epic=true] [critical=true]\n"
        "  make release-suggest version=v1.2.0 - Recommend features based on status data\n"
        "  make release-list             - List every release folder + status\n"
        "  make release-close version=v1.2.0 - Close and document retro notes\n"
    ),
    "backlog": """Issue backlog + triage commands
  make backlog-add type=bug|wildcards|work-items title='X' severity=P1 desc='Y' [owner=@alice]
  make backlog-list [severity=P1] [category=ops] [format=table]
  make backlog-triage issue=BUG-001 - AI-assisted rubric + action items
  make backlog-assign issue=BUG-001 sprint=current
  make backlog-rubric            - Print P0-P4 criteria
  make backlog-stats             - Metrics grouped by severity/category
""",
    "parking": """Parking lot workflow commands
  make parking-add type=features title='Idea' desc='Y' [owner=@alice] [tags='foo,bar']
  make parking-list [category=labs] [format=table]
  make parking-review            - Guided quarterly review session
  make parking-promote item=FEAT-001 target=later
""",
    "validation": """Validation, status, and test commands
  make validate-quick            - Fast lint (runs automatically after every make)
  make validate                  - Full validation suite
  make pre-exec-lint             - Strict sprint task lint (session/purpose + ambiguity gate)
  make pre-exec-audit            - Full pre-exec audit (captures evidence + runs pre-exec-lint)
  make status                    - Regenerate status/current_summary.md
  make check-all                 - Convenience alias for validate + status
  make test-system               - Run validation + status + daily smoke checks
""",
    "utilities": """Utility + daily-use commands
  make daily / daily-force / daily-check - Manage daily status cadence
  make onboarding                 - Root onboarding guide
  make onboarding session <template> - Facilitated prompts (e.g., sprint-planning)
  make onboarding session continue-session - Show latest Codex + command history summary
  make end-session                - Generate session summary via headless Codex
  make dashboard                  - Quick sprint + validation snapshot
  make clean                      - Remove Python caches
  make install-hooks              - Install repo git hooks
  make test-system                - Automation smoke test suite
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
