#!/usr/bin/env python3
"""Judge deferred RA-1 result rows without regenerating model responses.

This sends task content and model responses to the fixed Sonnet judge. Use only
after explicit approval for external evaluation.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_experiment import append_result, completed_keys, ensure_results_file, env_value, evaluate_response, load_tasks, task_metric


EXPERIMENT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = EXPERIMENT_DIR / "results"
DEFAULT_SOURCE = RESULTS_DIR / "results_raw_qwen_local_single_agent_deferred_2026_05_19.csv"
DEFAULT_OUTPUT = RESULTS_DIR / "results_judged_qwen_local_single_agent_sonnet_2026_05_19.csv"


def load_deferred_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def row_key(row: dict[str, str]) -> tuple[str, str, int, str]:
    return (row["task_id"], row["condition"], int(row["rep"]), row["model_arm"])


def select_rows(rows: list[dict[str, str]], args: argparse.Namespace) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    for row in rows:
        if row.get("error"):
            continue
        if row.get("quality_score"):
            continue
        if not row.get("agent_response"):
            continue
        if args.task and row.get("task_id") != args.task:
            continue
        if args.condition and row.get("condition") != args.condition:
            continue
        selected.append(row)
    if args.limit is not None:
        return selected[: args.limit]
    return selected


def base_row(row: dict[str, str], task: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": row["task_id"],
        "industry": row["industry"],
        "category": row.get("category", ""),
        "problem_class": row["problem_class"],
        "predicted_strategy": row["predicted_strategy"],
        "metric_tested": row.get("metric_tested") or task_metric(task),
        "condition": row["condition"],
        "rep": int(row["rep"]),
        "model_arm": row["model_arm"],
        "provider": row["provider"],
        "model": row["model"],
        "agent_response_len": row.get("agent_response_len") or len(row["agent_response"]),
        "agent_response": row["agent_response"],
        "agent_trace": row.get("agent_trace", "[]"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def assert_judge_config_ready() -> None:
    missing: list[str] = []
    if not env_value("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")
    if importlib.util.find_spec("anthropic") is None:
        missing.append("python package: anthropic")
    if missing:
        raise SystemExit(
            "Fixed Sonnet judge is not configured; missing "
            + ", ".join(missing)
            + ". No rows were judged."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--task")
    parser.add_argument("--condition")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--restart", action="store_true")
    parser.add_argument("--sleep", type=float, default=0.5)
    args = parser.parse_args()

    assert_judge_config_ready()

    if args.restart and args.output.exists():
        args.output.unlink()
    ensure_results_file(args.output)
    completed = completed_keys(args.output) if args.resume else set()

    tasks = {task["id"]: task for task in load_tasks()}
    rows = select_rows(load_deferred_rows(args.source), args)
    print(
        json.dumps(
            {
                "source": str(args.source),
                "output": str(args.output),
                "selected_rows": len(rows),
                "completed_loaded": len(completed),
                "external_judge": "anthropic",
            },
            indent=2,
        )
    )

    written = 0
    skipped = 0
    errors = 0
    for index, row in enumerate(rows, start=1):
        key = row_key(row)
        if key in completed:
            skipped += 1
            continue
        task = tasks.get(row["task_id"])
        if task is None:
            errors += 1
            append_result(
                args.output,
                {
                    **base_row(row, {}),
                    "latency_sec": 0,
                    "error": f"task not found: {row['task_id']}",
                },
            )
            continue

        print(f"[{index}/{len(rows)}] judging {row['task_id']} {row['condition']} rep={row['rep']}", flush=True)
        started = time.time()
        try:
            scores = evaluate_response(task, row["agent_response"])
            append_result(
                args.output,
                {
                    **base_row(row, task),
                    **scores,
                    "latency_sec": round(time.time() - started, 3),
                    "error": "",
                },
            )
            written += 1
            print(f"  score={scores['quality_score']:.3f}", flush=True)
        except Exception as exc:
            errors += 1
            append_result(
                args.output,
                {
                    **base_row(row, task),
                    "judge_detail": json.dumps({"error": str(exc)}),
                    "latency_sec": round(time.time() - started, 3),
                    "error": str(exc),
                },
            )
            print(f"  ERROR {exc}", flush=True)
        if args.sleep:
            time.sleep(args.sleep)

    print(json.dumps({"written": written, "skipped": skipped, "errors": errors, "output": str(args.output)}, indent=2))
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
