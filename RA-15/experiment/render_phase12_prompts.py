#!/usr/bin/env python3
"""Render RA-15 Phase 1.2 role/order disentanglement prompts."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from render_phase0_prompts import (
    SYSTEM_PROMPT,
    load_contexts,
    load_ra1_tasks,
    load_snippets,
    measured_fields,
)
from render_phase1_prompts import DEFAULT_REPS
from render_phase11_prompts import LABELS, label_block, schema_for


PHASE12_GROUPS = {
    ("healthcare_T6", "canonical"),
    ("insurance_T6", "canonical"),
    ("insurance_T9", "canonical"),
    ("insurance_T9", "conflict"),
    ("software_T3", "conflict"),
}

CONDITIONS = ("role_fixed", "order_neutral")
FIXED_ROLE = "neutral enterprise decision reviewer"


def load_pilot_tasks(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {row["task_id"]: row for row in csv.DictReader(handle)}


def contexts_for_block(contexts: dict[str, dict[str, str]], block: str) -> list[dict[str, str]]:
    return [row for row in contexts.values() if row["block"] == block]


def render_phase12_user_prompt(
    *,
    task: dict[str, Any],
    context: dict[str, str],
    snippet: str,
    fields: list[str],
    condition: str,
) -> str:
    if condition == "role_fixed":
        role_frame = FIXED_ROLE
        condition_note = (
            "Condition: role_fixed. Use the same neutral reviewer role for every "
            "measurement context. Treat the context identifier only as the pair of "
            "measured contents; do not infer business-action, risk-first, escalation-first, "
            "or evidence-first priority from it."
        )
    elif condition == "order_neutral":
        role_frame = context["role_frame"]
        condition_note = (
            "Condition: order_neutral. Use the requested role frame, but treat the measured "
            "contents as unordered independent labels. Do not infer priority from the order "
            "in which q fields are listed, and do not apply business-action-first, risk-first, "
            "escalation-first, or evidence-first framing."
        )
    else:
        raise ValueError(f"Unknown Phase 1.2 condition: {condition}")

    q4_note = ""
    if "q4" in fields:
        q4_note = (
            "\nFor q4, judge whether the evidence currently available is ready to support "
            "the requested action now. Do not answer broad evidence sufficiency; answer "
            "action-readiness only."
        )

    return f"""Role frame:
{role_frame}

Task:
{task["question"]}

Ontology/policy context:
{snippet}

Measurement context:
{context["context_id"]} measures exactly these contents:
{", ".join(fields)}

{condition_note}
{q4_note}

Allowed labels:
{label_block(fields)}

Output schema:
{schema_for(fields)}

Return JSON only. Include exactly the measured q fields plus rationale.
Do not include unmeasured q fields."""


def build_records(root: Path, reps: int = DEFAULT_REPS) -> list[dict[str, Any]]:
    tasks = load_ra1_tasks(root / "../RA-1-coordination/tasks_ra1.json")
    pilot_tasks = load_pilot_tasks(root / "pilot_tasks_v0.csv")
    contexts = load_contexts(root / "context_matrix_v0.csv")
    snippets = load_snippets(root / "ontology_snippets_v0.jsonl")

    records: list[dict[str, Any]] = []
    for task_id, source_block in sorted(PHASE12_GROUPS):
        task_row = pilot_tasks[task_id]
        task = tasks[task_id]
        snippet = snippets[(task_id, source_block)]
        for condition in CONDITIONS:
            block = f"{source_block}_{condition}"
            for context in contexts_for_block(contexts, source_block):
                fields = measured_fields(context)
                user_prompt = render_phase12_user_prompt(
                    task=task,
                    context=context,
                    snippet=snippet,
                    fields=fields,
                    condition=condition,
                )
                for rep in range(1, reps + 1):
                    records.append(
                        {
                            "phase": "phase1.2",
                            "condition": condition,
                            "source_block": source_block,
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


def validate_freeze(records: list[dict[str, Any]], reps: int) -> dict[str, Any]:
    group_counts: dict[str, int] = {}
    for record in records:
        key = f"{record['task_id']}:{record['block']}"
        group_counts[key] = group_counts.get(key, 0) + 1
    return {
        "phase": "phase1.2",
        "records": len(records),
        "expected_records": len(PHASE12_GROUPS) * len(CONDITIONS) * 4 * reps,
        "conditions": list(CONDITIONS),
        "groups": sorted(group_counts),
        "group_counts": dict(sorted(group_counts.items())),
        "q4_labels": list(LABELS["q4"][:2]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reps", type=int, default=DEFAULT_REPS)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    records = build_records(root, reps=args.reps)
    args.output.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
        encoding="utf-8",
    )
    summary = validate_freeze(records, args.reps)
    if args.summary:
        args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), **summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
