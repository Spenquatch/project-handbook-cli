from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .rollout_parser import CodexRolloutParser, RolloutParserError, SessionMetadata

MANIFEST_LIMIT = 5
SESSION_END_RECORD_LIMIT = 200

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


def _collapse_content(chunks: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for chunk in chunks:
        chunk_type = chunk.get("type")
        if chunk_type in {"input_text", "output_text"}:
            text = chunk.get("text", "")
            if text:
                parts.append(str(text))
    return "\n".join(parts).strip()


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


def build_session_end_identifier(anchor: datetime, session_id: str | None, mode: str) -> str:
    anchor = anchor.astimezone(timezone.utc)
    stamp = anchor.strftime("%Y%m%dT%H%M%S")
    base = session_id or "session"
    return f"{stamp}_{base}_{mode.replace('-', '_')}"


def format_session_end_paths(*, ph_root: Path, workstream: str, summary_id: str, mode: str) -> tuple[Path, Path]:
    base = ph_root / "process" / "sessions" / "session_end" / workstream
    base.mkdir(parents=True, exist_ok=True)
    summary_path = base / f"{summary_id}_{mode}.md"
    prompt_path = base / f"{summary_id}_{mode}.prompt.txt"
    return summary_path, prompt_path


def record_session_end_index(*, ph_root: Path, entry: dict[str, Any]) -> None:
    index_path = ph_root / "process" / "sessions" / "session_end" / "session_end_index.json"
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
                resolved = (ph_root / rel).resolve()
                resolved.relative_to(ph_root.resolve())
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
    ph_root: Path,
    metadata: SessionMetadata,
    mode: str,
    workstream: str | None,
    created_at: datetime,
    summary_relpath: str,
) -> tuple[Path, Path]:
    resolved_workstream = resolve_workstream_identifier(workstream, metadata)
    summary_id = build_session_end_identifier(created_at, metadata.session_id, mode)
    summary_path, prompt_path = format_session_end_paths(
        ph_root=ph_root,
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
        "summary_path": str(summary_path.relative_to(ph_root)),
        "prompt_path": str(prompt_path.relative_to(ph_root)),
        "created_at": created_at.astimezone(timezone.utc).isoformat(),
        "codex_enriched": False,
    }
    record_session_end_index(ph_root=ph_root, entry=index_entry)

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
    session_end_mode: str = "none",
    workstream: str | None = None,
) -> EndSessionResult:
    logs_dir = ph_root / "process" / "sessions" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    parser = CodexRolloutParser(ph_root)
    try:
        metadata, entries = parser.parse(log_path)
    except RolloutParserError as exc:
        raise EndSessionError(str(exc) + "\n") from exc

    now = datetime.now(timezone.utc)
    summary_filename = now.strftime("%Y-%m-%d_%H%M_summary.md")
    summary_path = logs_dir / summary_filename
    latest_path = logs_dir / "latest_summary.md"
    manifest_path = logs_dir / "manifest.json"

    summary = render_skip_codex_summary(metadata=metadata, entries=entries, generated_at=now)
    summary_path.write_text(summary, encoding="utf-8")
    latest_path.write_text(summary, encoding="utf-8")

    entry = metadata.to_manifest_entry(
        ph_root.resolve(),
        summary_path.relative_to(ph_root.resolve()),
        log_path,
        now.isoformat(),
    )
    update_manifest(manifest_path=manifest_path, entry=entry)

    session_end_summary_path = None
    session_end_prompt_path = None
    if session_end_mode != "none":
        session_end_summary_path, session_end_prompt_path = write_session_end_artifacts(
            ph_root=ph_root,
            metadata=metadata,
            mode=session_end_mode,
            workstream=workstream,
            created_at=now,
            summary_relpath=str(summary_path.relative_to(ph_root)),
        )

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
    session_end_mode: str = "none",
    workstream: str | None = None,
) -> EndSessionResult:
    logs_dir = ph_root / "process" / "sessions" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    parser = CodexRolloutParser(ph_root)
    try:
        metadata, entries = parser.parse(log_path)
    except RolloutParserError as exc:
        raise EndSessionError(str(exc) + "\n") from exc

    now = datetime.now(timezone.utc)
    summary_filename = now.strftime("%Y-%m-%d_%H%M_summary.md")
    summary_path = logs_dir / summary_filename
    latest_path = logs_dir / "latest_summary.md"
    manifest_path = logs_dir / "manifest.json"

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

    codex_highlights, _chunk_outputs = summarize_with_codex(
        ph_root=ph_root,
        transcript=transcript,
        model=model,
        overrides=overrides,
    )

    summary = render_skip_codex_summary(metadata=metadata, entries=entries, generated_at=now)
    summary += "\n## Headless Codex Summary\n\n" + codex_highlights.strip() + "\n"

    summary_path.write_text(summary, encoding="utf-8")
    latest_path.write_text(summary, encoding="utf-8")

    entry = metadata.to_manifest_entry(
        ph_root.resolve(),
        summary_path.relative_to(ph_root.resolve()),
        log_path,
        now.isoformat(),
    )
    update_manifest(manifest_path=manifest_path, entry=entry)

    session_end_summary_path = None
    session_end_prompt_path = None
    if session_end_mode != "none":
        session_end_summary_path, session_end_prompt_path = write_session_end_artifacts(
            ph_root=ph_root,
            metadata=metadata,
            mode=session_end_mode,
            workstream=workstream,
            created_at=now,
            summary_relpath=str(summary_path.relative_to(ph_root)),
        )

    return EndSessionResult(
        summary_path=summary_path,
        latest_path=latest_path,
        manifest_path=manifest_path,
        session_end_summary_path=session_end_summary_path,
        session_end_prompt_path=session_end_prompt_path,
    )
