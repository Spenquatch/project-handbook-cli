from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import load_handbook_config
from .rollout_parser import CodexRolloutParser, RolloutParserError, SessionMetadata

MANIFEST_LIMIT = 5
SESSION_END_RECORD_LIMIT = 200
MAX_RECORD_CHARS = 400
SESSION_END_COMMAND_LIMIT = 30
SESSION_END_OPENING_COUNT = 4
SESSION_END_MIDDLE_COUNT = 2
SESSION_END_CLOSING_COUNT = 8
SESSION_END_PLAN_HINTS = [
    "PLAN_CODEX_LOGGING_REFINEMENTS.md",
    "docs/logs/codex_summarizer_scratchpad.md",
    "status/current_summary.md",
]

READ_GROUP_CATEGORIES = {"read", "list", "search"}
ASSISTANT_ACKS = {"ok", "okay", "done", "sure", "sounds good", "got it", "thanks"}
USER_ACKS = {"thanks", "thank you", "thx"}
ASSISTANT_RESULT_KEYWORDS = {"plan", "next", "result", "fixed", "resolved", "blocker", "issue", "because"}
USER_INTENT_KEYWORDS = {"need", "should", "let's", "please", "can you", "how", "why", "investigate"}
INTENT_KEYWORDS = {"implement", "investigate", "next", "todo", "plan", "update", "fix", "add", "need", "should"}
ASSISTANT_ACTION_KEYWORDS = {"next step", "next steps", "todo", "follow-up", "follow up", "blocker", "blocked"}
PHASE_EXPLORATION = {"read", "list", "search"}
PHASE_VERIFICATION = {"test", "build"}
PHASE_EXECUTION = {"edit", "fs-write", "git"}
PHASE_SUPPORT = {"network", "dangerous", "shell", "misc", "command"}
CHAPTER_VERB_MAP = {
    "edit": "Update",
    "fs-write": "Modify",
    "git": "Refine",
    "test": "Verify",
    "build": "Build",
    "read": "Inspect",
    "list": "Survey",
    "search": "Investigate",
}

CODEX_OVERRIDE_FLAG_MAP = {
    "model_reasoning_effort": "--reasoning-effort",
    "model_reasoning_summary": "--reasoning-summary",
    "model_verbosity": "--model-verbosity",
}

HEADLESS_PROMPT_TEMPLATE = """You are the Project Handbook continuity summarizer.

Using the transcript chunk below (including tools and roles), produce a concise markdown summary with:
- Actions completed (ordered)
- Decisions & rationale
- Blockers or open questions
- Next recommended steps for the next agent

If information is missing for a section, note it explicitly instead of inventing details.
Chunk {index}/{total}:
```
{chunk}
```
"""


class EndSessionError(RuntimeError):
    pass


@dataclass
class SummaryEvent:
    event_id: str
    kind: str
    timestamp: str | None
    local_time: str | None
    text: str
    category: str | None = None
    status: str | None = None
    scope: str | None = None
    duration: float | None = None
    stdout_len: int | None = None
    stderr_len: int | None = None
    touched_files: list[str] = field(default_factory=list)
    call_id: str | None = None
    anchor_index: int | None = None
    reasoning_section: str | None = None
    chapter_hint: str | None = None
    triggers: list[str] | None = None
    phase: str | None = None


@dataclass
class Chapter:
    chapter_id: int
    title: str
    subtitle: str | None
    start_ts: str | None
    end_ts: str | None
    duration_seconds: float | None
    triggers: list[str]
    events: list[SummaryEvent]
    files_touched: list[str]
    summary: str


def resolve_repo_root(*, ph_root: Path) -> Path:
    config = load_handbook_config(ph_root)
    repo_root = Path(config.repo_root)
    if not repo_root.is_absolute():
        return (ph_root / repo_root).resolve()
    return repo_root.expanduser().resolve()


def is_within_repo(repo_root: Path, candidate: str | Path) -> bool:
    try:
        candidate_path = Path(candidate).expanduser().resolve()
    except Exception:
        return False
    try:
        candidate_path.relative_to(repo_root.resolve())
        return True
    except Exception:
        return False


def parse_iso8601(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except Exception:
        return None


def format_local_timestamp(value: str | None) -> str:
    ts = parse_iso8601(value)
    if not ts:
        return value or "?"
    return ts.astimezone().strftime("%a %b %d - %I:%M %p")


def format_duration_label(seconds: float | None) -> str:
    if seconds is None:
        return "n/a"
    total = max(0, int(seconds))
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    parts: list[str] = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if not parts:
        parts.append(f"{secs}s")
    elif secs and not hours and minutes < 5:
        parts.append(f"{secs}s")
    return " ".join(parts)


def to_local_naive(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone().replace(tzinfo=None)


def trim_text(value: str, limit: int = MAX_RECORD_CHARS) -> str:
    value = value.strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def trim_text_middle(value: str, limit: int) -> str:
    value = value.strip()
    if len(value) <= limit:
        return value
    if limit <= 3:
        return value[:limit]
    half = max(1, (limit - 3) // 2)
    prefix = value[:half].rstrip()
    suffix = value[-half:].lstrip()
    return f"{prefix}...{suffix}"


def collapse_content(chunks: Iterable[dict[str, Any]]) -> str:
    parts: list[str] = []
    for chunk in chunks:
        chunk_type = chunk.get("type")
        if chunk_type in {"input_text", "output_text"}:
            parts.append(chunk.get("text", ""))
        elif chunk_type == "tool_invocation":
            summary = chunk.get("summary")
            if summary:
                parts.append(f"[tool] {summary}")
    return "\n".join(part for part in parts if part).strip()


def indent_block(text: str, prefix: str = "  ") -> str:
    return "\n".join(prefix + line if line else prefix for line in text.splitlines())


def format_function_call(entry: dict[str, Any]) -> str:
    payload = entry.get("payload") or {}
    args_raw = payload.get("arguments", "")
    try:
        parsed = json.loads(args_raw)
        args_display = json.dumps(parsed, indent=2)
    except Exception:
        args_display = str(args_raw).strip()
    timestamp = entry.get("timestamp", "unknown")
    name = payload.get("name", "<unknown>")
    return f"- [{timestamp}] {name}\n{indent_block(args_display)}"


def extract_context(
    entries: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[dict[str, Any]], list[str], list[str]]:
    session_meta = next((e for e in entries if e.get("type") == "session_meta"), None)
    turn_contexts = [e for e in entries if e.get("type") == "turn_context"]
    function_calls = [
        e
        for e in entries
        if e.get("type") == "response_item"
        and (e.get("payload") or {}).get("type") in {"function_call", "custom_tool_call", "custom_tool_call_output"}
    ]
    messages_user = [
        collapse_content((e.get("payload") or {}).get("content", []))
        for e in entries
        if e.get("type") == "response_item"
        and (e.get("payload") or {}).get("type") == "message"
        and (e.get("payload") or {}).get("role") == "user"
    ]
    messages_assistant = [
        collapse_content((e.get("payload") or {}).get("content", []))
        for e in entries
        if e.get("type") == "response_item"
        and (e.get("payload") or {}).get("type") == "message"
        and (e.get("payload") or {}).get("role") == "assistant"
    ]
    return session_meta, turn_contexts, function_calls, messages_user, messages_assistant


def summarize_output(text: str | None) -> str:
    if not text:
        return ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:160]
    return ""


def build_command_timeline(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    timeline: list[dict[str, Any]] = []
    for entry in entries:
        if entry.get("type") != "response_item":
            continue
        payload = entry.get("payload") or {}
        if payload.get("type") != "message":
            continue
        role = payload.get("role", "assistant")
        full_text = collapse_content(payload.get("content", []))
        snippet = summarize_output(full_text)
        timestamp = entry.get("timestamp")
        timeline.append(
            {
                "timestamp": timestamp,
                "local_time": format_local_timestamp(timestamp),
                "event": "message",
                "role": role,
                "text": snippet or "",
            }
        )
    return timeline


def build_summary_events_from_timeline(timeline: list[dict[str, Any]]) -> list[SummaryEvent]:
    summary_events: list[SummaryEvent] = []
    seq = 0
    anchor_index = 0
    for raw in timeline:
        seq += 1
        event_type = raw.get("event")
        if event_type != "message":
            continue
        anchor_index += 1
        role = raw.get("role", "assistant")
        kind = "user_message" if role == "user" else "assistant_message"
        text = raw.get("text") or ""
        hint = infer_chapter_hint(kind, text, None, None)
        triggers: list[str] = []
        if hint == "intent":
            triggers.append("intent_change")
        phase = determine_phase(kind, None)
        summary_events.append(
            SummaryEvent(
                event_id=f"{seq:05d}",
                kind=kind,
                timestamp=raw.get("timestamp"),
                local_time=raw.get("local_time"),
                text=text,
                anchor_index=anchor_index,
                chapter_hint=hint,
                triggers=triggers,
                phase=phase,
            )
        )
    return summary_events


def format_transcript_timestamp(event: SummaryEvent) -> str:
    return event.local_time or format_local_timestamp(event.timestamp) or event.timestamp or "?"


def infer_chapter_hint(kind: str, text: str, category: str | None, status: str | None) -> str | None:
    lowered = (text or "").lower()
    if kind == "user_message" and any(word in lowered for word in INTENT_KEYWORDS):
        return "intent"
    if kind == "assistant_message" and any(word in lowered for word in ASSISTANT_ACTION_KEYWORDS):
        return "next_step"
    if kind == "command":
        if status == "failure":
            return "failure"
        if category in {"build", "test"}:
            return "verification"
        if category in {"edit", "fs-write"}:
            return "execution"
        if category in {"read", "list", "search"}:
            return "exploration"
    if kind == "context_change":
        return "context_shift"
    if kind == "assistant_reasoning":
        return "reasoning"
    return None


def determine_phase(kind: str, category: str | None) -> str | None:
    category = (category or "").lower()
    if kind == "command":
        if category in PHASE_EXPLORATION:
            return "exploration"
        if category in PHASE_VERIFICATION:
            return "verification"
        if category in PHASE_EXECUTION:
            return "execution"
        if category in PHASE_SUPPORT:
            return category
        return "command"
    if kind == "assistant_reasoning":
        return "reasoning"
    if kind in {"user_message", "assistant_message"}:
        return "communication"
    if kind == "context_change":
        return "context"
    return None


def should_keep_user_message(text: str, hint: str | None) -> bool:
    snippet = (text or "").strip()
    if not snippet:
        return False
    lowered = snippet.lower()
    if lowered in USER_ACKS:
        return False
    if hint == "intent":
        return True
    if any(keyword in lowered for keyword in USER_INTENT_KEYWORDS):
        return True
    return len(snippet) >= 25 or "?" in snippet


def should_keep_assistant_message(text: str, hint: str | None) -> bool:
    snippet = (text or "").strip()
    if not snippet:
        return False
    lowered = snippet.lower()
    if lowered in ASSISTANT_ACKS and hint != "next_step":
        return False
    if hint == "next_step":
        return True
    if any(keyword in lowered for keyword in ASSISTANT_RESULT_KEYWORDS):
        return True
    return len(snippet) >= 40


def build_command_line(event: SummaryEvent) -> str:
    stamp = format_transcript_timestamp(event)
    status = (event.status or "run").upper()
    scope = event.scope or "repo"
    snippet = trim_text(event.text or "", 180)
    files = ", ".join(Path(path).name for path in event.touched_files[:3])
    file_suffix = f" | files: {files}" if files else ""
    return f"[{stamp}] CMD {status} [{scope}] :: {snippet}{file_suffix}"


def summarize_read_run(run: list[SummaryEvent]) -> str | None:
    if not run:
        return None
    first = run[0]
    stamp = format_transcript_timestamp(first)
    scope = first.scope or "repo"
    files = sorted({Path(path).name for event in run for path in (event.touched_files or [])})
    if files:
        display = ", ".join(files[:3])
        if len(files) > 3:
            display += f" +{len(files) - 3}"
    else:
        display = trim_text(first.text or "", 80) or "inspection"
    return f"[{stamp}] READ sweep x{len(run)} [{scope}] :: {display}"


def format_context_line(event: SummaryEvent) -> str:
    stamp = format_transcript_timestamp(event)
    text = trim_text(event.text or "", 160)
    source = event.scope or "context"
    return f"[{stamp}] CTX ({source}) :: {text or 'unchanged'}"


def format_reasoning_line(event: SummaryEvent) -> str:
    stamp = format_transcript_timestamp(event)
    prefix = event.reasoning_section or "Reasoning"
    text = trim_text(event.text or "", 220)
    if prefix and prefix not in text:
        text = f"{prefix}: {text}"
    return f"[{stamp}] PLAN :: {text}"


def build_pruned_transcript(events: list[SummaryEvent]) -> list[str]:
    pruned: list[str] = []
    read_run: list[SummaryEvent] = []

    def flush_read_run() -> None:
        if not read_run:
            return
        line = summarize_read_run(read_run)
        if line:
            pruned.append(line)
        read_run.clear()

    for event in events:
        if event.kind == "command" and (event.category or "") in READ_GROUP_CATEGORIES:
            read_run.append(event)
            continue

        flush_read_run()
        stamp = format_transcript_timestamp(event)

        if event.kind == "command":
            pruned.append(build_command_line(event))
        elif event.kind == "user_message":
            if should_keep_user_message(event.text, event.chapter_hint):
                pruned.append(f"[{stamp}] USER :: {trim_text(event.text or '', 220)}")
        elif event.kind == "assistant_message":
            if should_keep_assistant_message(event.text, event.chapter_hint):
                pruned.append(f"[{stamp}] ASSISTANT :: {trim_text(event.text or '', 220)}")
        elif event.kind == "assistant_reasoning":
            pruned.append(format_reasoning_line(event))
        elif event.kind == "context_change":
            pruned.append(format_context_line(event))

    flush_read_run()
    return pruned


def build_chapters_from_events(events: list[SummaryEvent]) -> list[Chapter]:
    chapters: list[Chapter] = []
    if not events:
        return chapters

    def finalize(chapter_id: int, collected: list[SummaryEvent], triggers: list[str]) -> Chapter | None:
        if not collected:
            return None
        start_ts = collected[0].timestamp
        end_ts = collected[-1].timestamp
        start_dt = parse_iso8601(start_ts)
        end_dt = parse_iso8601(end_ts)
        duration = None
        if start_dt and end_dt:
            duration = max(0.0, (end_dt - start_dt).total_seconds())
        files = sorted({file for event in collected for file in event.touched_files})
        title = generate_chapter_title(collected, triggers)
        subtitle = generate_chapter_subtitle(collected, triggers)
        summary = summarize_chapter(collected)
        return Chapter(
            chapter_id=chapter_id,
            title=title,
            subtitle=subtitle,
            start_ts=start_ts,
            end_ts=end_ts,
            duration_seconds=duration,
            triggers=triggers,
            events=collected,
            files_touched=files,
            summary=summary,
        )

    guardrail_triggers = {
        "intent_change",
        "failure",
        "context_shift",
        "scope_shift",
        "reasoning_section_break",
        "edit_block",
        "phase_change",
    }

    chapter_events: list[SummaryEvent] = []
    chapter_triggers: list[str] = []
    chapter_counter = 1
    last_ts: datetime | None = None
    last_scope: str | None = None
    last_phase: str | None = None

    def start_new_chapter() -> None:
        nonlocal chapter_events, chapter_triggers, chapter_counter
        chapter = finalize(chapter_counter, chapter_events, chapter_triggers)
        if chapter:
            chapters.append(chapter)
            chapter_counter += 1
        chapter_events = []
        chapter_triggers = []

    for event in events:
        event_triggers = list(event.triggers or [])
        event_ts = parse_iso8601(event.timestamp)
        if last_ts and event_ts:
            delta = (event_ts - last_ts).total_seconds()
            if delta > 300:
                event_triggers.append("time_gap")
        if event.kind == "user_message" and event.chapter_hint == "intent":
            event_triggers.append("intent_change")
        if event.kind == "command":
            if last_scope and event.scope and event.scope != last_scope:
                event_triggers.append("scope_shift")
            if last_phase and event.phase and event.phase != last_phase:
                event_triggers.append("phase_change")
            last_scope = event.scope or last_scope
            last_phase = event.phase or last_phase
        if event.kind == "assistant_reasoning" and event.reasoning_section:
            event_triggers.append("reasoning_section_break")
        if event_ts:
            last_ts = event_ts

        should_split = False
        if not chapter_events:
            should_split = False
        elif any(trigger in guardrail_triggers for trigger in event_triggers):
            should_split = True
        elif "time_gap" in event_triggers:
            should_split = True

        if should_split:
            start_new_chapter()

        chapter_events.append(event)
        chapter_triggers.extend(event_triggers)

    start_new_chapter()
    return chapters


def generate_chapter_title(events: list[SummaryEvent], triggers: list[str]) -> str:
    if not events:
        return "Chapter"
    intent = next(
        (trim_text(e.text or "", 80) for e in events if e.kind == "user_message" and e.chapter_hint == "intent"),
        None,
    )
    command = next((e for e in events if e.kind == "command"), None)

    if intent:
        base = intent
    elif command:
        verb = CHAPTER_VERB_MAP.get((command.category or "").lower(), (command.phase or "Work").title())
        if command.touched_files:
            target = Path(command.touched_files[0]).name
        else:
            target = trim_text(command.text or "", 60)
        base = f"{verb} {target}".strip()
    else:
        base = trim_text(events[0].text or "Chapter", 60)

    if len(base) < 5:
        base = "Chapter"

    tag = None
    if "failure" in triggers:
        tag = "BLOCKED"
    elif any(e.kind == "command" and e.status == "success" for e in events):
        tag = "COMPLETED"
    elif "reasoning_section_break" in triggers:
        tag = "PLAN"
    elif "scope_shift" in triggers:
        tag = "SCOPE"
    elif "phase_change" in triggers:
        tag = "PHASE"
    if tag:
        return f"{base.strip()} [{tag}]"
    return base.strip()


def generate_chapter_subtitle(events: list[SummaryEvent], triggers: list[str]) -> str | None:
    commands = [event for event in events if event.kind == "command"]
    if not commands:
        reasoning = next((event for event in events if event.kind == "assistant_reasoning"), None)
        if reasoning:
            prefix = reasoning.reasoning_section or "Plan"
            return f"{prefix}: {trim_text(reasoning.text or '', 80)}"
        message = next((event for event in events if event.kind == "assistant_message"), None)
        if message:
            return trim_text(message.text or "", 80)
        return None

    files = sorted({Path(path).name for event in commands for path in event.touched_files})
    if files:
        file_part = ", ".join(files[:2])
        if len(files) > 2:
            file_part += f" +{len(files) - 2}"
    else:
        file_part = trim_text(commands[0].text or "", 60)

    status = "blocked" if "failure" in triggers else "in progress"
    if any(cmd.status == "success" for cmd in commands):
        status = "completed"
    phase = commands[0].phase or commands[0].category or "work"
    return f"{phase.title()} focus on {file_part} ({status})"


def summarize_chapter(events: list[SummaryEvent]) -> str:
    plan_parts: list[str] = []
    action_parts: list[str] = []
    result_parts: list[str] = []

    for event in events:
        if event.kind == "user_message" and event.chapter_hint == "intent":
            plan_parts.append(trim_text(event.text or "", 160))
        elif event.kind == "assistant_reasoning":
            plan_parts.append(trim_text(event.text or "", 160))
        elif event.kind == "command":
            detail = trim_text(event.text or "", 120)
            status = (event.status or "run").upper()
            action_parts.append(f"{status}: {detail}")
            if event.status == "failure":
                result_parts.append(f"Blocked: {detail}")
            elif event.status == "success":
                result_parts.append(f"Done: {detail}")
        elif event.kind == "assistant_message" and event.chapter_hint == "next_step":
            result_parts.append(f"Next: {trim_text(event.text or '', 140)}")

    plan_text = plan_parts[0] if plan_parts else "No explicit plan captured."
    actions_text = "; ".join(action_parts[:3]) if action_parts else "Actions centered on setup/inspection."
    results_text = "; ".join(result_parts[:2]) if result_parts else "Results pending or not recorded."
    return f"Plan: {plan_text} | Actions: {actions_text} | Results: {results_text}"


def normalize_entry(entry: dict[str, Any]) -> str | None:
    timestamp = parse_iso8601(entry.get("timestamp"))
    stamp = timestamp.astimezone().strftime("%Y-%m-%d %H:%M") if timestamp else "unknown"
    entry_type = entry.get("type")
    payload = entry.get("payload") or {}

    if entry_type == "response_item":
        payload_type = payload.get("type")
        if payload_type == "message":
            text = collapse_content(payload.get("content", []))
            role = payload.get("role", "assistant")
            if not text.strip():
                return None
            return f"[{stamp}] {role}: {trim_text(text)}"
        if payload_type == "function_call":
            name = payload.get("name", "<function>")
            arguments = payload.get("arguments", "")
            return f"[{stamp}] tool-call {name}: {trim_text(arguments)}"
        if payload_type in {"function_call_output", "custom_tool_call_output"}:
            output = payload.get("output") or payload.get("content")
            return f"[{stamp}] tool-output: {trim_text(str(output or ''))}"
        if payload_type == "custom_tool_call":
            name = payload.get("name", "<tool>")
            args = payload.get("arguments", "")
            return f"[{stamp}] tool {name}: {trim_text(args)}"

    if entry_type == "event_msg":
        payload_type = payload.get("type")
        if payload_type == "user_message":
            message = payload.get("message", "")
            if message.strip():
                return f"[{stamp}] user: {trim_text(message)}"
        if payload_type in {"agent_reasoning", "reasoning"}:
            text = payload.get("text") or payload.get("message") or ""
            if text.strip():
                return f"[{stamp}] assistant-reasoning: {trim_text(text)}"
        return None

    if entry_type == "turn_context":
        summary = payload.get("summary")
        if summary:
            return f"[{stamp}] ctx: {trim_text(summary)}"

    return None


def build_normalized_blocks(entries: list[dict[str, Any]]) -> list[str]:
    blocks: list[str] = []
    for entry in entries:
        normalized = normalize_entry(entry)
        if normalized:
            blocks.append(normalized)
    return blocks


def compute_log_bounds(entries: list[dict[str, Any]]) -> tuple[datetime | None, datetime | None]:
    timestamps = [parse_iso8601(entry.get("timestamp")) for entry in entries if entry.get("timestamp")]
    start = next((ts for ts in timestamps if ts), None)
    end = next((ts for ts in reversed(timestamps) if ts), start)
    return start, end


def format_summary_path(logs_dir: Path, start: datetime | None, session_id: str | None) -> Path:
    if start is None:
        start = datetime.now(timezone.utc)
    if start.tzinfo is not None:
        start = start.astimezone(timezone.utc).replace(tzinfo=None)
    base_dir = logs_dir / f"{start.year:04d}" / f"{start.month:02d}" / f"{start.day:02d}"
    if session_id:
        base_dir = base_dir / session_id
    base_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{start.strftime('%H%M%S')}_summary.md"
    return base_dir / filename


def timestamp_from_filename(path: Path) -> datetime | None:
    match = re.match(r"rollout-(\d{4}-\d{2}-\d{2})T(\d{2})-(\d{2})-(\d{2})-", path.name)
    if not match:
        return None
    date_part, hour, minute, second = match.groups()
    timestamp_str = f"{date_part}T{hour}:{minute}:{second}"
    try:
        return datetime.fromisoformat(timestamp_str)
    except ValueError:
        return None


def read_history_entries(history_log: Path, limit: int = 50) -> list[tuple[datetime, str]]:
    if not history_log.exists():
        return []
    entries: list[tuple[datetime, str]] = []
    with history_log.open("r", encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw or "|" not in raw:
                continue
            timestamp_str, command = raw.split("|", 1)
            try:
                parsed = datetime.strptime(timestamp_str.strip(), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            entries.append((parsed, command.strip()))
    return entries[-limit:]


def filter_history_window(
    entries: Sequence[tuple[datetime, str]],
    start: datetime | None,
    end: datetime | None,
    limit: int = 15,
) -> list[tuple[datetime, str]]:
    if not entries:
        return []
    if start and end:
        scoped = [entry for entry in entries if start <= entry[0] <= end]
        if scoped:
            return scoped[-limit:]
    return list(entries[-limit:])


def read_status_snapshot(status_path: Path, max_lines: int = 25) -> tuple[list[str], bool]:
    if not status_path.exists():
        return ([], False)
    text = status_path.read_text(encoding="utf-8")
    lines = [line.rstrip() for line in text.splitlines()]
    truncated = len(lines) > max_lines
    return (lines[:max_lines], truncated)


def render_summary(
    entries: list[dict[str, Any]],
    codex_highlights: str,
    chunk_outputs: list[str],
    history_entries: list[tuple[datetime, str]],
    status_lines: list[str],
    status_truncated: bool,
    pruned_blocks: list[str],
    command_timeline: list[dict[str, Any]],
    chapters: list[Any],
) -> str:
    session_meta, turn_contexts, function_calls, messages_user, messages_assistant = extract_context(entries)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines: list[str] = [f"# Session Summary ({now})", ""]

    lines.append("## Session Info")
    if session_meta:
        payload = session_meta.get("payload") or {}
        lines.append(f"- Session ID: `{payload.get('id', '<unknown>')}`")
        lines.append(f"- Working dir: `{payload.get('cwd', '<unknown>')}`")
        lines.append(f"- Originator: `{payload.get('originator', '<unknown>')}`")
        if payload.get("cli_version"):
            lines.append(f"- CLI version: `{payload['cli_version']}`")
    if turn_contexts:
        last_ctx = turn_contexts[-1].get("payload") or {}
        if last_ctx.get("summary"):
            lines.append(f"- Last turn summary: {last_ctx['summary']}")
    lines.append("")

    lines.append("## Codex Compressed Highlights")
    lines.append(codex_highlights.strip() or "(No headless summary returned.)")
    lines.append("")

    if chunk_outputs:
        lines.append("### Chunk Outputs")
        for index, output in enumerate(chunk_outputs, start=1):
            lines.append(f"**Chunk {index}:**")
            lines.append(output.strip() or "(empty)")
            lines.append("")

    lines.append("## Commands & Tool Calls")
    if function_calls:
        for call in function_calls[-10:]:
            lines.append(format_function_call(call))
    else:
        lines.append("- (No tool invocations recorded)")
    lines.append("")

    def append_messages(header: str, messages: list[str]) -> None:
        lines.append(f"## {header}")
        if messages:
            for msg in messages[-3:]:
                trimmed = msg.strip()
                if not trimmed:
                    continue
                snippet = trimmed if len(trimmed) < 400 else trimmed[:397] + "..."
                lines.append(f"- {snippet}")
        else:
            lines.append("- (No entries)")
        lines.append("")

    append_messages("Recent User Inputs", messages_user)
    append_messages("Recent Assistant Responses", messages_assistant)

    lines.append("## Pruned Transcript Sample")
    sample = pruned_blocks[-8:]
    if sample:
        lines.extend(f"- {line}" for line in sample)
    else:
        lines.append("- (No transcript data)")
    lines.append("")

    lines.append("## Chapter Timeline")
    if chapters:
        for chapter in chapters[-5:]:
            duration = f"{chapter.duration_seconds:.0f}s" if chapter.duration_seconds else "?"
            files = ", ".join(chapter.files_touched[:3]) if chapter.files_touched else "no file changes"
            lines.append(f"- {chapter.title} ({duration}) – {files}")
            if chapter.subtitle:
                lines.append(f"  - {chapter.subtitle}")
            lines.append(f"  - {chapter.summary}")
    else:
        lines.append("- (No chapter data)")
    lines.append("")

    lines.append("## Command Timeline (recent)")
    if command_timeline:
        for event in command_timeline[-10:]:
            if event.get("event") == "command":
                status = event.get("status", "pending")
                summary_line = event.get("summary") or "(no output)"
                command_text = event.get("display_command") or event.get("tool")
                category = event.get("category", "misc").upper()
                scope = event.get("scope", "unknown")
                stats: list[str] = []
                duration = event.get("duration")
                if isinstance(duration, int | float):
                    stats.append(f"{duration:.2f}s")
                stdout_len = event.get("stdout_len")
                if isinstance(stdout_len, int):
                    stats.append(f"out={stdout_len}")
                stderr_len = event.get("stderr_len")
                if isinstance(stderr_len, int):
                    stats.append(f"err={stderr_len}")
                stat_suffix = f" ({', '.join(stats)})" if stats else ""
                lines.append(
                    f"- [{event.get('timestamp', 'unknown')}] {category} {status.upper()} [{scope}] "
                    f":: {command_text} :: {summary_line}{stat_suffix}"
                )
            elif event.get("event") == "message":
                lines.append(f"- [{event.get('timestamp', 'unknown')}] message from {event.get('role', 'assistant')}")
            elif event.get("event") == "context":
                change_line = event.get("changes") or "(no changes recorded)"
                source = event.get("source", "context")
                lines.append(
                    f"- [{event.get('timestamp', 'unknown')}] CONTEXT ({source}) :: "
                    f"{change_line or '(no changes recorded)'}"
                )
            elif event.get("event") == "reasoning":
                section = event.get("section")
                text = event.get("text") or ""
                summary_text = text or "(no reasoning text)"
                if section and section not in summary_text:
                    summary_text = f"{section}: {summary_text}"
                lines.append(f"- [{event.get('timestamp', 'unknown')}] reasoning :: {summary_text}")
    else:
        lines.append("- (No command or message events recorded)")
    lines.append("")

    lines.append("## Recent CLI Commands")
    if history_entries:
        for timestamp, command in history_entries:
            lines.append(f"- {timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {command}")
    else:
        lines.append("- (No command history recorded yet)")
    lines.append("")

    lines.append("## Current Sprint Snapshot")
    if status_lines:
        lines.append("```markdown")
        lines.extend(status_lines)
        if status_truncated:
            lines.append("… (see status/current_summary.md for full details)")
        lines.append("```")
    else:
        lines.append("- status/current_summary.md not found")
    lines.append("")

    lines.append("## Suggested Next Steps")
    next_steps = [msg for msg in messages_assistant[-5:] if "next step" in msg.lower() or "todo" in msg.lower()]
    if next_steps:
        for step in next_steps:
            snippet = step.strip()
            lines.append(f"- {snippet}")
    else:
        lines.append("- Review `status/current_summary.md` and backlog updates.")
        lines.append("- Re-run `ph onboarding session continue-session` before resuming work.")

    lines.append("")
    lines.append("> Generated automatically from Codex logs, command history, and sprint status.")
    return "\n".join(lines)


def build_compact_command_lines(events: list[SummaryEvent], limit: int) -> list[str]:
    rows: list[str] = []
    current: dict[str, Any] | None = None

    def finalize(acc: dict[str, Any]) -> None:
        line = acc["line"]
        count = acc.get("count", 1)
        if count > 1:
            line = f"{line} (x{count})"
        rows.append(line)

    for event in events:
        if event.kind != "command":
            continue
        signature = (event.category or "", event.scope or "", event.text or "")
        line = format_session_end_command_line(event)
        if current and current.get("signature") == signature:
            current["count"] = current.get("count", 1) + 1
            continue
        if current:
            finalize(current)
        current = {"signature": signature, "line": line, "count": 1}
        if len(rows) + 1 >= limit:
            break

    if current and len(rows) < limit:
        finalize(current)

    return rows[:limit]


def format_session_end_command_line(event: SummaryEvent) -> str:
    timestamp = event.local_time or format_local_timestamp(event.timestamp)
    category = (event.category or "misc").upper()
    status = (event.status or "run").upper()
    scope = event.scope or "unknown"
    detail = trim_text(event.text or "", 200)
    extras: list[str] = []
    if event.duration is not None:
        extras.append(f"{event.duration:.2f}s")
    if event.stdout_len:
        extras.append(f"out={event.stdout_len}")
    if event.stderr_len:
        extras.append(f"err={event.stderr_len}")
    meta = f" ({', '.join(extras)})" if extras else ""
    return f"- [{timestamp}] {category} {status} [{scope}] {detail}{meta}"


def gather_message_events(events: list[SummaryEvent]) -> list[SummaryEvent]:
    keep = {"user_message", "assistant_message", "assistant_reasoning"}
    return [event for event in events if event.kind in keep]


def determine_message_indices(events: list[SummaryEvent], mode: str, count: int) -> list[int]:
    total = len(events)
    if total == 0:
        return []
    if mode == "opening":
        return list(range(total))
    if mode == "closing":
        return list(range(total - 1, -1, -1))

    primary_indices = [idx for idx, event in enumerate(events) if event.kind in {"user_message", "assistant_message"}]
    anchor = None
    if primary_indices:
        total_primary = len(primary_indices)
        band_start = int(total_primary * 0.35)
        band_end = max(band_start + 1, int(total_primary * 0.7))
        band_end = min(total_primary, band_end)
        for primary_pos in range(band_start, band_end):
            idx = primary_indices[primary_pos]
            if events[idx].kind == "user_message":
                anchor = idx
                break
        if anchor is None:
            anchor = primary_indices[min(total_primary - 1, total_primary // 2)]
    else:
        band_start = int(total * 0.35)
        band_end = max(band_start + 1, int(total * 0.7))
        band_end = min(total, band_end)
        for idx in range(band_start, band_end):
            if events[idx].kind == "user_message":
                anchor = idx
                break
    if anchor is None:
        anchor = total // 2
    half_span = max(1, (count + 1) // 2)
    start = max(0, anchor - half_span)
    end = min(total, start + max(count, half_span * 2))
    return list(range(start, end))


def message_dedupe_key(event: SummaryEvent) -> str | None:
    text = (event.text or "").strip()
    if not text:
        return None
    normalized = re.sub(r"\s+", " ", text.lower())
    role = event.kind or "message"
    return f"{role}:{normalized}"


def message_dedupe_key_from_line(line: str | None) -> str | None:
    if not line:
        return None
    normalized = re.sub(r"\s+", " ", line.strip().lower())
    return normalized or None


def format_message_line(event: SummaryEvent, first_user_full: bool = False) -> str:
    text = (event.text or "").strip()
    if not text:
        return ""
    ts = event.local_time or format_local_timestamp(event.timestamp)
    role = event.kind.replace("_", " ")
    limit = 260
    middle = False
    if first_user_full and event.kind == "user_message":
        limit = 2500
        middle = True
    content = trim_text_middle(text, limit) if middle else trim_text(text, limit)
    return f"- [{ts}] {role}: {content}"


def collect_message_slice(events: list[SummaryEvent], mode: str, count: int) -> list[str]:
    if not events or count <= 0:
        return []
    formatted: list[str] = []
    indices = determine_message_indices(events, mode, count)

    def attempt(allowed_kinds: set[str]) -> None:
        nonlocal formatted
        seen: set[str] = {message_dedupe_key_from_line(line) for line in formatted if line}
        last_line: str | None = None
        first_user_rendered = any("user message" in line for line in formatted)
        for idx in indices:
            if len(formatted) >= count:
                break
            event = events[idx]
            if allowed_kinds and event.kind not in allowed_kinds:
                continue
            render_full = False
            if mode == "opening" and event.kind == "user_message" and not first_user_rendered:
                render_full = True
                first_user_rendered = True
            line = format_message_line(event, first_user_full=render_full)
            if not line:
                continue
            key = message_dedupe_key(event)
            if key and key in seen:
                continue
            if last_line == line:
                continue
            formatted.append(line)
            last_line = line
            if key:
                seen.add(key)

    primary = {"user_message", "assistant_message"}
    attempt(primary)
    if len(formatted) < count:
        attempt({"assistant_reasoning"})

    if mode == "closing":
        formatted = list(reversed(formatted))
    return formatted[:count]


def derive_task_hint(message_events: list[SummaryEvent], metadata: SessionMetadata) -> str:
    for event in reversed(message_events):
        if event.kind == "user_message" and event.text:
            return trim_text(event.text.strip(), 160)
    if metadata.instructions:
        return trim_text(metadata.instructions.strip(), 160)
    return "Continue where the last session left off."


def derive_next_steps_hint(message_events: list[SummaryEvent]) -> str | None:
    for event in reversed(message_events):
        if event.kind in {"assistant_message", "assistant_reasoning"} and event.text:
            lowered = event.text.lower()
            if any(keyword in lowered for keyword in ("next", "todo", "plan", "continue")):
                return trim_text(event.text.strip(), 200)
    return None


def format_project_pointers(task_ref: str | None, repo_root: Path) -> list[str]:
    pointers: list[str] = []
    if task_ref:
        pointers.append(f"- Task reference: {task_ref}")
    for relative in SESSION_END_PLAN_HINTS:
        path = repo_root / relative
        if path.exists():
            pointers.append(f"- Review `{relative}` for broader context.")
    if not pointers:
        pointers.append("- Review project-handbook docs for broader context.")
    return pointers


def build_session_end_documents(
    *,
    mode: str,
    metadata: SessionMetadata,
    summary_events: list[SummaryEvent],
    workstream: str,
    task_ref: str | None,
    start_utc: datetime | None,
    end_utc: datetime | None,
    summary_relpath: str,
    summary_id: str,
    repo_root: Path,
) -> tuple[str, str, dict[str, Any]]:
    command_limit = SESSION_END_COMMAND_LIMIT if mode == "continue-task" else max(10, SESSION_END_COMMAND_LIMIT // 2)
    command_lines = build_compact_command_lines(summary_events, command_limit)
    message_events = gather_message_events(summary_events)
    opening = collect_message_slice(message_events, "opening", SESSION_END_OPENING_COUNT)
    middle = collect_message_slice(message_events, "middle", SESSION_END_MIDDLE_COUNT)
    closing = collect_message_slice(message_events, "closing", SESSION_END_CLOSING_COUNT)
    task_hint = derive_task_hint(message_events, metadata)
    next_hint = derive_next_steps_hint(message_events)

    git_info = metadata.git or {}
    branch = git_info.get("branch") or "n/a"
    start_label = start_utc.astimezone().strftime("%a %b %d %I:%M %p") if start_utc else "?"
    end_label = end_utc.astimezone().strftime("%a %b %d %I:%M %p") if end_utc else "?"
    duration_seconds = None
    if start_utc and end_utc:
        duration_seconds = max(0.0, (end_utc - start_utc).total_seconds())
    duration_label = format_duration_label(duration_seconds)

    header_lines = [
        f"# Session-End Recap ({mode.replace('-', ' ').title()})",
        f"- Summary ID: {summary_id}",
        f"- Workstream: {workstream}",
        f"- Session: {metadata.session_id or 'n/a'}",
        f"- Branch: {branch}",
        f"- Window: {start_label} → {end_label} ({duration_label})",
        f"- Mode: {mode}",
        f"- Summary Path: `{summary_relpath}`",
    ]
    if task_ref:
        header_lines.append(f"- Task Ref: {task_ref}")
    header_lines.append("")

    lines = list(header_lines)
    lines.append("## Command Timeline")
    if command_lines:
        lines.extend(command_lines)
    else:
        lines.append("- (No commands recorded)")
    lines.append("")

    lines.append("## Conversation Highlights")
    sections = [
        ("Opening Intent", opening),
        ("Mid-session Pulse", middle),
        ("Latest Context", closing),
    ]
    for title, block in sections:
        lines.append(f"### {title}")
        if block:
            lines.extend(block)
        else:
            lines.append("- (no messages captured)")
        lines.append("")

    lines.append("## Project / Sprint Context")
    pointers = format_project_pointers(task_ref, repo_root)
    lines.extend(pointers)
    lines.append("")

    if mode == "continue-task":
        lines.append("## Focus for Next Session")
        lines.append(f"- Continue: {task_hint}")
        if next_hint:
            lines.append(f"- Last assistant guidance: {next_hint}")
    else:
        lines.append("## Sprint Hand-off Notes")
        lines.append(f"- Prior task recap: {task_hint}")
        if next_hint:
            lines.append(f"- Open question / next steps: {next_hint}")
        lines.append("- Shift to the next sprint task with the context above.")
    lines.append("")

    prompt_lines = [
        f"Workstream '{workstream}' session recap ({mode}).",
        f"Review {summary_relpath} for context.",
    ]
    if task_ref:
        prompt_lines.append(f"Task reference: {task_ref}.")
    prompt_lines.append(f"Key focus: {task_hint}")
    if mode == "sprint-hand-off":
        prompt_lines.append("Start a new task in the same sprint using the context above.")
    else:
        prompt_lines.append("Resume the same task using the latest context block.")
    prompt_text = "\n".join(prompt_lines)

    lines.append("## Kickoff Prompt")
    lines.append("```text")
    lines.append(prompt_text)
    lines.append("```")
    lines.append("")

    metadata_for_index = {
        "summary_id": summary_id,
        "workstream": workstream,
        "mode": mode,
        "task_ref": task_ref,
        "task_hint": task_hint,
        "next_hint": next_hint,
    }
    return "\n".join(lines), prompt_text, metadata_for_index


def _collapse_content(chunks: list[dict[str, Any]]) -> str:
    return collapse_content(chunks)


def _extract_user_messages(entries: list[dict[str, Any]]) -> list[str]:
    messages: list[str] = []
    for entry in entries:
        if entry.get("type") != "response_item":
            continue
        payload = entry.get("payload") or {}
        if payload.get("type") != "message":
            continue
        if payload.get("role") != "user":
            continue
        content = payload.get("content") or []
        if not isinstance(content, list):
            continue
        text = _collapse_content(content)
        if text:
            messages.append(text)
    return messages


def render_skip_codex_summary(
    *, metadata: SessionMetadata, entries: list[dict[str, Any]], generated_at: datetime
) -> str:
    date = generated_at.astimezone(timezone.utc).date().isoformat()
    user_messages = _extract_user_messages(entries)

    lines: list[str] = []
    lines.append("---")
    lines.append(f"title: Session Summary ({metadata.session_id or 'unknown'})")
    lines.append("type: session-summary")
    lines.append(f"date: {date}")
    lines.append("tags: [sessions, summary]")
    lines.append("links: []")
    lines.append("---")
    lines.append("")
    lines.append("# Session Summary")
    lines.append("")
    lines.append("## Session Metadata")
    lines.append(f"- session_id: `{metadata.session_id}`")
    lines.append(f"- timestamp: `{metadata.timestamp}`")
    lines.append(f"- cli_version: `{metadata.cli_version}`")
    lines.append(f"- cwd: `{metadata.cwd}`")
    lines.append("")
    lines.append("## User Messages")
    if user_messages:
        for msg in user_messages:
            lines.append("- " + msg.replace("\n", "\n  "))
    else:
        lines.append("- (no user messages found in rollout)")
    lines.append("")
    lines.append("> Generated automatically from the provided rollout log.")
    return "\n".join(lines) + "\n"


def update_manifest(*, manifest_path: Path, entry: dict[str, Any]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {"sessions": []}
    if manifest_path.exists():
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            data = {"sessions": []}

    sessions = [item for item in data.get("sessions", []) if item.get("session_id") != entry.get("session_id")]
    sessions.insert(0, entry)
    data["sessions"] = sessions[:MANIFEST_LIMIT]
    manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def sanitize_slug(value: str | None, fallback: str = "default") -> str:
    if not value:
        return fallback
    slug = "".join(ch.lower() if ch.isalnum() or ch == "-" else "-" for ch in value).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or fallback


def resolve_workstream_identifier(workstream: str | None, metadata: SessionMetadata) -> str:
    if workstream:
        return sanitize_slug(workstream)
    branch = (metadata.git or {}).get("branch") if isinstance(metadata.git, dict) else None
    if branch:
        return sanitize_slug(str(branch))
    if metadata.originator:
        return sanitize_slug(metadata.originator)
    if metadata.source:
        return sanitize_slug(metadata.source)
    return "default"


def build_session_end_identifier(anchor: datetime | None, session_id: str | None, mode: str) -> str:
    anchor = anchor or datetime.now(timezone.utc)
    if anchor.tzinfo is None:
        anchor = anchor.replace(tzinfo=timezone.utc)
    anchor = anchor.astimezone(timezone.utc)
    stamp = anchor.strftime("%Y%m%dT%H%M%S")
    base = session_id or "session"
    return f"{stamp}_{base}_{mode.replace('-', '_')}"


def format_session_end_paths(*, repo_root: Path, workstream: str, summary_id: str, mode: str) -> tuple[Path, Path]:
    base = repo_root / "process" / "sessions" / "session_end" / workstream
    base.mkdir(parents=True, exist_ok=True)
    summary_path = base / f"{summary_id}_{mode}.md"
    prompt_path = base / f"{summary_id}_{mode}.prompt.txt"
    return summary_path, prompt_path


def record_session_end_index(*, repo_root: Path, entry: dict[str, Any]) -> None:
    index_path = repo_root / "process" / "sessions" / "session_end" / "session_end_index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)

    def record_paths_exist(record: dict[str, Any]) -> bool:
        for key in ("summary_path", "prompt_path"):
            raw = record.get(key)
            if not isinstance(raw, str) or not raw.strip():
                return False
            rel = Path(raw)
            if rel.is_absolute():
                return False
            try:
                resolved = (repo_root / rel).resolve()
                resolved.relative_to(repo_root.resolve())
            except Exception:
                return False
            if not resolved.exists():
                return False
        return True

    if not record_paths_exist(entry):
        raise EndSessionError("Refusing to write index entry with missing summary/prompt paths.\n")

    data: dict[str, Any] = {"records": []}
    if index_path.exists():
        try:
            raw = json.loads(index_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and isinstance(raw.get("records"), list):
                data = raw
        except Exception:
            data = {"records": []}

    records: list[Any] = list(data.get("records", []))
    records.insert(0, entry)

    seen: set[tuple[str, str]] = set()
    pruned: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        summary_path = record.get("summary_path")
        prompt_path = record.get("prompt_path")
        if not isinstance(summary_path, str) or not isinstance(prompt_path, str):
            continue
        signature = (summary_path, prompt_path)
        if signature in seen:
            continue
        if not record_paths_exist(record):
            continue
        seen.add(signature)
        pruned.append(record)
        if len(pruned) >= SESSION_END_RECORD_LIMIT:
            break

    data["records"] = pruned
    index_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_session_end_artifacts(
    *,
    repo_root: Path,
    metadata: SessionMetadata,
    mode: str,
    workstream: str | None,
    created_at: datetime,
    summary_relpath: str,
) -> tuple[Path, Path]:
    resolved_workstream = resolve_workstream_identifier(workstream, metadata)
    summary_id = build_session_end_identifier(created_at, metadata.session_id, mode)
    summary_path, prompt_path = format_session_end_paths(
        repo_root=repo_root,
        workstream=resolved_workstream,
        summary_id=summary_id,
        mode=mode,
    )

    date = created_at.astimezone(timezone.utc).date().isoformat()
    lines: list[str] = []
    lines.append("---")
    lines.append(f"title: Session-End Recap ({mode})")
    lines.append("type: session-end")
    lines.append(f"date: {date}")
    lines.append("tags: [sessions, session-end]")
    lines.append("links: []")
    lines.append("---")
    lines.append("")
    lines.append(f"# Session-End Recap ({mode})")
    lines.append(f"- Workstream: `{resolved_workstream}`")
    lines.append(f"- Session: `{metadata.session_id}`")
    lines.append(f"- Summary Path: `{summary_relpath}`")
    lines.append("")

    prompt_text = f"Workstream '{resolved_workstream}' session recap ({mode}).\nReview {summary_relpath} for context.\n"
    lines.append("## Kickoff Prompt")
    lines.append("```text")
    lines.append(prompt_text.strip())
    lines.append("```")
    lines.append("")

    session_end_text = "\n".join(lines) + "\n"
    summary_path.write_text(session_end_text, encoding="utf-8")
    prompt_path.write_text(prompt_text, encoding="utf-8")

    index_entry = {
        "summary_id": summary_id,
        "workstream": resolved_workstream,
        "mode": mode,
        "session_id": metadata.session_id,
        "summary_path": str(summary_path.relative_to(repo_root)),
        "prompt_path": str(prompt_path.relative_to(repo_root)),
        "created_at": created_at.astimezone(timezone.utc).isoformat(),
        "codex_enriched": False,
    }
    record_session_end_index(repo_root=repo_root, entry=index_entry)

    return summary_path, prompt_path


def chunk_text_blocks(text: str, chunk_size: int, overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    if overlap >= chunk_size:
        overlap = chunk_size // 4
    chunks: list[str] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        chunks.append(text[start:end])
        if end >= length:
            break
        start = max(0, end - overlap)
    return chunks


def codex_available() -> bool:
    return shutil.which("codex") is not None


def build_codex_cli_args(model: str | None, overrides: dict[str, str] | None = None) -> list[str]:
    args: list[str] = []
    if model:
        args.extend(["--model", model])
    for key, value in (overrides or {}).items():
        flag = CODEX_OVERRIDE_FLAG_MAP.get(key)
        if not flag or not value:
            continue
        args.extend([flag, value])
    return args


def run_codex_prompt(
    *, prompt: str, ph_root: Path, model: str | None = None, overrides: dict[str, str] | None = None
) -> str:
    codex_path = shutil.which("codex")
    if not codex_path:
        raise EndSessionError("codex CLI not found on PATH.\nRemediation: install @openai/codex or use --skip-codex.\n")

    with tempfile.NamedTemporaryFile(delete=False) as handle:
        output_path = Path(handle.name)

    cmd = [
        codex_path,
        "exec",
        "--sandbox",
        "read-only",
        "--cd",
        str(ph_root),
        "--output-last-message",
        str(output_path),
    ]
    cmd.extend(build_codex_cli_args(model, overrides))
    cmd.append("-")

    result = subprocess.run(cmd, input=prompt, text=True, capture_output=True, cwd=ph_root)
    if result.returncode != 0:
        stderr = result.stderr.strip() or "Unknown codex error"
        fallback_text = None
        if output_path.exists():
            try:
                fallback_text = output_path.read_text(encoding="utf-8").strip()
            except Exception:
                fallback_text = None
        output_path.unlink(missing_ok=True)
        if fallback_text:
            return fallback_text
        raise EndSessionError(stderr + "\n")

    try:
        content = output_path.read_text(encoding="utf-8").strip()
    finally:
        output_path.unlink(missing_ok=True)
    return content or "(Codex returned an empty response.)"


def summarize_with_codex(
    *,
    ph_root: Path,
    transcript: str,
    model: str | None,
    overrides: dict[str, str] | None,
    chunk_size: int = 4000,
    chunk_overlap: int = 200,
) -> tuple[str, list[str]]:
    if not codex_available():
        raise EndSessionError("codex CLI not found; use --skip-codex.\n")
    chunks = chunk_text_blocks(transcript, chunk_size, chunk_overlap)
    if not chunks:
        return ("(No transcript data available for Codex compression.)", [])

    chunk_outputs: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        prompt = HEADLESS_PROMPT_TEMPLATE.format(index=index, total=len(chunks), chunk=chunk)
        chunk_outputs.append(run_codex_prompt(prompt=prompt, ph_root=ph_root, model=model, overrides=overrides))

    merged_lines: list[str] = []
    seen: set[str] = set()
    for output in chunk_outputs:
        for line in output.splitlines():
            cleaned = line.strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            merged_lines.append(cleaned)

    merged = "\n".join(merged_lines).strip() or "(Codex did not return any usable summary text.)"
    return merged, chunk_outputs


@dataclass(frozen=True)
class EndSessionResult:
    summary_path: Path
    latest_path: Path
    manifest_path: Path
    session_end_summary_path: Path | None = None
    session_end_prompt_path: Path | None = None


def run_end_session_skip_codex(
    *,
    ph_root: Path,
    log_path: Path,
    force: bool = False,
    session_end_mode: str = "none",
    workstream: str | None = None,
    task_ref: str | None = None,
) -> EndSessionResult:
    repo_root = resolve_repo_root(ph_root=ph_root)
    logs_dir = repo_root / "process" / "sessions" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    parser = CodexRolloutParser(repo_root)
    metadata = parser.read_session_meta(log_path)
    if metadata is None:
        raise EndSessionError(f"[session-summary] Unable to parse provided log {log_path}\n")
    if metadata.cwd and not is_within_repo(repo_root, metadata.cwd):
        if not force:
            raise EndSessionError("[session-summary] Provided log was not recorded inside this repository.\n")
        print(
            "[session-summary] Warning: forcing summary generation for log outside repo root.\n"
            f"  log cwd: {metadata.cwd}\n  repo root: {repo_root}",
            file=sys.stderr,
        )

    try:
        metadata, entries = parser.parse(log_path)
    except RolloutParserError as exc:
        raise EndSessionError(str(exc) + "\n") from exc
    if not entries:
        raise EndSessionError(f"[session-summary] Log {log_path} contained no entries.\n")

    history_log = repo_root / ".project-handbook" / "history.log"
    history_entries = read_history_entries(history_log)

    start_utc, end_utc = compute_log_bounds(entries)
    if start_utc is None:
        start_utc = timestamp_from_filename(log_path) or datetime.now(timezone.utc)
    if start_utc.tzinfo is None:
        start_utc = start_utc.replace(tzinfo=timezone.utc)
    if end_utc is None:
        end_utc = start_utc
    if end_utc.tzinfo is None:
        end_utc = end_utc.replace(tzinfo=timezone.utc)

    command_timeline = build_command_timeline(entries)
    summary_events = build_summary_events_from_timeline(command_timeline)
    pruned_transcript = build_pruned_transcript(summary_events)
    if not pruned_transcript:
        pruned_transcript = build_normalized_blocks(entries)
    chapters = build_chapters_from_events(summary_events)

    scoped_history = filter_history_window(
        history_entries,
        to_local_naive(start_utc),
        to_local_naive(end_utc),
    )
    status_lines, status_truncated = read_status_snapshot(repo_root / "status" / "current_summary.md")

    codex_highlights = "(Codex compression skipped by --skip-codex.)"
    summary = render_summary(
        entries,
        codex_highlights,
        [],
        scoped_history,
        status_lines,
        status_truncated,
        pruned_transcript,
        command_timeline,
        chapters,
    )

    summary_path = format_summary_path(logs_dir, start_utc, metadata.session_id)
    latest_path = logs_dir / "latest_summary.md"
    manifest_path = logs_dir / "manifest.json"
    summary_path.write_text(summary + "\n", encoding="utf-8")
    latest_path.write_text(summary + "\n", encoding="utf-8")

    generated_at = datetime.now(timezone.utc).isoformat()
    entry = metadata.to_manifest_entry(
        repo_root,
        summary_path.relative_to(repo_root),
        log_path,
        generated_at,
    )
    update_manifest(manifest_path=manifest_path, entry=entry)

    print(f"[session-summary] Wrote {summary_path}")
    if history_log.exists() and history_log.stat().st_mtime > summary_path.stat().st_mtime:
        print("[session-summary] Warning: history log updated after summary generation; consider re-running soon.")

    session_end_summary_path = None
    session_end_prompt_path = None
    if session_end_mode != "none":
        resolved_workstream = resolve_workstream_identifier(workstream, metadata)
        summary_id = build_session_end_identifier(start_utc, metadata.session_id, session_end_mode)
        session_end_summary_path, session_end_prompt_path = format_session_end_paths(
            repo_root=repo_root,
            workstream=resolved_workstream,
            summary_id=summary_id,
            mode=session_end_mode,
        )
        summary_rel = str(session_end_summary_path.relative_to(repo_root))
        session_end_text, prompt_text, extra_meta = build_session_end_documents(
            mode=session_end_mode,
            metadata=metadata,
            summary_events=summary_events,
            workstream=resolved_workstream,
            task_ref=task_ref,
            start_utc=start_utc,
            end_utc=end_utc,
            summary_relpath=summary_rel,
            summary_id=summary_id,
            repo_root=repo_root,
        )
        session_end_summary_path.write_text(session_end_text + "\n", encoding="utf-8")
        session_end_prompt_path.write_text(prompt_text + "\n", encoding="utf-8")
        created_at = datetime.now(timezone.utc).isoformat()
        branch = metadata.git.get("branch") if metadata.git else None
        index_entry = {
            **extra_meta,
            "codex_enriched": False,
            "session_id": metadata.session_id,
            "branch": branch,
            "summary_path": summary_rel,
            "prompt_path": str(session_end_prompt_path.relative_to(repo_root)),
            "created_at": created_at,
        }
        record_session_end_index(repo_root=repo_root, entry={k: v for k, v in index_entry.items() if v is not None})
        print(f"[session-end] Wrote {session_end_summary_path}")
        print("[session-end] Prompt snippet:\n" + prompt_text)

    return EndSessionResult(
        summary_path=summary_path,
        latest_path=latest_path,
        manifest_path=manifest_path,
        session_end_summary_path=session_end_summary_path,
        session_end_prompt_path=session_end_prompt_path,
    )


def run_end_session_codex(
    *,
    ph_root: Path,
    log_path: Path,
    model: str | None,
    overrides: dict[str, str] | None,
    force: bool = False,
    session_end_mode: str = "none",
    workstream: str | None = None,
    task_ref: str | None = None,
) -> EndSessionResult:
    repo_root = resolve_repo_root(ph_root=ph_root)
    logs_dir = repo_root / "process" / "sessions" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    parser = CodexRolloutParser(repo_root)
    metadata = parser.read_session_meta(log_path)
    if metadata is None:
        raise EndSessionError(f"[session-summary] Unable to parse provided log {log_path}\n")
    if metadata.cwd and not is_within_repo(repo_root, metadata.cwd):
        if not force:
            raise EndSessionError("[session-summary] Provided log was not recorded inside this repository.\n")
        print(
            "[session-summary] Warning: forcing summary generation for log outside repo root.\n"
            f"  log cwd: {metadata.cwd}\n  repo root: {repo_root}",
            file=sys.stderr,
        )

    try:
        metadata, entries = parser.parse(log_path)
    except RolloutParserError as exc:
        raise EndSessionError(str(exc) + "\n") from exc
    if not entries:
        raise EndSessionError(f"[session-summary] Log {log_path} contained no entries.\n")

    history_log = repo_root / ".project-handbook" / "history.log"
    history_entries = read_history_entries(history_log)

    start_utc, end_utc = compute_log_bounds(entries)
    if start_utc is None:
        start_utc = timestamp_from_filename(log_path) or datetime.now(timezone.utc)
    if start_utc.tzinfo is None:
        start_utc = start_utc.replace(tzinfo=timezone.utc)
    if end_utc is None:
        end_utc = start_utc
    if end_utc.tzinfo is None:
        end_utc = end_utc.replace(tzinfo=timezone.utc)

    transcript_lines: list[str] = []
    for entry in entries:
        if entry.get("type") != "response_item":
            continue
        payload = entry.get("payload") or {}
        if payload.get("type") != "message":
            continue
        role = payload.get("role") or "unknown"
        content = payload.get("content") or []
        if not isinstance(content, list):
            continue
        text = _collapse_content(content)
        if not text:
            continue
        transcript_lines.append(f"{role}: {text}")
    transcript = "\n\n".join(transcript_lines)

    codex_highlights, chunk_outputs = summarize_with_codex(
        ph_root=ph_root,
        transcript=transcript,
        model=model,
        overrides=overrides,
    )

    command_timeline = build_command_timeline(entries)
    summary_events = build_summary_events_from_timeline(command_timeline)
    pruned_transcript = build_pruned_transcript(summary_events)
    if not pruned_transcript:
        pruned_transcript = build_normalized_blocks(entries)
    chapters = build_chapters_from_events(summary_events)

    scoped_history = filter_history_window(
        history_entries,
        to_local_naive(start_utc),
        to_local_naive(end_utc),
    )
    status_lines, status_truncated = read_status_snapshot(repo_root / "status" / "current_summary.md")

    summary = render_summary(
        entries,
        codex_highlights,
        chunk_outputs,
        scoped_history,
        status_lines,
        status_truncated,
        pruned_transcript,
        command_timeline,
        chapters,
    )

    summary_path = format_summary_path(logs_dir, start_utc, metadata.session_id)
    latest_path = logs_dir / "latest_summary.md"
    manifest_path = logs_dir / "manifest.json"
    summary_path.write_text(summary + "\n", encoding="utf-8")
    latest_path.write_text(summary + "\n", encoding="utf-8")

    generated_at = datetime.now(timezone.utc).isoformat()
    entry = metadata.to_manifest_entry(
        repo_root,
        summary_path.relative_to(repo_root),
        log_path,
        generated_at,
    )
    update_manifest(manifest_path=manifest_path, entry=entry)

    print(f"[session-summary] Wrote {summary_path}")
    if history_log.exists() and history_log.stat().st_mtime > summary_path.stat().st_mtime:
        print("[session-summary] Warning: history log updated after summary generation; consider re-running soon.")

    session_end_summary_path = None
    session_end_prompt_path = None
    if session_end_mode != "none":
        resolved_workstream = resolve_workstream_identifier(workstream, metadata)
        summary_id = build_session_end_identifier(start_utc, metadata.session_id, session_end_mode)
        session_end_summary_path, session_end_prompt_path = format_session_end_paths(
            repo_root=repo_root,
            workstream=resolved_workstream,
            summary_id=summary_id,
            mode=session_end_mode,
        )
        summary_rel = str(session_end_summary_path.relative_to(repo_root))
        session_end_text, prompt_text, extra_meta = build_session_end_documents(
            mode=session_end_mode,
            metadata=metadata,
            summary_events=summary_events,
            workstream=resolved_workstream,
            task_ref=task_ref,
            start_utc=start_utc,
            end_utc=end_utc,
            summary_relpath=summary_rel,
            summary_id=summary_id,
            repo_root=repo_root,
        )
        session_end_summary_path.write_text(session_end_text + "\n", encoding="utf-8")
        session_end_prompt_path.write_text(prompt_text + "\n", encoding="utf-8")
        created_at = datetime.now(timezone.utc).isoformat()
        branch = metadata.git.get("branch") if metadata.git else None
        index_entry = {
            **extra_meta,
            "codex_enriched": False,
            "session_id": metadata.session_id,
            "branch": branch,
            "summary_path": summary_rel,
            "prompt_path": str(session_end_prompt_path.relative_to(repo_root)),
            "created_at": created_at,
        }
        record_session_end_index(repo_root=repo_root, entry={k: v for k, v in index_entry.items() if v is not None})
        print(f"[session-end] Wrote {session_end_summary_path}")
        print("[session-end] Prompt snippet:\n" + prompt_text)

    return EndSessionResult(
        summary_path=summary_path,
        latest_path=latest_path,
        manifest_path=manifest_path,
        session_end_summary_path=session_end_summary_path,
        session_end_prompt_path=session_end_prompt_path,
    )
