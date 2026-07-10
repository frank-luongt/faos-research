#!/usr/bin/env python3
"""Render RA-15 Phase 1 first-model pilot prompts from frozen pilot assets."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from render_phase0_prompts import (
    LABELS,
    SYSTEM_PROMPT,
    load_contexts,
    load_ra1_tasks,
    load_snippets,
    measured_fields,
    render_user_prompt,
)


DEFAULT_REPS = 12
PHASE1_REPS = DEFAULT_REPS
HIGH_CONFLICT = "high"


def load_pilot_tasks(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def contexts_for_block(contexts: dict[str, dict[str, str]], block: str) -> list[dict[str, str]]:
    return [row for row in contexts.values() if row["block"] == block]


def blocks_for_task(task_row: dict[str, str]) -> list[str]:
    blocks = ["canonical"]
    if task_row["conflict_band"] == HIGH_CONFLICT:
        blocks.append("conflict")
    return blocks


def build_records(root: Path, reps: int = DEFAULT_REPS) -> list[dict[str, Any]]:
    tasks = load_ra1_tasks(root / "../RA-1-coordination/tasks_ra1.json")
    pilot_tasks = load_pilot_tasks(root / "pilot_tasks_v0.csv")
    contexts = load_contexts(root / "context_matrix_v0.csv")
    snippets = load_snippets(root / "ontology_snippets_v0.jsonl")

    records: list[dict[str, Any]] = []
    for task_row in pilot_tasks:
        task_id = task_row["task_id"]
        task = tasks[task_id]
        for block in blocks_for_task(task_row):
            snippet = snippets[(task_id, block)]
            for context in contexts_for_block(contexts, block):
                fields = measured_fields(context)
                user_prompt = render_user_prompt(
                    task=task,
                    context=context,
                    snippet=snippet,
                    fields=fields,
                )
                for rep in range(1, reps + 1):
                    records.append(
                        {
                            "task_id": task_id,
                            "industry": task_row["industry"],
                            "problem_class": task_row["problem_class"],
                            "predicted_strategy": task_row["predicted_strategy"],
                            "conflict_band": task_row["conflict_band"],
                            "block": block,
                            "context_id": context["context_id"],
                            "rep": rep,
                            "system_prompt": SYSTEM_PROMPT,
                            "user_prompt": user_prompt,
                        }
                    )
    return records


def validate_freeze(root: Path, records: list[dict[str, Any]], reps: int) -> dict[str, Any]:
    pilot_tasks = load_pilot_tasks(root / "pilot_tasks_v0.csv")
    high_conflict_task_ids = {
        row["task_id"] for row in pilot_tasks if row["conflict_band"] == HIGH_CONFLICT
    }
    expected_total = (
        (len(pilot_tasks) * 4 * reps) + (len(high_conflict_task_ids) * 4 * reps)
    )
    conflict_task_ids = {
        record["task_id"] for record in records if record["block"] == "conflict"
    }
    canonical_task_ids = {
        record["task_id"] for record in records if record["block"] == "canonical"
    }
    return {
        "records": len(records),
        "expected_records": expected_total,
        "canonical_tasks": sorted(canonical_task_ids),
        "conflict_tasks": sorted(conflict_task_ids),
        "expected_conflict_tasks": sorted(high_conflict_task_ids),
        "conflict_routing_ok": conflict_task_ids == high_conflict_task_ids,
        "q1_labels": list(LABELS["q1"][:2]),
    }


def representative_smoke_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pick a compact slice covering all Phase 1 context/block shapes."""
    smoke: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for record in records:
        key = (record["block"], record["context_id"])
        if key in seen:
            continue
        smoke.append(record)
        seen.add(key)
    return smoke


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSONL output path. If omitted, records are printed to stdout.",
    )
    parser.add_argument("--reps", type=int, default=DEFAULT_REPS)
    parser.add_argument(
        "--summary",
        type=Path,
        help="Optional JSON summary path for freeze verification.",
    )
    parser.add_argument(
        "--smoke-representative",
        action="store_true",
        help="Emit one record for each canonical/conflict context shape.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    records = build_records(root, reps=args.reps)
    if args.smoke_representative:
        records = representative_smoke_records(records)

    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    if args.output:
        args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
        summary = validate_freeze(root, records, args.reps)
        if args.summary:
            args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"output": str(args.output), **summary}, indent=2))
    else:
        for line in lines:
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
