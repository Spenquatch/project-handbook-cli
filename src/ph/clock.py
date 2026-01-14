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
