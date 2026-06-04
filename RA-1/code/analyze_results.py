#!/usr/bin/env python3
"""Analyze RA-1 coordination result CSVs.

This script is intentionally useful for partial runs. It reports coverage,
mean quality by model/problem class/condition, and a provisional H1 hit table.
The final paper analysis can add formal Friedman/Wilcoxon tests once the full
three-model matrix is available.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


EXPERIMENT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = EXPERIMENT_DIR / "results"
DEFAULT_OUTPUT = RESULTS_DIR / "analysis_summary.json"
CONDITIONS = ("single_agent", "consensus", "debate", "synthesis")
PREDICTED_BY_PC = {
    "PC1": "consensus",
    "PC2": "debate",
    "PC3": "synthesis",
    "PC4": "consensus",
    "PC5": "synthesis",
}


def parse_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("error"):
                    continue
                score = parse_float(row.get("quality_score", ""))
                if score is None:
                    continue
                row["quality_score"] = score
                rows.append(row)
    return rows


def summarize_unjudged(paths: list[Path]) -> dict[str, Any]:
    generated: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    judged_keys: set[tuple[str, str, str, str]] = set()
    errored = 0
    for path in paths:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("error"):
                    continue
                if parse_float(row.get("quality_score", "")) is not None:
                    judged_keys.add((row["model_arm"], row["task_id"], row["condition"], row["rep"]))
    for path in paths:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("error"):
                    errored += 1
                    continue
                if parse_float(row.get("quality_score", "")) is not None:
                    continue
                if (row["model_arm"], row["task_id"], row["condition"], row["rep"]) in judged_keys:
                    continue
                if not row.get("agent_response"):
                    continue
                generated[row["model_arm"]].add((row["task_id"], row["condition"], row["rep"]))
    return {
        "generated_unjudged_by_model": {
            model: {
                "generated_outputs": len(keys),
                "expected_full_outputs": 30 * 4 * 3,
                "coverage_pct": round(len(keys) / (30 * 4 * 3), 4),
            }
            for model, keys in sorted(generated.items())
        },
        "errored_rows": errored,
    }


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return statistics.fmean(values)


def summarize_coverage(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_model: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    for row in rows:
        by_model[row["model_arm"]].add((row["task_id"], row["condition"], row["rep"]))
    return {
        model: {
            "judged_outputs": len(keys),
            "expected_full_outputs": 30 * 4 * 3,
            "coverage_pct": round(len(keys) / (30 * 4 * 3), 4),
        }
        for model, keys in sorted(by_model.items())
    }


def summarize_cells(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in rows:
        groups[(row["model_arm"], row["problem_class"], row["condition"])].append(row["quality_score"])

    summary: dict[str, Any] = {}
    for (model, pc, condition), scores in sorted(groups.items()):
        summary.setdefault(model, {}).setdefault(pc, {})[condition] = {
            "n": len(scores),
            "mean_quality": round(statistics.fmean(scores), 4),
            "stdev_quality": round(statistics.stdev(scores), 4) if len(scores) > 1 else None,
        }
    return summary


def score_h1(cell_summary: dict[str, Any], tie_margin: float) -> dict[str, Any]:
    scored: dict[str, Any] = {}
    for model, pc_data in sorted(cell_summary.items()):
        hits = 0
        cells: dict[str, Any] = {}
        for pc, predicted in PREDICTED_BY_PC.items():
            condition_data = pc_data.get(pc, {})
            means = {
                condition: values["mean_quality"]
                for condition, values in condition_data.items()
                if condition in CONDITIONS and values.get("mean_quality") is not None
            }
            if not means:
                cells[pc] = {
                    "predicted_strategy": predicted,
                    "status": "missing",
                }
                continue
            if len(means) < len(CONDITIONS):
                cells[pc] = {
                    "predicted_strategy": predicted,
                    "status": "incomplete",
                    "means": means,
                    "conditions_available": sorted(means),
                }
                continue
            best_condition = max(means, key=means.get)
            best_mean = means[best_condition]
            predicted_mean = means.get(predicted)
            hit = predicted_mean is not None and predicted_mean >= best_mean - tie_margin
            if hit:
                hits += 1
            cells[pc] = {
                "predicted_strategy": predicted,
                "predicted_mean": predicted_mean,
                "best_condition": best_condition,
                "best_mean": best_mean,
                "status": "hit" if hit else "miss",
                "means": means,
            }
        scored[model] = {
            "hits": hits,
            "cells_available": sum(1 for cell in cells.values() if cell["status"] not in {"missing", "incomplete"}),
            "h1_threshold": ">=4 hits per model",
            "provisional_pass": hits >= 4,
            "cells": cells,
        }
    return scored


def default_result_paths() -> list[Path]:
    return sorted({*RESULTS_DIR.glob("results_raw_*.csv"), *RESULTS_DIR.glob("results_judged_*.csv")})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", nargs="*", type=Path, help="Result CSV paths. Defaults to results/results_raw_*.csv.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--tie-margin",
        type=float,
        default=0.10,
        help="Provisional hit scoring margin before formal bootstrap tests.",
    )
    args = parser.parse_args()

    paths = args.results or default_result_paths()
    rows = load_rows(paths)
    summary = {
        "input_files": [str(path) for path in paths],
        "valid_rows": len(rows),
        "unjudged": summarize_unjudged(paths),
        "coverage": summarize_coverage(rows),
        "cells": summarize_cells(rows),
    }
    summary["h1_provisional"] = score_h1(summary["cells"], args.tie_margin)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"valid_rows": len(rows), "output": str(args.output)}, indent=2))
    if not rows:
        print("No valid judged rows found yet. Run an experiment arm before interpreting analysis.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
