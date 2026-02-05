from __future__ import annotations

import datetime as dt
import os


def today(*, env: dict[str, str] | None = None) -> dt.date:
    env = env or os.environ
    raw = (env.get("PH_FAKE_TODAY") or "").strip()
    if raw:
        return dt.date.fromisoformat(raw)
    return dt.date.today()


def now(*, env: dict[str, str] | None = None) -> dt.datetime:
    env = env or os.environ
    raw = (env.get("PH_FAKE_NOW") or "").strip()
    if raw:
        text = raw.replace("Z", "+00:00")
        parsed = dt.datetime.fromisoformat(text)
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(dt.timezone.utc).replace(tzinfo=None)
        return parsed
    return dt.datetime.now()


def local_today_from_now(*, env: dict[str, str] | None = None) -> dt.date:
    """
    Legacy parity helper.

    Some legacy scripts compute "today" via dt.date.today() (local timezone) but
    record timestamps in UTC. When PH_FAKE_NOW is provided, derive the local date
    for that instant so callers can deterministically match legacy output.
    """
    env = env or os.environ
    raw = (env.get("PH_FAKE_NOW") or "").strip()
    if raw:
        text = raw.replace("Z", "+00:00")
        parsed = dt.datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        local_tz = dt.datetime.now().astimezone().tzinfo or dt.timezone.utc
        return parsed.astimezone(local_tz).date()
    return dt.date.today()
