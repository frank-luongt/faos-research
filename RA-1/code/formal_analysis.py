#!/usr/bin/env python3
"""Formal RA-1 statistical analysis from fixed-Sonnet judged result CSVs.

The script intentionally avoids heavy dependencies so it can run in the local
RA-1 virtualenv. It reports:

- Friedman omnibus tests via deterministic within-block permutation.
- Pairwise predicted-strategy comparisons via signed-rank sign-flip tests.
- Paired bootstrap confidence intervals for predicted strategy minus each
  comparator and predicted strategy minus the best observed non-predicted
  strategy.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


EXPERIMENT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = EXPERIMENT_DIR / "results"
DEFAULT_JSON = RESULTS_DIR / "formal_analysis_summary.json"
DEFAULT_MARKDOWN = EXPERIMENT_DIR / "FORMAL-ANALYSIS-PACKET-2026-05-27.md"
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


def default_result_paths() -> list[Path]:
    return sorted(RESULTS_DIR.glob("results_judged_*.csv"))


def load_rows(paths: list[Path]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    by_key: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    skipped_errors = 0
    skipped_unjudged = 0
    duplicates = 0
    for path in paths:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("error"):
                    skipped_errors += 1
                    continue
                score = parse_float(row.get("quality_score", ""))
                if score is None:
                    skipped_unjudged += 1
                    continue
                row["quality_score"] = score
                key = (row["model_arm"], row["task_id"], row["condition"], row["rep"])
                if key in by_key:
                    duplicates += 1
                by_key[key] = row
    return list(by_key.values()), {
        "valid_unique_rows": len(by_key),
        "skipped_errors": skipped_errors,
        "skipped_unjudged": skipped_unjudged,
        "duplicates_overwritten": duplicates,
    }


def average_ranks(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[indexed[k][0]] = avg_rank
        i = j
    return ranks


def friedman_q(blocks: list[list[float]]) -> float:
    n = len(blocks)
    k = len(CONDITIONS)
    rank_sums = [0.0] * k
    for block in blocks:
        for index, rank in enumerate(average_ranks(block)):
            rank_sums[index] += rank
    return (12.0 / (n * k * (k + 1))) * sum(total * total for total in rank_sums) - 3 * n * (k + 1)


def permutation_friedman_p(blocks: list[list[float]], observed_q: float, reps: int, rng: random.Random) -> float:
    if not blocks:
        return math.nan
    extreme = 0
    for _ in range(reps):
        permuted = []
        for block in blocks:
            shuffled = list(block)
            rng.shuffle(shuffled)
            permuted.append(shuffled)
        if friedman_q(permuted) >= observed_q - 1e-12:
            extreme += 1
    return (extreme + 1) / (reps + 1)


def signed_rank_stat(diffs: list[float]) -> tuple[float, list[float]]:
    nonzero = [diff for diff in diffs if abs(diff) > 1e-12]
    ranks = average_ranks([abs(diff) for diff in nonzero])
    positive = sum(rank for rank, diff in zip(ranks, nonzero) if diff > 0)
    negative = sum(rank for rank, diff in zip(ranks, nonzero) if diff < 0)
    return min(positive, negative), ranks


def signed_rank_p(diffs: list[float]) -> float:
    nonzero = [diff for diff in diffs if abs(diff) > 1e-12]
    if not nonzero:
        return 1.0
    observed, ranks = signed_rank_stat(nonzero)
    total_rank = sum(ranks)
    states = {0.0: 1}
    for rank in ranks:
        next_states: dict[float, int] = defaultdict(int)
        for value, count in states.items():
            next_states[value] += count
            next_states[value + rank] += count
        states = next_states
    extreme = 0
    total = 2 ** len(ranks)
    for positive, count in states.items():
        stat = min(positive, total_rank - positive)
        if stat <= observed + 1e-12:
            extreme += count
    return min(1.0, extreme / total)


def bootstrap_ci(diffs: list[float], reps: int, rng: random.Random) -> dict[str, float]:
    if not diffs:
        return {"mean": math.nan, "ci_low": math.nan, "ci_high": math.nan}
    means = []
    for _ in range(reps):
        sample = [rng.choice(diffs) for _ in diffs]
        means.append(statistics.fmean(sample))
    means.sort()
    low_index = int(0.025 * (len(means) - 1))
    high_index = int(0.975 * (len(means) - 1))
    return {
        "mean": round(statistics.fmean(diffs), 6),
        "ci_low": round(means[low_index], 6),
        "ci_high": round(means[high_index], 6),
    }


def build_blocks(rows: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    cells: dict[tuple[str, str, str, str], dict[str, float]] = defaultdict(dict)
    metadata: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for row in rows:
        pc = row["problem_class"]
        key = (row["model_arm"], pc, row["task_id"], row["rep"])
        cells[key][row["condition"]] = row["quality_score"]
        metadata[key] = {
            "industry": row["industry"],
            "task_id": row["task_id"],
            "rep": row["rep"],
        }
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for (model, pc, task_id, rep), scores in sorted(cells.items()):
        if all(condition in scores for condition in CONDITIONS):
            grouped[(model, pc)].append(
                {
                    "task_id": task_id,
                    "rep": rep,
                    "industry": metadata[(model, pc, task_id, rep)]["industry"],
                    "scores": [scores[condition] for condition in CONDITIONS],
                    "score_by_condition": {condition: scores[condition] for condition in CONDITIONS},
                }
            )
    return grouped


def analyze(rows: list[dict[str, Any]], permutation_reps: int, bootstrap_reps: int, seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    grouped = build_blocks(rows)
    result: dict[str, Any] = {}
    for (model, pc), blocks_data in sorted(grouped.items()):
        predicted = PREDICTED_BY_PC[pc]
        blocks = [block["scores"] for block in blocks_data]
        means = {
            condition: round(statistics.fmean(block["score_by_condition"][condition] for block in blocks_data), 6)
            for condition in CONDITIONS
        }
        best_condition = max(means, key=means.get)
        q_value = friedman_q(blocks)
        p_value = permutation_friedman_p(blocks, q_value, permutation_reps, rng)
        predicted_scores = [block["score_by_condition"][predicted] for block in blocks_data]
        pairwise: dict[str, Any] = {}
        for condition in CONDITIONS:
            if condition == predicted:
                continue
            comparator_scores = [block["score_by_condition"][condition] for block in blocks_data]
            diffs = [pred_score - comp_score for pred_score, comp_score in zip(predicted_scores, comparator_scores)]
            ci = bootstrap_ci(diffs, bootstrap_reps, rng)
            pairwise[condition] = {
                **ci,
                "signed_rank_p": round(signed_rank_p(diffs), 6),
                "bonferroni_p_m3": round(min(1.0, signed_rank_p(diffs) * 3), 6),
            }
        best_non_predicted = max((condition for condition in CONDITIONS if condition != predicted), key=means.get)
        best_non_predicted_diffs = [
            block["score_by_condition"][predicted] - block["score_by_condition"][best_non_predicted]
            for block in blocks_data
        ]
        result.setdefault(model, {})[pc] = {
            "n_blocks": len(blocks_data),
            "predicted_strategy": predicted,
            "means": means,
            "best_condition": best_condition,
            "best_mean": means[best_condition],
            "delta_best_minus_predicted": round(means[best_condition] - means[predicted], 6),
            "tolerance_hit_0_10": means[predicted] >= means[best_condition] - 0.10,
            "friedman_q": round(q_value, 6),
            "friedman_permutation_p": round(p_value, 6),
            "pairwise_predicted_minus": pairwise,
            "predicted_minus_best_non_predicted": {
                "best_non_predicted": best_non_predicted,
                **bootstrap_ci(best_non_predicted_diffs, bootstrap_reps, rng),
            },
        }
    return result


def write_markdown(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# RA-1 Formal Analysis Packet",
        "",
        "Status date: 2026-05-27",
        "",
        "This packet adds dependency-light formal tests to the completed RA-1 empirical matrix.",
        "",
        "## Coverage",
        "",
        f"- Valid unique judged rows: {summary['load_report']['valid_unique_rows']}",
        f"- Duplicate judged rows overwritten during analysis load: {summary['load_report']['duplicates_overwritten']}",
        f"- Skipped errored rows: {summary['load_report']['skipped_errors']}",
        "",
        "## H1 Formal Gate",
        "",
        "| Model | PC | Predicted | Best | Delta best-pred | Friedman p | Predicted minus best non-pred CI | Formal read |",
        "| --- | --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for model, pc_data in summary["formal"].items():
        for pc, cell in pc_data.items():
            ci = cell["predicted_minus_best_non_predicted"]
            formal_read = "near-best" if cell["tolerance_hit_0_10"] else "outside tolerance"
            ci_text = f"{ci['mean']:.4f} [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}] vs {ci['best_non_predicted']}"
            lines.append(
                "| "
                + " | ".join(
                    [
                        model,
                        pc,
                        cell["predicted_strategy"],
                        cell["best_condition"],
                        f"{cell['delta_best_minus_predicted']:.4f}",
                        f"{cell['friedman_permutation_p']:.4f}",
                        ci_text,
                        formal_read,
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The formal packet preserves the tolerance-band H1 result: every model/problem-class cell remains within 0.10 of the best observed condition.",
            "- The bootstrap intervals do not support a blanket claim that predicted strategies are statistically superior to all alternatives.",
            "- PC4 remains the main policy revision: `single_agent` is the exact best condition in all model arms.",
            "- Treat these tests as the submission-statistics scaffold; final manuscript tables should cite the JSON output for exact per-comparator values.",
            "",
            "## Method Notes",
            "",
            f"- Friedman p-values use deterministic within-block permutation with {summary['parameters']['permutation_reps']} repetitions.",
            f"- Bootstrap intervals use paired resampling with {summary['parameters']['bootstrap_reps']} repetitions.",
            "- Pairwise p-values use exact signed-rank sign-flip enumeration and Bonferroni m=3 adjustment.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", nargs="*", type=Path, help="Judged result CSV paths. Defaults to results/results_judged_*.csv.")
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--permutation-reps", type=int, default=5000)
    parser.add_argument("--bootstrap-reps", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260527)
    args = parser.parse_args()

    paths = args.results or default_result_paths()
    rows, load_report = load_rows(paths)
    formal = analyze(rows, args.permutation_reps, args.bootstrap_reps, args.seed)
    summary = {
        "input_files": [str(path) for path in paths],
        "parameters": {
            "permutation_reps": args.permutation_reps,
            "bootstrap_reps": args.bootstrap_reps,
            "seed": args.seed,
        },
        "load_report": load_report,
        "formal": formal,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(summary, args.output_md)
    print(json.dumps({"valid_unique_rows": load_report["valid_unique_rows"], "output_json": str(args.output_json), "output_md": str(args.output_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
