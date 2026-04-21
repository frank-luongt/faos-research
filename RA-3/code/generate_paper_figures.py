#!/usr/bin/env python3
"""RA-3 Paper — Publication-Ready Figure Generator.

Generates 6 PDF figures at 300 DPI with academic serif styling for the
RA-3 Neurosymbolic Enterprise AI paper. Reads from results/ and outputs
to the paper's figures/ directory.

Figures:
    1. radar.pdf           — 4-metric radar chart, 4 conditions
    2. grouped_bar.pdf     — Grouped bar chart per metric
    3. industry_heatmap.pdf — C3 scores by industry x metric
    4. delta_heatmap.pdf   — C1->C3 delta by industry x metric (diverging)
    5. crossmodel_comparison.pdf — 3-model ontology lift comparison
    6. entropy_delta.pdf   — Per-metric entropy change (C1->C3) by model

Usage:
    python generate_paper_figures.py
"""

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Add experiment directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
import analyze_results

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONDITION_ORDER = analyze_results.CONDITION_ORDER
CONDITION_LABELS = analyze_results.CONDITION_LABELS
METRIC_NAMES = analyze_results.METRIC_NAMES
INDUSTRIES = config.INDUSTRIES

PAPER_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "papers", "RA-3-Neurosymbolic-Enterprise-AI", "figures",
)

RESULTS_DIR = config.RESULTS_DIR

# Data files for each model
MODEL_FILES = {
    "Claude Sonnet 4": os.path.join(RESULTS_DIR, "results_raw.csv"),
    "Qwen 2.5 72B": os.path.join(RESULTS_DIR, "results_raw_qwen72b.csv"),
    "Gemma 4 26B": os.path.join(RESULTS_DIR, "results_raw_gemma4_26b.csv"),
}

ENTROPY_FILE = os.path.join(RESULTS_DIR, "entropy_analysis_all_models.json")

# Industry display labels (shorter for figures)
INDUSTRY_LABELS = {
    "fintech": "FinTech",
    "insurance": "Insurance",
    "healthcare": "Healthcare",
    "banking_vn": "Banking (VN)",
    "insurance_vn": "Insurance (VN)",
}

# Model short labels
MODEL_SHORT = {
    "Claude Sonnet 4": "Claude",
    "Qwen 2.5 72B": "Qwen 72B",
    "Gemma 4 26B": "Gemma 26B",
}

# Colorblind-safe palette (Okabe-Ito inspired)
CB_COLORS = {
    "C1": "#E69F00",  # orange
    "C2": "#56B4E9",  # sky blue
    "C3": "#009E73",  # bluish green
    "C4": "#0072B2",  # blue
}
CONDITION_COLORS = [CB_COLORS["C1"], CB_COLORS["C2"], CB_COLORS["C3"], CB_COLORS["C4"]]

MODEL_COLORS = {
    "Claude Sonnet 4": "#0072B2",   # blue
    "Qwen 2.5 72B": "#E69F00",     # orange
    "Gemma 4 26B": "#009E73",      # green
}


# ---------------------------------------------------------------------------
# Style Setup
# ---------------------------------------------------------------------------

def apply_academic_style():
    """Apply publication-ready matplotlib style."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "legend.fontsize": 10,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.grid": True,
        "grid.alpha": 0.3,
    })


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------

def load_all_models() -> dict[str, pd.DataFrame]:
    """Load CSV data for all 3 models."""
    dfs = {}
    for model_name, filepath in MODEL_FILES.items():
        if os.path.exists(filepath):
            dfs[model_name] = analyze_results.load_data(filepath)
            print(f"  Loaded {model_name}: {len(dfs[model_name])} rows from {filepath}")
        else:
            print(f"  WARNING: {filepath} not found, skipping {model_name}")
    return dfs


def load_entropy_data() -> dict:
    """Load entropy analysis JSON for all models."""
    if not os.path.exists(ENTROPY_FILE):
        print(f"  WARNING: {ENTROPY_FILE} not found")
        return {}
    with open(ENTROPY_FILE) as f:
        return json.load(f)


def compute_metric_means(df: pd.DataFrame, condition: str) -> dict[str, float]:
    """Compute metric-filtered means for a given condition."""
    cdf = df[df["condition"] == condition]
    means = {}
    for m in METRIC_NAMES:
        tested = cdf[cdf["metric_tested"].isin([m, "ALL"])]
        means[m] = tested[m].mean() if len(tested) > 0 else 0.0
    return means


def compute_industry_metric_means(
    df: pd.DataFrame, condition: str
) -> dict[str, dict[str, float]]:
    """Compute metric-filtered means per industry for a condition."""
    result = {}
    for industry in INDUSTRIES:
        mask = (df["condition"] == condition) & (df["industry"] == industry)
        cdf = df[mask]
        means = {}
        for m in METRIC_NAMES:
            tested = cdf[cdf["metric_tested"].isin([m, "ALL"])]
            means[m] = tested[m].mean() if len(tested) > 0 else 0.0
        result[industry] = means
    return result


# ---------------------------------------------------------------------------
# Figure 1: Radar Chart
# ---------------------------------------------------------------------------

def fig_radar(df: pd.DataFrame, output_dir: str):
    """4-metric radar chart with 4 conditions (PDF, 300 DPI, serif)."""
    angles = np.linspace(0, 2 * np.pi, len(METRIC_NAMES), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))

    for i, condition in enumerate(CONDITION_ORDER):
        means = compute_metric_means(df, condition)
        values = [means[m] for m in METRIC_NAMES]
        values += values[:1]
        ax.plot(
            angles, values, "o-", linewidth=2,
            label=CONDITION_LABELS[condition],
            color=CONDITION_COLORS[i], markersize=5,
        )
        ax.fill(angles, values, alpha=0.08, color=CONDITION_COLORS[i])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(METRIC_NAMES, fontsize=12, fontweight="bold")
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], fontsize=9, color="gray")
    ax.set_title("Four-Metric Profile by Grounding Condition", fontsize=13, pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), framealpha=0.9)

    out = os.path.join(output_dir, "radar.pdf")
    plt.savefig(out, format="pdf")
    plt.close()
    print(f"  [1/6] Saved: {out}")


# ---------------------------------------------------------------------------
# Figure 2: Grouped Bar Chart
# ---------------------------------------------------------------------------

def fig_grouped_bar(df: pd.DataFrame, output_dir: str):
    """Grouped bar chart: mean score per condition for each metric."""
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.5), sharey=True)

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

        bars = ax.bar(
            labels, means, yerr=stds, color=CONDITION_COLORS,
            capsize=4, alpha=0.85, edgecolor="white", linewidth=0.5,
        )
        ax.set_title(m, fontsize=13, fontweight="bold")
        ax.set_ylim(0, 1.08)
        ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.3, linewidth=0.8)

        # Annotate bar values
        for bar, mean in zip(bars, means):
            ax.text(
                bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                f"{mean:.2f}", ha="center", va="bottom", fontsize=8, color="0.3",
            )

        if i == 0:
            ax.set_ylabel("Score (0\u20131)")

    fig.suptitle(
        "RA-3: Scores by Grounding Condition and Metric",
        fontsize=14, y=1.02, fontweight="bold",
    )
    plt.tight_layout()
    out = os.path.join(output_dir, "grouped_bar.pdf")
    plt.savefig(out, format="pdf")
    plt.close()
    print(f"  [2/6] Saved: {out}")


# ---------------------------------------------------------------------------
# Figure 3: Industry Heatmap (C3 scores)
# ---------------------------------------------------------------------------

def fig_industry_heatmap(df: pd.DataFrame, output_dir: str):
    """Heatmap: mean scores by industry x condition for each metric."""
    fig, axes = plt.subplots(1, 4, figsize=(18, 4.5))

    for i, m in enumerate(METRIC_NAMES):
        metric_df = df[df["metric_tested"].isin([m, "ALL"])]
        pivot = metric_df.groupby(["industry", "condition"])[m].mean().reset_index()
        pivot_wide = pivot.pivot(index="industry", columns="condition", values=m)
        # Reorder columns and rows
        pivot_wide = pivot_wide.reindex(
            columns=[c for c in CONDITION_ORDER if c in pivot_wide.columns]
        )
        pivot_wide = pivot_wide.reindex(INDUSTRIES)
        pivot_wide.columns = [CONDITION_LABELS.get(c, c) for c in pivot_wide.columns]
        pivot_wide.index = [INDUSTRY_LABELS.get(ind, ind) for ind in pivot_wide.index]

        sns.heatmap(
            pivot_wide, annot=True, fmt=".2f", cmap="RdYlGn",
            vmin=0, vmax=1, ax=axes[i],
            cbar=(i == 3),
            cbar_kws={"shrink": 0.8} if i == 3 else {},
            linewidths=0.5, linecolor="white",
        )
        axes[i].set_title(m, fontsize=13, fontweight="bold")
        if i > 0:
            axes[i].set_ylabel("")
        else:
            axes[i].set_ylabel("")
        axes[i].tick_params(axis="x", rotation=45)

    fig.suptitle(
        "Score by Industry and Grounding Condition",
        fontsize=14, y=1.02, fontweight="bold",
    )
    plt.tight_layout()
    out = os.path.join(output_dir, "industry_heatmap.pdf")
    plt.savefig(out, format="pdf")
    plt.close()
    print(f"  [3/6] Saved: {out}")


# ---------------------------------------------------------------------------
# Figure 4: Delta Heatmap (C1 -> C3 improvement)
# ---------------------------------------------------------------------------

def fig_delta_heatmap(df: pd.DataFrame, output_dir: str):
    """Heatmap: C1->C3 delta by industry x metric, diverging colormap."""
    c1_means = compute_industry_metric_means(df, "C1_ungrounded")
    c3_means = compute_industry_metric_means(df, "C3_ontology")

    # Build delta matrix
    delta_data = {}
    for industry in INDUSTRIES:
        delta_data[INDUSTRY_LABELS.get(industry, industry)] = {
            m: c3_means[industry][m] - c1_means[industry][m]
            for m in METRIC_NAMES
        }
    delta_df = pd.DataFrame(delta_data).T
    delta_df = delta_df[METRIC_NAMES]

    # Symmetric color range
    vmax = max(abs(delta_df.values.min()), abs(delta_df.values.max()))
    vmax = max(vmax, 0.1)  # minimum range

    fig, ax = plt.subplots(figsize=(7, 5))
    sns.heatmap(
        delta_df, annot=True, fmt="+.3f", cmap="RdBu", center=0,
        vmin=-vmax, vmax=vmax, ax=ax,
        linewidths=0.8, linecolor="white",
        cbar_kws={"label": "\u0394 Score (C3 \u2212 C1)", "shrink": 0.85},
    )
    ax.set_title(
        "Ontology Lift: C1 \u2192 C3 Score Improvement by Industry and Metric",
        fontsize=13, fontweight="bold", pad=12,
    )
    ax.set_ylabel("")
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=0)
    ax.tick_params(axis="y", rotation=0)

    plt.tight_layout()
    out = os.path.join(output_dir, "delta_heatmap.pdf")
    plt.savefig(out, format="pdf")
    plt.close()
    print(f"  [4/6] Saved: {out}")


# ---------------------------------------------------------------------------
# Figure 5: Cross-Model Comparison (Ontology Lift)
# ---------------------------------------------------------------------------

def fig_crossmodel_comparison(
    all_dfs: dict[str, pd.DataFrame], output_dir: str
):
    """3-model comparison: ontology lift (C3-C1 delta) per industry.

    Visualizes the Inverse PKE: Vietnamese industries show ~2x improvement,
    and smaller models (Qwen/Gemma) benefit more than Claude.
    """
    models = [m for m in MODEL_FILES if m in all_dfs]
    if len(models) < 2:
        print("  [5/6] SKIPPED: need at least 2 models for cross-model comparison")
        return

    n_industries = len(INDUSTRIES)
    n_models = len(models)
    bar_width = 0.22
    x = np.arange(n_industries)

    fig, ax = plt.subplots(figsize=(12, 5.5))

    for i, model_name in enumerate(models):
        df = all_dfs[model_name]
        c1_means = compute_industry_metric_means(df, "C1_ungrounded")
        c3_means = compute_industry_metric_means(df, "C3_ontology")

        # Compute composite lift (mean across 4 metrics)
        lifts = []
        for industry in INDUSTRIES:
            delta = np.mean([
                c3_means[industry][m] - c1_means[industry][m]
                for m in METRIC_NAMES
            ])
            lifts.append(delta)

        bars = ax.bar(
            x + i * bar_width, lifts, bar_width,
            label=MODEL_SHORT.get(model_name, model_name),
            color=MODEL_COLORS.get(model_name, f"C{i}"),
            alpha=0.85, edgecolor="white", linewidth=0.5,
        )
        # Value labels
        for bar, val in zip(bars, lifts):
            y_pos = bar.get_height()
            va = "bottom" if y_pos >= 0 else "top"
            ax.text(
                bar.get_x() + bar.get_width() / 2, y_pos + 0.005 * (1 if y_pos >= 0 else -1),
                f"{val:+.3f}", ha="center", va=va, fontsize=8, color="0.3",
            )

    ax.set_xticks(x + bar_width * (n_models - 1) / 2)
    ax.set_xticklabels([INDUSTRY_LABELS.get(ind, ind) for ind in INDUSTRIES])
    ax.set_ylabel("Composite \u0394 Score (C3 \u2212 C1)")
    ax.set_title(
        "Cross-Model Ontology Lift by Industry (Inverse PKE Visualization)",
        fontsize=13, fontweight="bold", pad=12,
    )
    ax.axhline(y=0, color="black", linewidth=0.8, linestyle="-")
    ax.legend(framealpha=0.9)

    # Annotate VN region
    vn_start = INDUSTRIES.index("banking_vn")
    ax.axvspan(
        vn_start - 0.4, n_industries - 0.4,
        alpha=0.06, color="#D55E00", zorder=0,
    )
    ax.text(
        (vn_start + n_industries - 1) / 2,
        ax.get_ylim()[1] * 0.92,
        "Vietnamese domains\n(higher lift expected)",
        ha="center", fontsize=9, fontstyle="italic", color="#D55E00",
    )

    plt.tight_layout()
    out = os.path.join(output_dir, "crossmodel_comparison.pdf")
    plt.savefig(out, format="pdf")
    plt.close()
    print(f"  [5/6] Saved: {out}")


# ---------------------------------------------------------------------------
# Figure 6: Entropy Delta (C1 -> C3) per Model
# ---------------------------------------------------------------------------

def fig_entropy_delta(entropy_data: dict, output_dir: str):
    """Per-metric entropy change (C1->C3) for each model as grouped bar chart.

    Key finding: 11/12 metric x model combinations show entropy REDUCTION
    (constructive), except MA on Claude (entropy increase = Inverse PKE).
    """
    models_in_data = [m for m in MODEL_FILES if m in entropy_data]
    if not models_in_data:
        print("  [6/6] SKIPPED: no entropy data available")
        return

    n_metrics = len(METRIC_NAMES)
    n_models = len(models_in_data)
    bar_width = 0.22
    x = np.arange(n_metrics)

    fig, ax = plt.subplots(figsize=(10, 5.5))

    for i, model_name in enumerate(models_in_data):
        deltas_section = entropy_data[model_name].get("E1", {}).get("entropy_deltas", {})
        delta_vals = []
        for m in METRIC_NAMES:
            val = deltas_section.get(m, {}).get("delta_H_C3_C1", 0.0)
            delta_vals.append(val)

        bars = ax.bar(
            x + i * bar_width, delta_vals, bar_width,
            label=MODEL_SHORT.get(model_name, model_name),
            color=MODEL_COLORS.get(model_name, f"C{i}"),
            alpha=0.85, edgecolor="white", linewidth=0.5,
        )

        # Value labels and highlight the anomaly
        for j, (bar, val) in enumerate(zip(bars, delta_vals)):
            y_pos = bar.get_height()
            va = "bottom" if y_pos >= 0 else "top"
            offset = 0.02 if y_pos >= 0 else -0.02
            fontweight = "bold" if val > 0 else "normal"
            color = "#CC3311" if val > 0 else "0.3"
            ax.text(
                bar.get_x() + bar.get_width() / 2, y_pos + offset,
                f"{val:+.3f}", ha="center", va=va, fontsize=8,
                color=color, fontweight=fontweight,
            )

            # Red outline on the anomalous bar (MA on Claude = positive delta)
            if val > 0:
                bar.set_edgecolor("#CC3311")
                bar.set_linewidth(2.0)

    ax.set_xticks(x + bar_width * (n_models - 1) / 2)
    ax.set_xticklabels(METRIC_NAMES, fontweight="bold")
    ax.set_ylabel("\u0394H (bits): C3 \u2212 C1 entropy")
    ax.set_title(
        "Entropy Change Under Ontology Grounding (C1 \u2192 C3)",
        fontsize=13, fontweight="bold", pad=12,
    )
    ax.axhline(y=0, color="black", linewidth=0.8, linestyle="-")
    ax.legend(framealpha=0.9)

    # Annotate the constructive/destructive regions
    ylim = ax.get_ylim()
    ax.text(
        -0.3, ylim[0] * 0.5,
        "\u2190 Constructive\n   (entropy reduction)",
        fontsize=9, fontstyle="italic", color="#009E73", va="center",
    )
    ax.text(
        -0.3, max(ylim[1] * 0.3, 0.05),
        "\u2192 Destructive\n   (Inverse PKE)",
        fontsize=9, fontstyle="italic", color="#CC3311", va="center",
    )

    # Callout arrow to the anomaly
    # Find the MA + Claude bar
    ma_idx = METRIC_NAMES.index("MA")
    claude_idx = models_in_data.index("Claude Sonnet 4") if "Claude Sonnet 4" in models_in_data else None
    if claude_idx is not None:
        anomaly_x = ma_idx + claude_idx * bar_width
        anomaly_y = entropy_data["Claude Sonnet 4"]["E1"]["entropy_deltas"]["MA"]["delta_H_C3_C1"]
        ax.annotate(
            "Inverse PKE\nsignature",
            xy=(anomaly_x + bar_width / 2, anomaly_y),
            xytext=(anomaly_x + bar_width / 2 + 0.8, anomaly_y + 0.4),
            fontsize=9, fontweight="bold", color="#CC3311",
            arrowprops=dict(
                arrowstyle="->", color="#CC3311", lw=1.5,
                connectionstyle="arc3,rad=0.2",
            ),
            ha="center",
        )

    plt.tight_layout()
    out = os.path.join(output_dir, "entropy_delta.pdf")
    plt.savefig(out, format="pdf")
    plt.close()
    print(f"  [6/6] Saved: {out}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    apply_academic_style()

    print("=" * 60)
    print("RA-3 Paper Figure Generator (Publication-Ready)")
    print("=" * 60)

    # Ensure output directory exists
    os.makedirs(PAPER_DIR, exist_ok=True)
    print(f"\nOutput directory: {PAPER_DIR}")

    # Load data
    print("\nLoading data...")
    all_dfs = load_all_models()
    entropy_data = load_entropy_data()

    if not all_dfs:
        print("ERROR: No model data loaded. Exiting.")
        sys.exit(1)

    # Use Claude data as primary for single-model figures
    primary_model = "Claude Sonnet 4"
    if primary_model not in all_dfs:
        primary_model = list(all_dfs.keys())[0]
        print(f"  Using {primary_model} as primary model (Claude data not found)")
    df = all_dfs[primary_model]

    print(f"\nGenerating 6 figures...")
    print("-" * 40)

    # Fig 1-3: Upgraded existing figures (single model)
    fig_radar(df, PAPER_DIR)
    fig_grouped_bar(df, PAPER_DIR)
    fig_industry_heatmap(df, PAPER_DIR)

    # Fig 4: New delta heatmap (single model)
    fig_delta_heatmap(df, PAPER_DIR)

    # Fig 5: New cross-model comparison (all models)
    fig_crossmodel_comparison(all_dfs, PAPER_DIR)

    # Fig 6: New entropy delta (all models)
    fig_entropy_delta(entropy_data, PAPER_DIR)

    print("-" * 40)
    print(f"\nAll figures saved to: {PAPER_DIR}")
    print("Done.")


if __name__ == "__main__":
    main()
