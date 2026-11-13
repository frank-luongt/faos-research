"""Append-only JSONL logs with resume by key."""

import json
from datetime import datetime, timezone
from pathlib import Path


def done_keys(path: Path) -> set[str]:
    if not path.exists():
        return set()
    keys = set()
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                row = json.loads(line)
                if not row.get("error"):
                    keys.add(row["key"])
    return keys


def append(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {**row, "logged_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    with open(path, "a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]
