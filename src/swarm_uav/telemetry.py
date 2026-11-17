"""Append-only JSON Lines telemetry logging and replay helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def write_event(path: Path, event_type: str, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "data": data,
    }
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, separators=(",", ":"), allow_nan=False) + "\n")


def read_events(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"invalid JSON on line {line_number}: {error.msg}") from error
            if not isinstance(event, dict) or not {"timestamp", "event_type", "data"} <= event.keys():
                raise ValueError(f"invalid event structure on line {line_number}")
            yield event


def replay_summary(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    first_timestamp = None
    last_timestamp = None
    total = 0
    for event in events:
        total += 1
        first_timestamp = first_timestamp or event["timestamp"]
        last_timestamp = event["timestamp"]
        kind = event["event_type"]
        counts[kind] = counts.get(kind, 0) + 1
    return {"events": total, "by_type": counts, "first_timestamp": first_timestamp, "last_timestamp": last_timestamp}
