#!/usr/bin/env python3
"""Compute cyclic Contextuality-by-Default summaries for RA-15 pilot outputs.

The original RA-15 pilot reported a probability-drift residual score as ``cntx``.
This script now also reports the canonical cyclic-binary CbD degree, which uses
expectation-scale disturbance and the standard one-half normalization.
"""

from __future__ import annotations

import argparse
import json
import math
from itertools import product
from pathlib import Path
from statistics import mean
from typing import Any

from validate_outputs import extract_json_object, validate_record


VALUE_MAP = {
    "q1": {
        "clear_to_continue": 1,
        "hold_for_review": -1,
        "action_permitted_in_principle": 1,
        "action_not_permitted_in_principle": -1,
    },
    "q2": {"high_risk": 1, "not_high_risk": -1},
    "q3": {"escalate": 1, "no_escalate": -1},
    "q4": {
        "sufficient": 1,
        "insufficient": -1,
        "evidence_ready_for_action": 1,
        "evidence_not_ready_for_action": -1,
        "evidence_packet_ready": 1,
        "evidence_packet_not_ready": -1,
    },
}

CONTEXT_PAIRS = {
    "C1": ("q1", "q2"),
    "C2": ("q2", "q3"),
    "C3": ("q3", "q4"),
    "C4": ("q4", "q1"),
}

CONNECTIONS = {
    "q1": ("C1", "C4"),
    "q2": ("C1", "C2"),
    "q3": ("C2", "C3"),
    "q4": ("C3", "C4"),
}


def base_context_id(context_id: str) -> str:
    """Map conflict contexts C1X-C4X onto the cyclic C1-C4 structure."""
    return context_id[:-1] if context_id.endswith("X") else context_id


def load_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("error"):
                continue
            errors = validate_record(record, line_no)
            if errors:
                raise ValueError(f"Invalid record on line {line_no}: {errors}")
            response, _ = extract_json_object(record["response"])
            assert response is not None
            record["_parsed_response"] = response
            records.append(record)
    return records


def positive_probability(records: list[dict[str, Any]], q_field: str) -> float:
    values = [record["_parsed_response"][q_field] for record in records]
    positives = sum(1 for value in values if VALUE_MAP[q_field][value] == 1)
    return positives / len(values)


def binary_entropy(probability: float) -> float:
    if probability <= 0.0 or probability >= 1.0:
        return 0.0
    return -(
        probability * math.log2(probability)
        + (1.0 - probability) * math.log2(1.0 - probability)
    )


def context_correlation(records: list[dict[str, Any]], context_id: str) -> float:
    q_a, q_b = CONTEXT_PAIRS[base_context_id(context_id)]
    products = []
    for record in records:
        response = record["_parsed_response"]
        products.append(VALUE_MAP[q_a][response[q_a]] * VALUE_MAP[q_b][response[q_b]])
    return mean(products)


def s_odd(correlations: list[float]) -> float:
    candidates = []
    for signs in product((-1, 1), repeat=len(correlations)):
        if signs.count(-1) % 2 == 1:
            candidates.append(sum(sign * corr for sign, corr in zip(signs, correlations)))
    return max(candidates)


def summarize_group(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_context: dict[str, list[dict[str, Any]]] = {context: [] for context in CONTEXT_PAIRS}
    for record in records:
        context_id = base_context_id(str(record["context_id"]))
        if context_id in by_context:
            by_context[context_id].append(record)

    missing = [context for context, items in by_context.items() if not items]
    if missing:
        raise ValueError(f"Missing contexts: {missing}")
    context_counts = {context: len(items) for context, items in by_context.items()}
    if len(set(context_counts.values())) != 1:
        raise ValueError(f"Uneven context counts: {context_counts}")

    direct_influence: dict[str, float] = {}
    direct_influence_expectation: dict[str, float] = {}
    for q_field, (context_a, context_b) in CONNECTIONS.items():
        p_a = positive_probability(by_context[context_a], q_field)
        p_b = positive_probability(by_context[context_b], q_field)
        direct_influence[q_field] = abs(p_a - p_b)
        direct_influence_expectation[q_field] = 2 * direct_influence[q_field]

    entropy: dict[str, float] = {}
    for context, items in by_context.items():
        for q_field in CONTEXT_PAIRS[context]:
            entropy[f"{context}.{q_field}"] = binary_entropy(
                positive_probability(items, q_field)
            )

    correlations = {
        context: context_correlation(items, context) for context, items in by_context.items()
    }
    ordered_correlations = [correlations[context] for context in ("C1", "C2", "C3", "C4")]
    s_odd_value = s_odd(ordered_correlations)
    di_total = sum(direct_influence.values())
    di_expectation_total = sum(direct_influence_expectation.values())
    cntx_legacy_probability_drift_raw = s_odd_value - 2 - di_total
    cntx_legacy_probability_drift = max(0.0, cntx_legacy_probability_drift_raw)
    cntx_canonical_raw = (s_odd_value - 2 - di_expectation_total) / 2
    cntx_canonical = max(0.0, cntx_canonical_raw)

    q1_values = []
    for context in ("C1", "C4"):
        q1_values.extend(
            VALUE_MAP["q1"][record["_parsed_response"]["q1"]]
            for record in by_context[context]
        )
    max_q1_frequency = max(
        q1_values.count(1) / len(q1_values),
        q1_values.count(-1) / len(q1_values),
    )

    return {
        "n_records": sum(len(items) for items in by_context.values()),
        "context_counts": context_counts,
        "direct_influence": direct_influence,
        "direct_influence_probability": direct_influence,
        "direct_influence_expectation": direct_influence_expectation,
        "di_total": di_total,
        "di_probability_total": di_total,
        "di_expectation_total": di_expectation_total,
        "correlations": correlations,
        "s_odd": s_odd_value,
        "cntx_legacy_probability_drift_raw": cntx_legacy_probability_drift_raw,
        "cntx_legacy_probability_drift": cntx_legacy_probability_drift,
        "cntx_raw": cntx_canonical_raw,
        "cntx": cntx_canonical,
        "cntx_canonical_raw": cntx_canonical_raw,
        "cntx_canonical": cntx_canonical,
        "entropy": entropy,
        "h_mean": mean(entropy.values()),
        "q1_instability": 1 - max_q1_frequency,
    }


def group_metadata(records: list[dict[str, Any]]) -> dict[str, Any]:
    fields = ["industry", "problem_class", "conflict_band", "predicted_strategy"]
    metadata: dict[str, Any] = {}
    for field in fields:
        values = sorted({record[field] for record in records if field in record})
        if len(values) == 1:
            metadata[field] = values[0]
        elif values:
            metadata[field] = values
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    records = load_records(args.input)
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for record in records:
        key = (str(record["task_id"]), str(record["block"]), str(record["model"]))
        grouped.setdefault(key, []).append(record)

    summary: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for (task_id, block, model), group_records in sorted(grouped.items()):
        try:
            item = {
                "task_id": task_id,
                "block": block,
                "model": model,
                **group_metadata(group_records),
                **summarize_group(group_records),
            }
            summary.append(item)
        except ValueError as exc:
            skipped.append(
                {
                    "task_id": task_id,
                    "block": block,
                    "model": model,
                    "n_records": len(group_records),
                    "reason": str(exc),
                }
            )

    payload = {"input": str(args.input), "groups": summary, "skipped_incomplete": skipped}
    text = json.dumps(payload, indent=2)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
