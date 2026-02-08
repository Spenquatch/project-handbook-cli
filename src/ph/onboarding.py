from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class OnboardingError(RuntimeError):
    pass


STATIC_SESSION_TOPIC_MAP: dict[str, str | None] = {
    "sprint-planning": "sprint-planning.md",
    "planning": "sprint-planning.md",
    "sprint-closing": "sprint-closing.md",
    "sprint-close": "sprint-closing.md",
    "close-sprint": "sprint-closing.md",
    "retrospective": "sprint-closing.md",
    "retro": "sprint-closing.md",
    "task-execution": "task-execution.md",
    "execution": "task-execution.md",
    "implement": "task-execution.md",
    "implementation": "task-execution.md",
    "research-discovery": "research-discovery.md",
    "research": "research-discovery.md",
    "discovery": "research-discovery.md",
    "quality-gate": "quality-gate.md",
    "testing": "quality-gate.md",
    "continue-session": None,
    "next-steps": None,
}


def _extract_frontmatter_title(markdown: str) -> str | None:
    if not markdown.startswith("---\n"):
        return None

    lines = markdown.splitlines()
    if len(lines) < 3:
        return None

    if lines[0].strip() != "---":
        return None

    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            break
        if lines[i].startswith("title:"):
            title = lines[i].split(":", 1)[1].strip()
            return title or None

    return None


@dataclass(frozen=True)
class SessionList:
    topics: list[str]

    def render(self) -> str:
        lines: list[str] = []
        lines.append("Available onboarding topics:")
        for topic in self.topics:
            lines.append(f"  - {topic}")
        lines.append("Special topics:")
        lines.append("  - continue-session (print the latest session summary)")
        return "\n".join(lines) + "\n"


def read_onboarding_markdown(*, ph_data_root: Path) -> str:
    path = ph_data_root / "ONBOARDING.md"
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise OnboardingError(f"Missing onboarding file: {path}\n") from exc


def render_onboarding(*, ph_data_root: Path) -> str:
    markdown = read_onboarding_markdown(ph_data_root=ph_data_root)
    title = _extract_frontmatter_title(markdown) or "Project Handbook Onboarding"
    header = title.upper()
    underline = "=" * len(header)
    return f"{header}\n{underline}\n{markdown}\n"


def build_session_topic_map(*, ph_data_root: Path) -> dict[str, str | None]:
    topic_map: dict[str, str | None] = dict(STATIC_SESSION_TOPIC_MAP)
    templates_dir = ph_data_root / "process" / "sessions" / "templates"
    if templates_dir.exists():
        for template_path in templates_dir.glob("*.md"):
            if template_path.is_file():
                topic_map.setdefault(template_path.stem, template_path.name)
    return topic_map


def list_session_topics(*, ph_data_root: Path) -> list[str]:
    topic_map = build_session_topic_map(ph_data_root=ph_data_root)
    return sorted({topic for topic, template_name in topic_map.items() if template_name is not None})


def read_session_template(*, ph_data_root: Path, topic: str) -> str:
    topic_map = build_session_topic_map(ph_data_root=ph_data_root)
    template_name = topic_map.get(topic)
    if template_name is None:
        raise OnboardingError(f"Unknown session topic: {topic}\nUse: ph onboarding session list\n")

    path = ph_data_root / "process" / "sessions" / "templates" / template_name
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise OnboardingError(f"Unknown session topic: {topic}\nUse: ph onboarding session list\n") from exc


def render_session_template(*, ph_data_root: Path, topic: str) -> str:
    body = read_session_template(ph_data_root=ph_data_root, topic=topic)
    header = f"ONBOARDING TOPIC: {topic}"
    underline = "=" * len(header)
    return f"{header}\n{underline}\n{body}\n"


def read_latest_session_summary(*, ph_data_root: Path) -> str:
    path = ph_data_root / "process" / "sessions" / "logs" / "latest_summary.md"
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise OnboardingError(f"Missing latest session summary: {path}\nRemediation: run `ph end-session`.\n") from exc
