from __future__ import annotations

from .context import Context
from .question_manager import QuestionError, QuestionManager

_SYSTEM_SCOPE_REMEDIATION = "Questions are project-scope only. Use: ph --scope project question ..."


def run_question_add(
    *,
    ctx: Context,
    title: str,
    severity: str,
    scope: str,
    sprint: str | None,
    task_id: str | None,
    release: str | None,
    asked_by: str | None,
    owner: str | None,
    body: str,
    env: dict[str, str],
) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1
    manager = QuestionManager(ph_data_root=ctx.ph_data_root, env=env)
    try:
        qid = manager.add_question(
            title=title,
            severity=severity,
            scope=scope,
            sprint=sprint,
            task_id=task_id,
            release=release,
            asked_by=asked_by,
            owner=owner,
            body=body,
        )
    except QuestionError as exc:
        print(str(exc), end="")
        return 2
    print(f"✅ Created question: {qid}")
    print("Next:")
    print('- Answer: `ph question answer --id Q-0001 --answer "..." --by @user`')
    print("- Close : `ph question close --id Q-0001 --resolution answered|not-needed|superseded`")
    return 0


def run_question_list(*, ctx: Context, status: str, format: str, env: dict[str, str]) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1
    manager = QuestionManager(ph_data_root=ctx.ph_data_root, env=env)
    manager.list_questions(status=status, format=format)
    return 0


def run_question_show(*, ctx: Context, qid: str, env: dict[str, str]) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1
    manager = QuestionManager(ph_data_root=ctx.ph_data_root, env=env)
    try:
        manager.show_question(qid=qid)
    except QuestionError as exc:
        print(str(exc), end="")
        return 2
    return 0


def run_question_answer(*, ctx: Context, qid: str, answer: str, by: str | None, env: dict[str, str]) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1
    manager = QuestionManager(ph_data_root=ctx.ph_data_root, env=env)
    try:
        manager.answer_question(qid=qid, answer=answer, by=by)
    except QuestionError as exc:
        print(str(exc), end="")
        return 2
    print(f"✅ Answer recorded for {qid}")
    return 0


def run_question_close(*, ctx: Context, qid: str, resolution: str, env: dict[str, str]) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1
    manager = QuestionManager(ph_data_root=ctx.ph_data_root, env=env)
    try:
        manager.close_question(qid=qid, resolution=resolution)
    except QuestionError as exc:
        print(str(exc), end="")
        return 2
    print(f"✅ Closed {qid}")
    return 0
