from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import clock


class QuestionError(RuntimeError):
    pass


_QUESTION_ID_RE = re.compile(r"^Q-(\d{4})\b")
_FRONT_MATTER_BOUNDARY = "---"


def _slugify(text: str) -> str:
    raw = (text or "").strip().lower()
    raw = re.sub(r"[^a-z0-9]+", "-", raw)
    raw = re.sub(r"-{2,}", "-", raw).strip("-")
    return raw or "question"


def _parse_front_matter(text: str) -> dict[str, Any]:
    if not text.startswith(f"{_FRONT_MATTER_BOUNDARY}\n"):
        return {}
    lines = text.splitlines()
    out: dict[str, Any] = {}
    for line in lines[1:]:
        if line.strip() == _FRONT_MATTER_BOUNDARY:
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value.lower() in {"true", "false"}:
            out[key] = value.lower() == "true"
        else:
            out[key] = value
    return out


def _render_front_matter(meta: dict[str, Any]) -> str:
    lines = ["---"]
    for k, v in meta.items():
        lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _resolve_current_sprint_id(*, ph_data_root: Path) -> str | None:
    link = ph_data_root / "sprints" / "current"
    if not link.exists():
        return None
    try:
        resolved = link.resolve()
    except Exception:
        return None
    if not resolved.is_dir() or not resolved.name.startswith("SPRINT-"):
        return None
    return resolved.name


@dataclass(frozen=True)
class Question:
    id: str
    title: str
    status: str
    severity: str
    scope: str
    sprint: str | None
    task_id: str | None
    release: str | None
    asked_by: str | None
    owner: str | None
    path: str
    date: str | None


class QuestionManager:
    def __init__(self, *, ph_data_root: Path, env: dict[str, str]) -> None:
        self.ph_data_root = Path(ph_data_root).absolute()
        self.env = env
        self.questions_dir = self.ph_data_root / "status" / "questions"
        self.index_file = self.questions_dir / "index.json"

    def ensure_dirs(self) -> None:
        self.questions_dir.mkdir(parents=True, exist_ok=True)

    def _next_question_id(self) -> str:
        self.ensure_dirs()
        max_seen = 0
        for path in self.questions_dir.glob("Q-*.md"):
            m = _QUESTION_ID_RE.match(path.name)
            if not m:
                continue
            try:
                max_seen = max(max_seen, int(m.group(1)))
            except Exception:
                continue
        return f"Q-{max_seen + 1:04d}"

    def add_question(
        self,
        *,
        title: str,
        severity: str,
        scope: str,
        sprint: str | None,
        task_id: str | None,
        release: str | None,
        asked_by: str | None,
        owner: str | None,
        body: str,
    ) -> str:
        severity_norm = (severity or "").strip().lower()
        if severity_norm not in {"blocking", "non-blocking"}:
            raise QuestionError("Invalid --severity (expected blocking|non-blocking)\n")
        scope_norm = (scope or "").strip().lower()
        if scope_norm not in {"sprint", "task", "release", "project"}:
            raise QuestionError("Invalid --scope (expected sprint|task|release|project)\n")

        sprint_val = (sprint or "").strip() or None
        task_val = (task_id or "").strip() or None
        release_val = (release or "").strip() or None

        if scope_norm in {"sprint", "task"} and not sprint_val:
            raise QuestionError("Missing --sprint for scope sprint|task\n")
        if scope_norm == "task" and not task_val:
            raise QuestionError("Missing --task-id for scope task\n")

        qid = self._next_question_id()
        slug = _slugify(title)
        path = self.questions_dir / f"{qid}-{slug}.md"
        if path.exists():
            raise QuestionError(f"Question already exists: {path}\n")

        today = clock.today(env=self.env).strftime("%Y-%m-%d")
        meta: dict[str, Any] = {
            "id": qid,
            "title": title.strip(),
            "date": today,
            "status": "open",
            "severity": severity_norm,
            "scope": scope_norm,
            "sprint": sprint_val or "null",
            "task_id": task_val or "null",
            "release": release_val or "null",
            "asked_by": asked_by.strip() if (asked_by or "").strip() else "null",
            "owner": owner.strip() if (owner or "").strip() else "null",
        }

        content = _render_front_matter(meta)
        content += f"\n# {qid}: {title.strip()}\n\n"
        content += (body or "").rstrip() + "\n"
        content += "\n## Answer\n\n- Status: open\n"

        path.write_text(content, encoding="utf-8")
        self.update_index(print_summary=False)
        return qid

    def _load_questions(self) -> list[Question]:
        self.ensure_dirs()
        out: list[Question] = []
        for md in sorted(self.questions_dir.glob("Q-*.md"), key=lambda p: p.name):
            text = _read_text(md)
            fm = _parse_front_matter(text)
            qid = str(fm.get("id") or "").strip()
            if not qid:
                continue
            out.append(
                Question(
                    id=qid,
                    title=str(fm.get("title") or md.stem),
                    status=str(fm.get("status") or "open"),
                    severity=str(fm.get("severity") or "non-blocking"),
                    scope=str(fm.get("scope") or "project"),
                    sprint=(
                        None
                        if str(fm.get("sprint") or "").strip().lower() in {"", "null", "none"}
                        else str(fm.get("sprint"))
                    ),
                    task_id=(
                        None
                        if str(fm.get("task_id") or "").strip().lower() in {"", "null", "none"}
                        else str(fm.get("task_id"))
                    ),
                    release=(
                        None
                        if str(fm.get("release") or "").strip().lower() in {"", "null", "none"}
                        else str(fm.get("release"))
                    ),
                    asked_by=(
                        None
                        if str(fm.get("asked_by") or "").strip().lower() in {"", "null", "none"}
                        else str(fm.get("asked_by"))
                    ),
                    owner=(
                        None
                        if str(fm.get("owner") or "").strip().lower() in {"", "null", "none"}
                        else str(fm.get("owner"))
                    ),
                    path=str(md.relative_to(self.ph_data_root)),
                    date=(
                        None
                        if str(fm.get("date") or "").strip().lower() in {"", "null", "none"}
                        else str(fm.get("date"))
                    ),
                )
            )
        return out

    def update_index(self, *, print_summary: bool = True) -> None:
        self.ensure_dirs()
        questions = self._load_questions()
        payload: dict[str, Any] = {
            "last_updated": clock.now(env=self.env).isoformat(),
            "total_items": len(questions),
            "open": [q.id for q in questions if q.status.strip().lower() == "open"],
            "blocking_open": [
                q.id for q in questions if q.status.strip().lower() == "open" and q.severity == "blocking"
            ],
            "items": [
                {
                    "id": q.id,
                    "title": q.title,
                    "status": q.status,
                    "severity": q.severity,
                    "scope": q.scope,
                    "sprint": q.sprint,
                    "task_id": q.task_id,
                    "release": q.release,
                    "asked_by": q.asked_by,
                    "owner": q.owner,
                    "date": q.date,
                    "path": q.path,
                }
                for q in questions
            ],
        }
        self.index_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        if print_summary:
            print(f"📊 Updated questions index: {len(questions)} question(s)")

    def get_questions(self) -> list[Question]:
        return self._load_questions()

    def list_questions(self, *, status: str = "open", format: str = "table") -> None:
        if not self.index_file.exists():
            self.update_index(print_summary=format != "json")
        payload = json.loads(self.index_file.read_text(encoding="utf-8"))
        items = payload.get("items") or []
        if not isinstance(items, list):
            items = []

        status_norm = (status or "open").strip().lower()
        if status_norm != "all":
            items = [i for i in items if str(i.get("status") or "").strip().lower() == status_norm]

        def sort_key(i: dict[str, Any]) -> tuple[int, str]:
            sev = str(i.get("severity") or "non-blocking").strip().lower()
            sev_rank = 0 if sev == "blocking" else 1
            return (sev_rank, str(i.get("id") or ""))

        items = sorted(items, key=sort_key)

        if format == "json":
            print(json.dumps({"items": items}, indent=2))
            return

        print("\n❓ QUESTIONS")
        print("=" * 80)
        if not items:
            print("No questions found")
            return
        for q in items[:50]:
            sev = q.get("severity", "non-blocking")
            scope = q.get("scope", "project")
            sprint = q.get("sprint")
            sprint_str = f" sprint={sprint}" if sprint else ""
            print(f"- {q.get('id')}: [{sev}] [{scope}]{sprint_str} — {q.get('title')}")

    def show_question(self, *, qid: str) -> None:
        self.ensure_dirs()
        qid_norm = (qid or "").strip().upper()
        if not qid_norm.startswith("Q-"):
            raise QuestionError("Invalid --id (expected Q-####)\n")
        matches = list(self.questions_dir.glob(f"{qid_norm}-*.md"))
        if not matches:
            raise QuestionError(f"Question not found: {qid_norm}\n")
        path = matches[0]
        print(path.relative_to(self.ph_data_root))
        print(path.read_text(encoding="utf-8").rstrip())

    def answer_question(self, *, qid: str, answer: str, by: str | None) -> None:
        self.ensure_dirs()
        qid_norm = (qid or "").strip().upper()
        matches = list(self.questions_dir.glob(f"{qid_norm}-*.md"))
        if not matches:
            raise QuestionError(f"Question not found: {qid_norm}\n")
        path = matches[0]
        text = _read_text(path)
        fm = _parse_front_matter(text)
        fm["status"] = "answered"
        fm["answered_by"] = (by or "").strip() or "null"
        fm["answered_date"] = clock.today(env=self.env).strftime("%Y-%m-%d")
        body = text.split(f"{_FRONT_MATTER_BOUNDARY}\n", 2)[-1]
        # Rebuild with updated front matter; keep existing body and append answer note.
        new_text = _render_front_matter(fm) + body
        new_text = new_text.rstrip() + "\n\n### Response\n"
        new_text += f"- By: {(by or '').strip() or '@user'}\n"
        new_text += f"- Date: {fm['answered_date']}\n\n"
        new_text += (answer or "").rstrip() + "\n"
        path.write_text(new_text, encoding="utf-8")
        self.update_index(print_summary=False)

    def close_question(self, *, qid: str, resolution: str) -> None:
        self.ensure_dirs()
        qid_norm = (qid or "").strip().upper()
        matches = list(self.questions_dir.glob(f"{qid_norm}-*.md"))
        if not matches:
            raise QuestionError(f"Question not found: {qid_norm}\n")
        resolution_norm = (resolution or "").strip().lower()
        if resolution_norm not in {"answered", "not-needed", "superseded"}:
            raise QuestionError("Invalid --resolution (expected answered|not-needed|superseded)\n")
        path = matches[0]
        text = _read_text(path)
        fm = _parse_front_matter(text)
        fm["status"] = "closed"
        fm["resolution"] = resolution_norm
        fm["closed_date"] = clock.today(env=self.env).strftime("%Y-%m-%d")
        body = text.split(f"{_FRONT_MATTER_BOUNDARY}\n", 2)[-1]
        new_text = _render_front_matter(fm) + body
        new_text = new_text.rstrip() + "\n\n## Closure\n"
        new_text += f"- Resolution: {resolution_norm}\n"
        new_text += f"- Date: {fm['closed_date']}\n"
        path.write_text(new_text + "\n", encoding="utf-8")
        self.update_index(print_summary=False)

    def blocking_open_for_current_sprint(self) -> list[Question]:
        current = _resolve_current_sprint_id(ph_data_root=self.ph_data_root)
        if not current:
            return []
        questions = self._load_questions()
        out: list[Question] = []
        for q in questions:
            if q.status.strip().lower() != "open":
                continue
            if q.severity.strip().lower() != "blocking":
                continue
            if q.scope not in {"sprint", "task"}:
                continue
            if (q.sprint or "").strip() != current:
                continue
            out.append(q)
        return out
