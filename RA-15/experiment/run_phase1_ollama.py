#!/usr/bin/env python3
"""Run RA-15 Phase 1 prompts against a local Ollama chat model with resume support."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
from pathlib import Path
from typing import Any

from render_phase1_prompts import (
    DEFAULT_REPS,
    build_records,
    representative_smoke_records,
)
from run_phase0_ollama import DEFAULT_MODEL, call_ollama


def record_key(record: dict[str, Any], model: str | None = None) -> tuple[str, str, str, int, str]:
    return (
        str(record["task_id"]),
        str(record["block"]),
        str(record["context_id"]),
        int(record["rep"]),
        str(model if model is not None else record["model"]),
    )


def load_completed_keys(path: Path) -> set[tuple[str, str, str, int, str]]:
    if not path.exists():
        return set()

    completed: set[tuple[str, str, str, int, str]] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("error"):
                continue
            required = {"task_id", "block", "context_id", "rep", "model", "response"}
            if required <= set(record) and record.get("response"):
                completed.add(record_key(record))
    return completed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--limit", type=int, help="Optional record limit for debugging")
    parser.add_argument("--reps", type=int, default=DEFAULT_REPS)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--sleep", type=float, default=0.0)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Append to an existing output and skip successfully completed records.",
    )
    parser.add_argument(
        "--restart",
        action="store_true",
        help="Overwrite output instead of resuming completed records.",
    )
    parser.add_argument(
        "--smoke-representative",
        action="store_true",
        help="Run one record for each canonical/conflict context shape.",
    )
    parser.add_argument(
        "--no-json-format",
        action="store_true",
        help="Do not request Ollama format=json; rely on prompt-only JSON instruction.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    records = build_records(root, reps=args.reps)
    if args.smoke_representative:
        records = representative_smoke_records(records)
    if args.limit is not None:
        records = records[: args.limit]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    completed_keys = set() if args.restart else load_completed_keys(args.output)
    pending_records = [
        record for record in records if record_key(record, args.model) not in completed_keys
    ]
    mode = "w" if args.restart else "a"

    written = 0
    with args.output.open(mode, encoding="utf-8") as handle:
        for record in pending_records:
            started = time.time()
            output_record: dict[str, Any] = {
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
            done = len(completed_keys) + written
            print(
                json.dumps(
                    {
                        "written_this_run": written,
                        "done": done,
                        "total": len(records),
                        "pending": len(pending_records),
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
                "records_previously_completed": len(completed_keys),
                "records_written_this_run": written,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
