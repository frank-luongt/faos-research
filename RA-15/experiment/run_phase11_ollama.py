#!/usr/bin/env python3
"""Run RA-15 Phase 1.1 q4-robustness prompts against local Ollama."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
from pathlib import Path
from typing import Any

from render_phase1_prompts import DEFAULT_REPS
from render_phase11_prompts import build_records
from run_phase0_ollama import DEFAULT_MODEL, call_ollama


def record_key(record: dict[str, Any]) -> tuple[str, str, str, int]:
    return (
        str(record["task_id"]),
        str(record["block"]),
        str(record["context_id"]),
        int(record["rep"]),
    )


def load_completed(path: Path) -> set[tuple[str, str, str, int]]:
    if not path.exists():
        return set()
    completed: set[tuple[str, str, str, int]] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("response") and not record.get("error"):
                completed.add(record_key(record))
    return completed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--reps", type=int, default=DEFAULT_REPS)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--timeout", type=int, default=420)
    parser.add_argument("--sleep", type=float, default=0.0)
    parser.add_argument("--no-json-format", action="store_true")
    parser.add_argument("--restart", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    records = build_records(root, reps=args.reps)
    if args.limit is not None:
        records = records[: args.limit]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    completed = set() if args.restart else load_completed(args.output)
    pending = [record for record in records if record_key(record) not in completed]

    mode = "w" if args.restart else "a"
    written = 0
    with args.output.open(mode, encoding="utf-8") as handle:
        for record in pending:
            started = time.time()
            output_record: dict[str, Any] = {
                "phase": "phase1.1",
                "task_id": record["task_id"],
                "industry": record["industry"],
                "problem_class": record["problem_class"],
                "predicted_strategy": record["predicted_strategy"],
                "conflict_band": record["conflict_band"],
                "block": record["block"],
                "context_id": record["context_id"],
                "rep": record["rep"],
                "model": args.model,
            }
            try:
                content = call_ollama(
                    model=args.model,
                    system_prompt=record["system_prompt"],
                    user_prompt=record["user_prompt"],
                    temperature=args.temperature,
                    timeout=args.timeout,
                    json_format=not args.no_json_format,
                )
                output_record["response"] = content
                output_record["latency_sec"] = round(time.time() - started, 3)
            except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
                output_record["response"] = ""
                output_record["error"] = str(exc)
                output_record["latency_sec"] = round(time.time() - started, 3)
            handle.write(json.dumps(output_record, ensure_ascii=False) + "\n")
            handle.flush()
            written += 1
            done = len(completed) + written
            print(
                json.dumps(
                    {
                        "written_this_run": written,
                        "done": done,
                        "total": len(records),
                        "task_id": output_record["task_id"],
                        "block": output_record["block"],
                        "context_id": output_record["context_id"],
                        "rep": output_record["rep"],
                        "error": output_record.get("error"),
                    }
                )
            )
            if args.sleep:
                time.sleep(args.sleep)

    print(
        json.dumps(
            {
                "output": str(args.output),
                "records_total": len(records),
                "records_previously_completed": len(completed),
                "records_written_this_run": written,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
