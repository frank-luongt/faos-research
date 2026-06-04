#!/usr/bin/env python3
"""RA-1 H2 pre-registered test: VI vs EN strategy-differentiation via Kendall's W.

The pre-registration (experimental_design_v0.md sec 5.2) defines H2 as:

    Vietnamese industries (banking_vn, insurance_vn) show larger strategy-effect
    spreads than English industries -- i.e. consensus / debate / synthesis
    differentiate more in low-coverage domains. Test: industry-stratified
    Friedman, compare W (Kendall) for VI vs EN.

This script implements that test on the completed 1,440-row fixed-Sonnet-judged
matrix. It reuses the dependency-light helpers from formal_analysis.py so the
statistic family matches the H1 formal packet exactly.

Kendall's W is computed from the same average-rank Friedman chi-square used in
the H1 packet via the identity W = chi2_F / (m * (k - 1)), where m is the number
of blocks (task x rep cells) and k is the number of conditions. This keeps one
ranking/tie convention across H1 and H2.

Outputs:
- results/h2_kendall_w_summary.json
- H2-KENDALL-W-PACKET-2026-05-29.md
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from formal_analysis import (
    CONDITIONS,
    bootstrap_ci,
    default_result_paths,
    friedman_q,
    load_rows,
    permutation_friedman_p,
    signed_rank_p,
)

EXPERIMENT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = EXPERIMENT_DIR / "results"
DEFAULT_JSON = RESULTS_DIR / "h2_kendall_w_summary.json"
DEFAULT_MARKDOWN = EXPERIMENT_DIR / "H2-KENDALL-W-PACKET-2026-05-29.md"

VI_INDUSTRIES = ("banking_vn", "insurance_vn")
EN_INDUSTRIES = ("fintech", "insurance", "healthcare", "software")
PRE_REGISTERED_ARMS = ("sonnet", "qwen_local", "gemma_openrouter")
AUXILIARY_ARMS = ("openai",)
PROBLEM_CLASSES = ("PC1", "PC2", "PC3", "PC4", "PC5")
K = len(CONDITIONS)


def language_of(industry: str) -> str | None:
    if industry in VI_INDUSTRIES:
        return "VI"
    if industry in EN_INDUSTRIES:
        return "EN"
    return None


def build_language_blocks(
    rows: list[dict[str, Any]],
) -> dict[tuple[str, str, str], list[list[float]]]:
    """Group complete (all-4-condition) task x rep cells by (model, language, PC).

    Each block is the list of quality scores in CONDITIONS order, i.e. one
    "judge" ranking the four coordination conditions.
    """
    cells: dict[tuple[str, str, str, str, str], dict[str, float]] = defaultdict(dict)
    for row in rows:
        language = language_of(row["industry"])
        if language is None:
            continue
        key = (row["model_arm"], language, row["problem_class"], row["task_id"], row["rep"])
        cells[key][row["condition"]] = row["quality_score"]
    grouped: dict[tuple[str, str, str], list[list[float]]] = defaultdict(list)
    for (model, language, pc, _task, _rep), scores in sorted(cells.items()):
        if all(condition in scores for condition in CONDITIONS):
            grouped[(model, language, pc)].append([scores[c] for c in CONDITIONS])
    return grouped


def kendall_w(blocks: list[list[float]]) -> float | None:
    """Kendall's W via the Friedman identity W = chi2_F / (m * (k - 1))."""
    m = len(blocks)
    if m == 0 or K < 2:
        return None
    return friedman_q(blocks) / (m * (K - 1))


def analyze(rows: list[dict[str, Any]], permutation_reps: int, bootstrap_reps: int, seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    grouped = build_language_blocks(rows)

    # Per (model, language, PC) cell statistics.
    cells: dict[str, dict[str, dict[str, Any]]] = defaultdict(lambda: defaultdict(dict))
    all_models = sorted({model for (model, _lang, _pc) in grouped})
    for model in all_models:
        for pc in PROBLEM_CLASSES:
            for language in ("VI", "EN"):
                blocks = grouped.get((model, language, pc), [])
                w = kendall_w(blocks)
                if w is None:
                    continue
                q = friedman_q(blocks)
                p = permutation_friedman_p(blocks, q, permutation_reps, rng)
                cells[model][pc][language] = {
                    "n_blocks": len(blocks),
                    "kendall_w": round(w, 6),
                    "friedman_q": round(q, 6),
                    "friedman_permutation_p": round(p, 6),
                }

    # Paired VI - EN deltas at (model, PC) granularity.
    def paired_deltas(arms: tuple[str, ...]) -> tuple[list[float], list[dict[str, Any]]]:
        deltas: list[float] = []
        detail: list[dict[str, Any]] = []
        for model in arms:
            for pc in PROBLEM_CLASSES:
                cell = cells.get(model, {}).get(pc, {})
                if "VI" in cell and "EN" in cell:
                    delta = cell["VI"]["kendall_w"] - cell["EN"]["kendall_w"]
                    deltas.append(delta)
                    detail.append(
                        {
                            "model_arm": model,
                            "problem_class": pc,
                            "w_vi": cell["VI"]["kendall_w"],
                            "w_en": cell["EN"]["kendall_w"],
                            "delta_vi_minus_en": round(delta, 6),
                        }
                    )
        return deltas, detail

    prereg_deltas, prereg_detail = paired_deltas(PRE_REGISTERED_ARMS)
    aux_deltas, aux_detail = paired_deltas(AUXILIARY_ARMS)

    def stratum_mean_w(arms: tuple[str, ...], language: str) -> float | None:
        values = [
            cells[model][pc][language]["kendall_w"]
            for model in arms
            for pc in PROBLEM_CLASSES
            if language in cells.get(model, {}).get(pc, {})
        ]
        return round(statistics.fmean(values), 6) if values else None

    def per_model_mean_w(model: str, language: str) -> float | None:
        values = [
            cells[model][pc][language]["kendall_w"]
            for pc in PROBLEM_CLASSES
            if language in cells.get(model, {}).get(pc, {})
        ]
        return round(statistics.fmean(values), 6) if values else None

    per_model = {}
    for model in all_models:
        w_vi = per_model_mean_w(model, "VI")
        w_en = per_model_mean_w(model, "EN")
        per_model[model] = {
            "role": "pre-registered" if model in PRE_REGISTERED_ARMS else "auxiliary",
            "mean_w_vi": w_vi,
            "mean_w_en": w_en,
            "delta_vi_minus_en": round(w_vi - w_en, 6) if (w_vi is not None and w_en is not None) else None,
            "direction": (
                "VI > EN" if (w_vi is not None and w_en is not None and w_vi > w_en)
                else "EN >= VI" if (w_vi is not None and w_en is not None)
                else "incomplete"
            ),
        }

    prereg_positive = sum(1 for d in prereg_deltas if d > 0)
    prereg_test = {
        "n_pairs": len(prereg_deltas),
        "n_positive_vi_gt_en": prereg_positive,
        "mean_delta": round(statistics.fmean(prereg_deltas), 6) if prereg_deltas else None,
        "median_delta": round(statistics.median(prereg_deltas), 6) if prereg_deltas else None,
        "wilcoxon_signed_rank_p": round(signed_rank_p(prereg_deltas), 6) if prereg_deltas else None,
        "bootstrap_mean_ci": bootstrap_ci(prereg_deltas, bootstrap_reps, rng) if prereg_deltas else None,
    }

    return {
        "strata": {"VI": list(VI_INDUSTRIES), "EN": list(EN_INDUSTRIES)},
        "pre_registered_arms": list(PRE_REGISTERED_ARMS),
        "auxiliary_arms": list(AUXILIARY_ARMS),
        "cells": cells,
        "per_model_mean_w": per_model,
        "pre_registered_stratum_mean_w": {
            "VI": stratum_mean_w(PRE_REGISTERED_ARMS, "VI"),
            "EN": stratum_mean_w(PRE_REGISTERED_ARMS, "EN"),
        },
        "pre_registered_paired_test": prereg_test,
        "pre_registered_pairs": prereg_detail,
        "auxiliary_pairs": aux_detail,
    }


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_markdown(summary: dict[str, Any], params: dict[str, Any], load_report: dict[str, Any], path: Path) -> None:
    test = summary["pre_registered_paired_test"]
    strat = summary["pre_registered_stratum_mean_w"]
    lines = [
        "# RA-1 H2 Kendall's W Packet (VI vs EN Strategy Differentiation)",
        "",
        "Status date: 2026-05-29",
        "",
        "Pre-registered H2 (experimental_design_v0.md sec 5.2): Vietnamese-language",
        "industries show larger strategy-effect spreads than English-language industries.",
        "Operationalized here as Kendall's W (coefficient of concordance over the four",
        "coordination conditions), industry-language-stratified, paired by (model, problem class).",
        "",
        "## Coverage",
        "",
        f"- Valid unique judged rows loaded: {load_report['valid_unique_rows']}",
        f"- VI stratum industries: {', '.join(VI_INDUSTRIES)}",
        f"- EN stratum industries: {', '.join(EN_INDUSTRIES)}",
        "",
        "## Per-Model Mean Kendall's W (averaged over PC1-PC5)",
        "",
        "| Model arm | Role | Mean W (VI) | Mean W (EN) | Delta (VI - EN) | Direction |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for model, cell in summary["per_model_mean_w"].items():
        lines.append(
            "| "
            + " | ".join(
                [
                    model,
                    cell["role"],
                    fmt(cell["mean_w_vi"]),
                    fmt(cell["mean_w_en"]),
                    fmt(cell["delta_vi_minus_en"]),
                    cell["direction"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Pre-Registered Paired Test (3 arms x 5 problem classes = "
            f"{test['n_pairs']} pairs)",
            "",
            f"- Pre-registered VI stratum mean W: {fmt(strat['VI'])}",
            f"- Pre-registered EN stratum mean W: {fmt(strat['EN'])}",
            f"- Pairs with W_VI > W_EN: {test['n_positive_vi_gt_en']} / {test['n_pairs']}",
            f"- Mean Delta (VI - EN): {fmt(test['mean_delta'])}",
            f"- Median Delta (VI - EN): {fmt(test['median_delta'])}",
            f"- Wilcoxon signed-rank p (two-sided, exact): {fmt(test['wilcoxon_signed_rank_p'])}",
            (
                "- Bootstrap 95% CI on mean Delta: ["
                + fmt(test["bootstrap_mean_ci"]["ci_low"])
                + ", "
                + fmt(test["bootstrap_mean_ci"]["ci_high"])
                + "]"
                if test.get("bootstrap_mean_ci")
                else "- Bootstrap 95% CI on mean Delta: n/a"
            ),
            "",
            "## Per-(Model, PC) Cell Detail",
            "",
            "| Model | PC | W (VI) | n_VI | W (EN) | n_EN | Delta (VI - EN) |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for pair in summary["pre_registered_pairs"] + summary["auxiliary_pairs"]:
        model = pair["model_arm"]
        pc = pair["problem_class"]
        vi_cell = summary["cells"][model][pc]["VI"]
        en_cell = summary["cells"][model][pc]["EN"]
        lines.append(
            "| "
            + " | ".join(
                [
                    model,
                    pc,
                    fmt(pair["w_vi"]),
                    str(vi_cell["n_blocks"]),
                    fmt(pair["w_en"]),
                    str(en_cell["n_blocks"]),
                    fmt(pair["delta_vi_minus_en"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Method Notes",
            "",
            "- Kendall's W computed as chi2_F / (m * (k - 1)) from the average-rank Friedman",
            "  statistic in formal_analysis.py; k = 4 conditions, m = task x rep blocks per stratum.",
            f"- Friedman permutation p-values use {params['permutation_reps']} within-block permutations.",
            f"- Bootstrap CI on the mean VI - EN delta uses {params['bootstrap_reps']} paired resamples.",
            f"- Deterministic seed: {params['seed']} (shared with the H1 formal packet).",
            "- VI stratum has 2 industries (6 blocks per PC); EN stratum has 4 industries (12 blocks per PC).",
            "  W is sample-size-normalized (range 0-1), so VI and EN W are directly comparable in scale,",
            "  though the smaller VI block count gives W_VI higher sampling variance.",
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
    summary = analyze(rows, args.permutation_reps, args.bootstrap_reps, args.seed)
    params = {
        "permutation_reps": args.permutation_reps,
        "bootstrap_reps": args.bootstrap_reps,
        "seed": args.seed,
    }
    out = {
        "input_files": [str(path) for path in paths],
        "parameters": params,
        "load_report": load_report,
        "h2": summary,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(summary, params, load_report, args.output_md)
    print(
        json.dumps(
            {
                "valid_unique_rows": load_report["valid_unique_rows"],
                "prereg_mean_w_vi": summary["pre_registered_stratum_mean_w"]["VI"],
                "prereg_mean_w_en": summary["pre_registered_stratum_mean_w"]["EN"],
                "n_positive_vi_gt_en": summary["pre_registered_paired_test"]["n_positive_vi_gt_en"],
                "n_pairs": summary["pre_registered_paired_test"]["n_pairs"],
                "wilcoxon_p": summary["pre_registered_paired_test"]["wilcoxon_signed_rank_p"],
                "output_json": str(args.output_json),
                "output_md": str(args.output_md),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
