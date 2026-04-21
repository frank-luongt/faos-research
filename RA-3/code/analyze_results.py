#!/usr/bin/env python3
"""RA-3 Pilot Study — Statistical Analysis and Visualization.

Usage:
    python analyze_results.py                # Full analysis
    python analyze_results.py --summary      # Descriptive stats only
    python analyze_results.py --output-suffix qwen14b
"""

import argparse
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

import config

CONDITION_ORDER = ["C1_ungrounded", "C2_rag", "C3_ontology", "C4_ontology_process"]
CONDITION_LABELS = {
    "C1_ungrounded": "C1: Ungrounded",
    "C2_rag": "C2: RAG-Only",
    "C3_ontology": "C3: Ontology (L2)",
    "C4_ontology_process": "C4: Onto+Process (L3)",
}
METRIC_NAMES = ["TF", "MA", "RC", "RS"]


def load_data(results_file: str = config.RAW_RESULTS_FILE) -> pd.DataFrame:
    """Load results CSV and deduplicate to the balanced design.

    The raw CSV may contain duplicate (task_id, condition, rep) rows from
    pilot/exploratory runs.  Keep only the last run per group to match the
    paper's 600-run balanced design (50 tasks × 4 conditions × 3 reps).
    """
    if not os.path.exists(results_file):
        print(f"ERROR: No results file at {results_file}")
        sys.exit(1)
    df = pd.read_csv(results_file)
    for m in METRIC_NAMES:
        df[m] = pd.to_numeric(df[m], errors="coerce").fillna(0.0)
    # Deduplicate: keep last entry per (task_id, condition, rep)
    n_before = len(df)
    df = df.drop_duplicates(subset=["task_id", "condition", "rep"], keep="last")
    n_after = len(df)
    if n_before != n_after:
        print(f"  Deduplicated: {n_before} → {n_after} rows "
              f"({n_before - n_after} pilot duplicates removed)")
    df["condition_label"] = df["condition"].map(CONDITION_LABELS)
    return df


# ---------------------------------------------------------------------------
# Descriptive Statistics
# ---------------------------------------------------------------------------

def descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute mean ± SD per condition × metric."""
    rows = []
    for condition in CONDITION_ORDER:
        cdf = df[df["condition"] == condition]
        row = {"condition": CONDITION_LABELS[condition]}
        for m in METRIC_NAMES:
            vals = cdf[m]
            row[f"{m}_mean"] = vals.mean()
            row[f"{m}_std"] = vals.std()
            row[f"{m}_n"] = len(vals)
        rows.append(row)
    return pd.DataFrame(rows)


def descriptive_by_industry(df: pd.DataFrame) -> pd.DataFrame:
    """Compute mean per condition × metric × industry."""
    rows = []
    for industry in config.INDUSTRIES:
        for condition in CONDITION_ORDER:
            mask = (df["condition"] == condition) & (df["industry"] == industry)
            cdf = df[mask]
            row = {
                "industry": industry,
                "condition": CONDITION_LABELS[condition],
            }
            for m in METRIC_NAMES:
                row[f"{m}_mean"] = cdf[m].mean() if len(cdf) > 0 else 0.0
            rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Inferential Statistics
# ---------------------------------------------------------------------------

def run_anova(df: pd.DataFrame) -> dict:
    """Repeated-measures approach: Friedman test per metric (non-parametric).

    Since tasks are the 'subjects' and conditions are within-subject,
    we pivot to get condition scores per task and apply Friedman.
    Only tasks whose metric_tested matches the current metric (or 'ALL')
    are included, matching the paper's methodology.
    """
    results = {}
    for m in METRIC_NAMES:
        # Filter to tasks designed for this metric (or ALL tasks)
        metric_df = df[df["metric_tested"].isin([m, "ALL"])]
        # Average across reps for each task × condition
        pivot = metric_df.groupby(["task_id", "condition"])[m].mean().reset_index()
        pivot_wide = pivot.pivot(index="task_id", columns="condition", values=m)
        # Ensure all conditions present
        available = [c for c in CONDITION_ORDER if c in pivot_wide.columns]
        if len(available) < 2:
            results[m] = {"test": "skipped", "reason": "insufficient conditions"}
            continue

        groups = [pivot_wide[c].dropna().values for c in available]
        # Align to common tasks
        common_idx = pivot_wide[available].dropna().index
        if len(common_idx) < 3:
            results[m] = {"test": "skipped", "reason": "too few tasks with all conditions"}
            continue

        aligned = [pivot_wide.loc[common_idx, c].values for c in available]

        # Friedman test
        stat, p = stats.friedmanchisquare(*aligned)

        # Effect size: Kendall's W = chi2 / (n * (k-1))
        n = len(common_idx)
        k = len(available)
        w = stat / (n * (k - 1)) if n * (k - 1) > 0 else 0

        # Post-hoc: Wilcoxon signed-rank between C1/C2 vs C3/C4
        posthoc = {}
        pairs = [("C1_ungrounded", "C3_ontology"), ("C2_rag", "C3_ontology"),
                 ("C3_ontology", "C4_ontology_process")]
        bonferroni = len(pairs)
        for a, b in pairs:
            if a in available and b in available:
                va = pivot_wide.loc[common_idx, a].values
                vb = pivot_wide.loc[common_idx, b].values
                try:
                    w_stat, w_p = stats.wilcoxon(va, vb)
                    posthoc[f"{a}_vs_{b}"] = {
                        "statistic": round(float(w_stat), 4),
                        "p_value": round(float(w_p), 6),
                        "p_corrected": round(min(float(w_p) * bonferroni, 1.0), 6),
                        "significant": float(w_p) * bonferroni < 0.05,
                    }
                except ValueError:
                    posthoc[f"{a}_vs_{b}"] = {"error": "identical distributions"}

        results[m] = {
            "test": "Friedman",
            "statistic": round(float(stat), 4),
            "p_value": round(float(p), 6),
            "significant": p < 0.05,
            "effect_size_W": round(float(w), 4),
            "n_tasks": int(n),
            "k_conditions": int(k),
            "posthoc_wilcoxon": posthoc,
        }

    return results


# ---------------------------------------------------------------------------
# Visualizations
# ---------------------------------------------------------------------------

def plot_grouped_bar(df: pd.DataFrame, output_dir: str):
    """Grouped bar chart: mean score per condition for each metric.

    Only includes rows where the metric was actually tested (metric_tested
    matches or is 'ALL'), so means reflect true scores, not zeros.
    """
    fig, axes = plt.subplots(1, 4, figsize=(18, 5), sharey=True)
    colors = ["#d62728", "#ff7f0e", "#2ca02c", "#1f77b4"]

    for i, m in enumerate(METRIC_NAMES):
        ax = axes[i]
        metric_df = df[df["metric_tested"].isin([m, "ALL"])]
        means = []
        stds = []
        labels = []
        for j, condition in enumerate(CONDITION_ORDER):
            cdf = metric_df[metric_df["condition"] == condition]
            means.append(cdf[m].mean())
            stds.append(cdf[m].std())
            labels.append(f"C{j+1}")

        bars = ax.bar(labels, means, yerr=stds, color=colors, capsize=4, alpha=0.85)
        ax.set_title(m, fontsize=14, fontweight="bold")
        ax.set_ylim(0, 1.05)
        ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.3)
        if i == 0:
            ax.set_ylabel("Score (0-1)", fontsize=12)

    fig.suptitle("RA-3 Pilot Study: Scores by Condition and Metric", fontsize=16, y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "grouped_bar.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: grouped_bar.png")


def plot_radar(df: pd.DataFrame, output_dir: str):
    """Radar/spider chart: 4-metric profile per condition.

    Uses metric-filtered means so each axis shows only scores from tasks
    where that metric was actually tested.
    """
    angles = np.linspace(0, 2 * np.pi, len(METRIC_NAMES), endpoint=False).tolist()
    angles += angles[:1]  # close the polygon

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    colors = ["#d62728", "#ff7f0e", "#2ca02c", "#1f77b4"]

    for i, condition in enumerate(CONDITION_ORDER):
        cdf = df[df["condition"] == condition]
        values = [cdf[cdf["metric_tested"].isin([m, "ALL"])][m].mean() for m in METRIC_NAMES]
        values += values[:1]
        ax.plot(angles, values, "o-", linewidth=2, label=CONDITION_LABELS[condition],
                color=colors[i])
        ax.fill(angles, values, alpha=0.1, color=colors[i])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(METRIC_NAMES, fontsize=12)
    ax.set_ylim(0, 1)
    ax.set_title("4-Metric Profile by Condition", fontsize=14, pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))

    plt.savefig(os.path.join(output_dir, "radar.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: radar.png")


def plot_industry_heatmap(df: pd.DataFrame, output_dir: str):
    """Heatmap: mean scores by industry × condition for each metric.

    Filters to metric-tested rows so values match paper tables.
    """
    fig, axes = plt.subplots(1, 4, figsize=(20, 4))

    for i, m in enumerate(METRIC_NAMES):
        metric_df = df[df["metric_tested"].isin([m, "ALL"])]
        pivot = metric_df.groupby(["industry", "condition"])[m].mean().reset_index()
        pivot_wide = pivot.pivot(index="industry", columns="condition", values=m)
        # Reorder
        pivot_wide = pivot_wide.reindex(columns=[c for c in CONDITION_ORDER if c in pivot_wide.columns])
        pivot_wide.columns = [CONDITION_LABELS.get(c, c) for c in pivot_wide.columns]

        sns.heatmap(pivot_wide, annot=True, fmt=".2f", cmap="RdYlGn",
                    vmin=0, vmax=1, ax=axes[i], cbar=i == 3)
        axes[i].set_title(m, fontsize=13, fontweight="bold")
        if i > 0:
            axes[i].set_ylabel("")

    fig.suptitle("Score by Industry × Condition", fontsize=15, y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "industry_heatmap.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: industry_heatmap.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="RA-3 Analysis")
    parser.add_argument("--summary", action="store_true", help="Descriptive stats only")
    parser.add_argument("--output-suffix", type=str, help="Read results_raw_<suffix>.csv and write suffixed outputs")
    args = parser.parse_args()

    results_file = config.get_results_file(args.output_suffix)
    analysis_file = config.get_analysis_file(args.output_suffix)
    figures_dir = config.get_figures_dir(args.output_suffix)

    df = load_data(results_file)
    print(f"Loaded {len(df)} result rows.\n")
    print(f"Results source: {results_file}")

    # --- Descriptive ---
    print("=" * 60)
    print("DESCRIPTIVE STATISTICS (Mean ± SD)")
    print("=" * 60)
    desc = descriptive_stats(df)
    for _, row in desc.iterrows():
        print(f"\n{row['condition']}:")
        for m in METRIC_NAMES:
            print(f"  {m}: {row[f'{m}_mean']:.3f} ± {row[f'{m}_std']:.3f}  (n={int(row[f'{m}_n'])})")

    print(f"\n{'='*60}")
    print("BY INDUSTRY")
    print("=" * 60)
    by_ind = descriptive_by_industry(df)
    for industry in config.INDUSTRIES:
        print(f"\n--- {industry.upper()} ---")
        ind_df = by_ind[by_ind["industry"] == industry]
        for _, row in ind_df.iterrows():
            scores = " | ".join(f"{m}={row[f'{m}_mean']:.2f}" for m in METRIC_NAMES)
            print(f"  {row['condition']}: {scores}")

    if args.summary:
        return

    # --- Inferential ---
    print(f"\n{'='*60}")
    print("INFERENTIAL STATISTICS")
    print("=" * 60)
    anova_results = run_anova(df)
    for m, result in anova_results.items():
        print(f"\n{m}:")
        if result.get("test") == "skipped":
            print(f"  Skipped: {result.get('reason')}")
            continue
        sig = "***" if result["significant"] else "n.s."
        print(f"  Friedman χ²={result['statistic']}, p={result['p_value']} {sig}")
        print(f"  Kendall's W={result['effect_size_W']} (n={result['n_tasks']}, k={result['k_conditions']})")
        for pair, ph in result.get("posthoc_wilcoxon", {}).items():
            if "error" in ph:
                print(f"  Post-hoc {pair}: {ph['error']}")
            else:
                sig_ph = "*" if ph["significant"] else "n.s."
                print(f"  Post-hoc {pair}: p_corrected={ph['p_corrected']} {sig_ph}")

    # --- Visualizations ---
    print(f"\n{'='*60}")
    print("GENERATING VISUALIZATIONS")
    print("=" * 60)
    os.makedirs(figures_dir, exist_ok=True)

    plot_grouped_bar(df, figures_dir)
    plot_radar(df, figures_dir)
    plot_industry_heatmap(df, figures_dir)

    # --- Metric-filtered industry×condition means (for paper tables) ---
    industry_condition_means = {}
    grand_accum = {c: {m: [] for m in METRIC_NAMES} for c in CONDITION_ORDER}
    for industry in config.INDUSTRIES:
        industry_condition_means[industry] = {}
        for cond in CONDITION_ORDER:
            mask = (df["condition"] == cond) & (df["industry"] == industry)
            cdf = df[mask]
            means = {}
            for m in METRIC_NAMES:
                tested = cdf[cdf["metric_tested"].isin([m, "ALL"])]
                val = round(float(tested[m].mean()), 3) if len(tested) > 0 else 0.0
                means[m] = val
                grand_accum[cond][m].append(val)
            industry_condition_means[industry][cond] = means
    grand_means = {}
    for cond in CONDITION_ORDER:
        grand_means[cond] = {
            m: round(float(np.mean(grand_accum[cond][m])), 3)
            for m in METRIC_NAMES
        }

    # --- Save summary JSON ---
    from datetime import datetime as dt, timezone as tz
    summary = {
        "experiment": f"RA-3 Pilot ({len(config.INDUSTRIES)} industries)",
        "total_rows": len(df),
        "industries": config.INDUSTRIES,
        "industry_counts": {
            ind: int((df["industry"] == ind).sum()) for ind in config.INDUSTRIES
        },
        "industry_condition_means": industry_condition_means,
        "grand_means": grand_means,
        "statistical_tests": anova_results,
        "n_tasks": df["task_id"].nunique(),
        "n_conditions": df["condition"].nunique(),
        "results_file": os.path.basename(results_file),
        "output_suffix": args.output_suffix or config.OUTPUT_SUFFIX,
        "generated": dt.now(tz.utc).isoformat(),
    }
    with open(analysis_file, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nSaved analysis summary: {analysis_file}")


if __name__ == "__main__":
    main()
