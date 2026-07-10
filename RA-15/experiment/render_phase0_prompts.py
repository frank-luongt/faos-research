#!/usr/bin/env python3
"""Render RA-15 Phase 0 smoke-test prompts from the current pilot assets."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


PHASE0_TASKS = ["software_T3", "fintech_T6"]
PHASE0_CONTEXTS = ["C1", "C2", "C3", "C4"]
PHASE0_BLOCK = "canonical"
PHASE0_REPS = 3

LABELS = {
    "q1": (
        "clear_to_continue",
        "hold_for_review",
        "business-continuity posture",
    ),
    "q2": ("high_risk", "not_high_risk", "risk severity"),
    "q3": ("escalate", "no_escalate", "formal escalation"),
    "q4": ("sufficient", "insufficient", "evidence sufficiency"),
}

SYSTEM_PROMPT = """You are an enterprise decision reviewer participating in a measurement study.

Follow the requested role frame, task, and ontology/policy context. Return JSON only.
Do not include markdown, chain-of-thought, hidden reasoning, or any keys not requested.
Use only the allowed labels for each measured content.
The rationale must be one short paragraph of 60 words or fewer."""


def load_ra1_tasks(path: Path) -> dict[str, dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        tasks = json.load(handle)
    return {task["id"]: task for task in tasks}


def load_contexts(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {row["context_id"]: row for row in rows}


def load_snippets(path: Path) -> dict[tuple[str, str], str]:
    snippets: dict[tuple[str, str], str] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            snippets[(row["task_id"], row["block"])] = row["snippet"]
    return snippets


def measured_fields(context_row: dict[str, str]) -> list[str]:
    return [item.strip() for item in context_row["measured_contents"].split(",")]


def label_block(fields: list[str]) -> str:
    lines = []
    for field in fields:
        positive, negative, meaning = LABELS[field]
        lines.append(f"- {field} ({meaning}): {positive} or {negative}")
    return "\n".join(lines)


def schema_for(fields: list[str]) -> str:
    schema = {field: "|".join(LABELS[field][:2]) for field in fields}
    schema["rationale"] = "one short paragraph"
    return json.dumps(schema, indent=2)


def render_user_prompt(
    *,
    task: dict[str, Any],
    context: dict[str, str],
    snippet: str,
    fields: list[str],
) -> str:
    return f"""Role frame:
{context["role_frame"]}

Task:
{task["question"]}

Ontology/policy context:
{snippet}

Measurement context:
{context["context_id"]} measures exactly these contents in this order:
{", ".join(fields)}

Allowed labels:
{label_block(fields)}

Output schema:
{schema_for(fields)}

Return JSON only. Include exactly the measured q fields plus rationale.
Do not include unmeasured q fields."""


def build_records(root: Path) -> list[dict[str, Any]]:
    tasks = load_ra1_tasks(root / "../RA-1-coordination/tasks_ra1.json")
    contexts = load_contexts(root / "context_matrix_v0.csv")
    snippets = load_snippets(root / "ontology_snippets_v0.jsonl")

    records: list[dict[str, Any]] = []
    for task_id in PHASE0_TASKS:
        task = tasks[task_id]
        snippet = snippets[(task_id, PHASE0_BLOCK)]
        for context_id in PHASE0_CONTEXTS:
            context = contexts[context_id]
            fields = measured_fields(context)
            user_prompt = render_user_prompt(
                task=task,
                context=context,
                snippet=snippet,
                fields=fields,
            )
            for rep in range(1, PHASE0_REPS + 1):
                records.append(
                    {
                        "task_id": task_id,
                        "block": PHASE0_BLOCK,
                        "context_id": context_id,
                        "rep": rep,
                        "system_prompt": SYSTEM_PROMPT,
                        "user_prompt": user_prompt,
                    }
                )
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSONL output path. If omitted, records are printed to stdout.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    records = build_records(root)

    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    if args.output:
        args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(json.dumps({"output": str(args.output), "records": len(records)}, indent=2))
    else:
        for line in lines:
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
