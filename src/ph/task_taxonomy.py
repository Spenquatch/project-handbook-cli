from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

ALLOWED_TASK_TYPES: set[str] = {
    "implementation",
    "research-discovery",
    "sprint-gate",
    "feature-research-planning",
    "task-docs-deep-dive",
}

TASK_TYPE_TO_SESSION: dict[str, str] = {
    "implementation": "task-execution",
    "research-discovery": "research-discovery",
    "sprint-gate": "sprint-gate",
    "feature-research-planning": "feature-research-planning",
    "task-docs-deep-dive": "task-docs-deep-dive",
}

# Backwards compatibility for legacy tasks that predate `task_type`.
# Some older tasks may only contain `session:`; we can map it back to a type.
SESSION_TO_LEGACY_TASK_TYPE: dict[str, str] = {v: k for k, v in TASK_TYPE_TO_SESSION.items()}


@dataclass(frozen=True)
class TaxonomyIssue:
    severity: str  # "error" | "warning"
    code: str
    message: str


def normalize_task_type(raw: Any) -> str | None:
    value = str(raw or "").strip().lower()
    return value or None


def normalize_session(raw: Any) -> str | None:
    value = str(raw or "").strip().lower()
    return value or None


def derive_session(*, task_type: str) -> str:
    normalized = normalize_task_type(task_type) or ""
    return TASK_TYPE_TO_SESSION.get(normalized, "")


def effective_task_type_and_session(
    task_meta: Mapping[str, Any],
) -> tuple[str | None, str | None, list[TaxonomyIssue]]:
    """
    Returns (effective_task_type, derived_session, issues).

    Rules:
    - `task_type` is canonical. If present, `session` is deprecated and ignored for behavior.
      - mismatch => error
      - match => warning (deprecated field)
    - If `task_type` is missing but `session` is present and mappable, treat as legacy and
      infer `task_type` (warning).
    """

    issues: list[TaxonomyIssue] = []
    raw_type = normalize_task_type(task_meta.get("task_type"))
    raw_session = normalize_session(task_meta.get("session"))

    if raw_type:
        if raw_type not in TASK_TYPE_TO_SESSION:
            issues.append(
                TaxonomyIssue(
                    severity="error",
                    code="task_type_invalid",
                    message=f"Invalid task_type: {raw_type!r}",
                )
            )
            return None, None, issues

        derived = TASK_TYPE_TO_SESSION[raw_type]
        if raw_session:
            if raw_session != derived:
                issues.append(
                    TaxonomyIssue(
                        severity="error",
                        code="task_type_session_mismatch",
                        message=(
                            "task_type and session are inconsistent "
                            f"(task_type={raw_type!r} requires session={derived!r}, found session={raw_session!r})"
                        ),
                    )
                )
            else:
                issues.append(
                    TaxonomyIssue(
                        severity="warning",
                        code="task_session_deprecated",
                        message="task.yaml contains deprecated key `session:`; remove it (derived from task_type).",
                    )
                )
        return raw_type, derived, issues

    if raw_session:
        inferred = SESSION_TO_LEGACY_TASK_TYPE.get(raw_session)
        if inferred:
            issues.append(
                TaxonomyIssue(
                    severity="warning",
                    code="task_type_missing_legacy_session",
                    message=(
                        "task.yaml missing task_type; inferred from legacy session. Add task_type and remove session."
                    ),
                )
            )
            return inferred, raw_session, issues

        issues.append(
            TaxonomyIssue(
                severity="error",
                code="session_invalid",
                message=f"Unknown session: {raw_session!r}",
            )
        )
        return None, raw_session, issues

    issues.append(
        TaxonomyIssue(
            severity="error",
            code="task_type_missing",
            message="Missing required task_type in task.yaml.",
        )
    )
    return None, None, issues
