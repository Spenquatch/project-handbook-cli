from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class OnboardingError(RuntimeError):
    pass


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


def read_onboarding_markdown(*, ph_root: Path) -> str:
    path = ph_root / "ONBOARDING.md"
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise OnboardingError(f"Missing onboarding file: {path}\n") from exc


def list_session_topics(*, ph_root: Path) -> list[str]:
    templates_dir = ph_root / "process" / "sessions" / "templates"
    if not templates_dir.exists():
        return []
    return sorted(p.stem for p in templates_dir.glob("*.md") if p.is_file())


def read_session_template(*, ph_root: Path, topic: str) -> str:
    path = ph_root / "process" / "sessions" / "templates" / f"{topic}.md"
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise OnboardingError(f"Unknown session topic: {topic}\nUse: ph onboarding session list\n") from exc


def read_latest_session_summary(*, ph_root: Path) -> str:
    path = ph_root / "process" / "sessions" / "logs" / "latest_summary.md"
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise OnboardingError(f"Missing latest session summary: {path}\nRemediation: run `ph end-session`.\n") from exc
