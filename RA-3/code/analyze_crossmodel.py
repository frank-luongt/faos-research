#!/usr/bin/env python3
"""RA-3 cross-model comparison analysis.

Usage:
    python analyze_crossmodel.py --compare-suffix qwen14b
"""

import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

import analyze_results as ra3_analysis
import config


def infer_label(suffix: str, fallback: str) -> str:
    if not suffix:
        return fallback
    normalized = suffix.lower()
    label_map = {
        "qwen14b": "Qwen 2.5 14B",
        "qwen32b": "Qwen 2.5 32B",
        "qwen72b": "Qwen 2.5 72B",
        "qwen_plus": "Qwen Plus (API)",
        "qwen_turbo": "Qwen Turbo (API)",
        "qwen_max": "Qwen Max (API)",
        "gemma4_26b": "Gemma 4 26B MoE (4B active)",
        "gemma4_31b": "Gemma 4 31B Dense",
        "gemma4_e4b": "Gemma 4 E4B",
        "gemma4": "Gemma 4",
        "qwen_qwen_2_5_72b_instruct": "Qwen 2.5 72B (OpenRouter)",
    }
    return label_map.get(normalized, suffix.replace("_", " ").title())


def compute_primary_task_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse each task×condition to its primary metric score."""
    grouped = (
        df.groupby(["task_id", "industry", "condition", "metric_tested"], as_index=False)[
            ["TF", "MA", "RC", "RS"]
        ]
        .mean()
    )

    rows = []
    for row in grouped.to_dict("records"):
        metric = row["metric_tested"]
        if metric == "ALL":
            primary = float(np.mean([row["TF"], row["MA"], row["RC"], row["RS"]]))
        else:
            primary = float(row[metric])
        rows.append(
            {
                "task_id": row["task_id"],
                "industry": row["industry"],
                "condition": row["condition"],
                "primary_score": primary,
            }
        )
    return pd.DataFrame(rows)


def compute_task_deltas(task_scores: pd.DataFrame) -> pd.DataFrame:
    """Compute per-task ontology lift, matching the paper's C1→C3 delta."""
    pivot = task_scores.pivot_table(
        index=["task_id", "industry"],
        columns="condition",
        values="primary_score",
        aggfunc="mean",
    )
    required = ["C1_ungrounded", "C3_ontology"]
    missing = [condition for condition in required if condition not in pivot.columns]
    if missing:
        raise ValueError(f"Missing conditions for delta analysis: {missing}")

    delta = (pivot["C3_ontology"] - pivot["C1_ungrounded"]).rename("delta_c1_c3")
    return delta.reset_index()


def compute_industry_condition_means(task_scores: pd.DataFrame) -> pd.DataFrame:
    means = (
        task_scores.groupby(["industry", "condition"], as_index=False)["primary_score"]
        .mean()
    )
    pivot = means.pivot(index="industry", columns="condition", values="primary_score")
    pivot = pivot.reindex(columns=ra3_analysis.CONDITION_ORDER)
    pivot["delta_c1_c3"] = pivot["C3_ontology"] - pivot["C1_ungrounded"]
    return pivot.reset_index()


def compute_metric_profiles(df: pd.DataFrame) -> dict[str, list[float]]:
    """Return the 4-metric profile per condition for radar plots."""
    profiles = {}
    for condition in ra3_analysis.CONDITION_ORDER:
        cdf = df[df["condition"] == condition]
        profiles[condition] = [
            float(cdf[cdf["metric_tested"].isin([metric, "ALL"])][metric].mean())
            for metric in ra3_analysis.METRIC_NAMES
        ]
    return profiles


def plot_dual_radar(
    baseline_df: pd.DataFrame,
    compare_df: pd.DataFrame,
    baseline_label: str,
    compare_label: str,
    output_dir: str,
):
    angles = np.linspace(0, 2 * np.pi, len(ra3_analysis.METRIC_NAMES), endpoint=False).tolist()
    angles += angles[:1]
    colors = ["#d62728", "#ff7f0e", "#2ca02c", "#1f77b4"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 7), subplot_kw=dict(polar=True))
    for ax, df, label in (
        (axes[0], baseline_df, baseline_label),
        (axes[1], compare_df, compare_label),
    ):
        profiles = compute_metric_profiles(df)
        for idx, condition in enumerate(ra3_analysis.CONDITION_ORDER):
            values = profiles[condition] + profiles[condition][:1]
            ax.plot(
                angles,
                values,
                "o-",
                linewidth=2,
                label=ra3_analysis.CONDITION_LABELS[condition],
                color=colors[idx],
            )
            ax.fill(angles, values, alpha=0.08, color=colors[idx])
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(ra3_analysis.METRIC_NAMES, fontsize=11)
        ax.set_ylim(0, 1)
        ax.set_title(label, fontsize=14, pad=18)

    axes[1].legend(loc="upper right", bbox_to_anchor=(1.35, 1.12))
    fig.suptitle("RA-3 Cross-Model Metric Profiles", fontsize=16, y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "dual_radar.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: dual_radar.png")


def plot_delta_by_industry(
    baseline_delta: pd.DataFrame,
    compare_delta: pd.DataFrame,
    baseline_label: str,
    compare_label: str,
    output_dir: str,
):
    merged = baseline_delta.merge(
        compare_delta,
        on="industry",
        suffixes=("_baseline", "_compare"),
    )
    x = np.arange(len(merged))
    width = 0.36

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(
        x - width / 2,
        merged["delta_c1_c3_baseline"],
        width,
        label=baseline_label,
        color="#1f77b4",
    )
    ax.bar(
        x + width / 2,
        merged["delta_c1_c3_compare"],
        width,
        label=compare_label,
        color="#2ca02c",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(merged["industry"], rotation=20, ha="right")
    ax.set_ylabel("Primary Score Delta (C3 - C1)")
    ax.set_title("Ontology Lift by Industry")
    ax.axhline(0, color="gray", linewidth=1, alpha=0.5)
    ax.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "delta_by_industry.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: delta_by_industry.png")


def summarize_delta_groups(delta_df: pd.DataFrame, column: str) -> dict[str, float]:
    english_mask = ~delta_df["industry"].str.endswith("_vn")
    vietnamese_mask = delta_df["industry"].str.endswith("_vn")
    return {
        "overall": round(float(delta_df[column].mean()), 4),
        "english": round(float(delta_df.loc[english_mask, column].mean()), 4),
        "vietnamese": round(float(delta_df.loc[vietnamese_mask, column].mean()), 4),
    }


def main():
    parser = argparse.ArgumentParser(description="RA-3 cross-model comparison")
    parser.add_argument("--baseline-suffix", default="", help="Suffix for the baseline run (default: Claude baseline)")
    parser.add_argument("--compare-suffix", default="qwen14b", help="Suffix for the comparison run")
    parser.add_argument("--baseline-label", help="Display label for the baseline model")
    parser.add_argument("--compare-label", help="Display label for the comparison model")
    args = parser.parse_args()

    baseline_file = config.get_results_file(args.baseline_suffix)
    compare_file = config.get_results_file(args.compare_suffix)
    baseline_label = args.baseline_label or infer_label(args.baseline_suffix, "Claude Sonnet 4")
    compare_label = args.compare_label or infer_label(args.compare_suffix, "Comparison Model")

    baseline_df = ra3_analysis.load_data(baseline_file)
    compare_df = ra3_analysis.load_data(compare_file)

    baseline_task_scores = compute_primary_task_scores(baseline_df)
    compare_task_scores = compute_primary_task_scores(compare_df)
    baseline_delta = compute_task_deltas(baseline_task_scores)
    compare_delta = compute_task_deltas(compare_task_scores)
    merged_delta = baseline_delta.merge(
        compare_delta,
        on=["task_id", "industry"],
        suffixes=("_baseline", "_compare"),
    )

    try:
        wilcoxon_stat, wilcoxon_p = stats.wilcoxon(
            merged_delta["delta_c1_c3_baseline"],
            merged_delta["delta_c1_c3_compare"],
        )
        delta_test = {
            "test": "Wilcoxon signed-rank",
            "statistic": round(float(wilcoxon_stat), 4),
            "p_value": round(float(wilcoxon_p), 6),
            "significant": float(wilcoxon_p) < 0.05,
        }
    except ValueError as exc:
        delta_test = {"test": "Wilcoxon signed-rank", "error": str(exc)}

    baseline_industry = compute_industry_condition_means(baseline_task_scores)
    compare_industry = compute_industry_condition_means(compare_task_scores)

    output_tag = infer_label(args.compare_suffix, "comparison").lower().replace(" ", "_")
    output_dir = os.path.join(config.RESULTS_DIR, f"figures_crossmodel_{output_tag}")
    os.makedirs(output_dir, exist_ok=True)

    print(f"Baseline file: {baseline_file}")
    print(f"Comparison file: {compare_file}")
    print(f"Output dir: {output_dir}")

    plot_dual_radar(baseline_df, compare_df, baseline_label, compare_label, output_dir)
    plot_delta_by_industry(baseline_industry, compare_industry, baseline_label, compare_label, output_dir)

    summary = {
        "baseline": {
            "label": baseline_label,
            "results_file": os.path.basename(baseline_file),
            "anova": ra3_analysis.run_anova(baseline_df),
            "delta_summary": summarize_delta_groups(baseline_delta, "delta_c1_c3"),
        },
        "comparison": {
            "label": compare_label,
            "results_file": os.path.basename(compare_file),
            "anova": ra3_analysis.run_anova(compare_df),
            "delta_summary": summarize_delta_groups(compare_delta, "delta_c1_c3"),
        },
        "delta_comparison": {
            "per_task": merged_delta.to_dict("records"),
            "delta_test": delta_test,
            "baseline_minus_comparison_mean": round(
                float(
                    (
                        merged_delta["delta_c1_c3_baseline"]
                        - merged_delta["delta_c1_c3_compare"]
                    ).mean()
                ),
                4,
            ),
        },
        "industry_delta_table": baseline_industry.merge(
            compare_industry,
            on="industry",
            suffixes=("_baseline", "_compare"),
        ).to_dict("records"),
    }

    summary_file = os.path.join(config.RESULTS_DIR, f"analysis_crossmodel_{output_tag}.json")

    def _json_default(obj):
        """Handle numpy types for JSON serialization."""
        if isinstance(obj, (np.bool_, np.integer)):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2, default=_json_default)
    print(f"Saved summary: {summary_file}")


if __name__ == "__main__":
    main()
