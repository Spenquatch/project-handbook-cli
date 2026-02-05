from __future__ import annotations

import json

from .backlog_manager import BacklogManager
from .context import Context


def run_backlog_add(
    *,
    ctx: Context,
    issue_type: str,
    title: str,
    severity: str,
    desc: str,
    owner: str,
    impact: str,
    workaround: str,
    env: dict[str, str],
) -> int:
    legacy_issue_type = issue_type
    normalized_issue_type = (issue_type or "").strip().lower()
    if normalized_issue_type == "bugs":
        legacy_issue_type = "bug"
    elif normalized_issue_type == "wildcards":
        legacy_issue_type = "wildcard"

    if ctx.scope == "project":
        package_json_path = ctx.ph_root / "package.json"
        package_name = "project-handbook"
        package_version = "0.0.0"
        if package_json_path.exists():
            try:
                package_data = json.loads(package_json_path.read_text(encoding="utf-8"))
                package_name = str(package_data.get("name") or package_name)
                package_version = str(package_data.get("version") or package_version)
            except Exception:
                pass

        print()
        print(f"> {package_name}@{package_version} make {ctx.ph_root}")
        print(
            "> make -- backlog-add "
            f"type\\={legacy_issue_type} "
            f"'title={title}' "
            f"severity\\={severity} "
            f"'desc={desc}'"
        )
        print()

    manager = BacklogManager(project_root=ctx.ph_data_root, env=env)
    issue_id = manager.add_issue(
        issue_type=legacy_issue_type,
        title=title,
        severity=severity,
        desc=desc,
        owner=owner,
        impact=impact,
        workaround=workaround,
    )
    if issue_id is None:
        return 1

    if ctx.scope == "project":
        print("Backlog entry created.")
        print("  - Run 'make backlog-triage issue=<ID>' for P0 analysis")
        print("  - Assign it into a sprint via 'make backlog-assign issue=<ID> sprint=current'")
        print("  - Re-run 'make validate-quick' if files were edited manually")

    return 0


def run_backlog_list(
    *,
    ctx: Context,
    severity: str | None,
    category: str | None,
    format: str,
    env: dict[str, str],
) -> int:
    manager = BacklogManager(project_root=ctx.ph_data_root, env=env)
    manager.list_issues(severity=severity, category=category, format=format)
    return 0


def run_backlog_triage(*, ctx: Context, issue_id: str, env: dict[str, str], print_index_summary: bool) -> int:
    manager = BacklogManager(project_root=ctx.ph_data_root, env=env)
    ok = manager.triage_issue(issue_id, print_index_summary=print_index_summary)
    return 0 if ok else 1


def run_backlog_assign(*, ctx: Context, issue_id: str, sprint: str, env: dict[str, str]) -> int:
    manager = BacklogManager(project_root=ctx.ph_data_root, env=env)
    ok = manager.assign_to_sprint(issue_id, sprint=sprint, scope=ctx.scope)
    return 0 if ok else 1


def run_backlog_rubric(*, ctx: Context, env: dict[str, str]) -> int:
    manager = BacklogManager(project_root=ctx.ph_data_root, env=env)
    manager.show_rubric()
    return 0


def run_backlog_stats(*, ctx: Context, env: dict[str, str]) -> int:
    manager = BacklogManager(project_root=ctx.ph_data_root, env=env)
    manager.show_stats(ph_root=ctx.ph_root)
    return 0
