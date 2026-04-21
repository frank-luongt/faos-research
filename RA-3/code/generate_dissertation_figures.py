#!/usr/bin/env python3
"""Dissertation Chapter 3 — Publication-Ready Figure Generator.

Generates three data-driven figures for the DBA dissertation, based on
pilot-study results from RA-3 and RA-6. All figures are rendered as both
PDF (300 dpi) for LaTeX inclusion and PNG (300 dpi) for reference.

Figures
-------
A. ra3_condition_effect.{pdf,png}
    Grouped bar chart of condition means for the four RA-3 dependent
    variables (TF, MA, RC, RS), faceted by the three subject models
    (Claude Sonnet 4, Qwen 2.5 72B, Gemma 4 26B MoE). Significance stars
    mark the C1->C4 omnibus Friedman result per metric.

B. ra3_inverse_pke.{pdf,png}
    Per-industry C4-minus-C1 composite lift for each model, demonstrating
    the Inverse Parametric Knowledge Effect: the Vietnamese industries
    (banking_vn, insurance_vn) gain approximately 2x the lift of the
    English industries, and the pattern replicates across all three
    models.

C. ra6_coverage_fdr.{pdf,png}
    Two-panel figure showing Regulatory Coverage (left) and Fault
    Detection Rate (right) across the four RA-6 generation conditions
    (G1 baseline, G2 persona, G3 RAG, G4 ontology), grouped by industry,
    based on Claude-subject coverage_results.json and fdr_results.json
    aggregates. Caption states the honest finding: G4 beats G2/G3
    significantly on ISS but fails the Bonferroni bar against G1 on RC.

All numeric values shown in the figures are loaded directly from the
pilot-study JSON files; nothing is simulated.

Usage
-----
    python generate_dissertation_figures.py

Outputs are written to:
    research-academic/dissertation/Ontology Foundation for EAS/figures/
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RA3_RESULTS = os.path.join(SCRIPT_DIR, "results")
RA6_RESULTS = os.path.join(
    SCRIPT_DIR, "..", "RA-6-pilot", "results",
)
OUTPUT_DIR = os.path.abspath(os.path.join(
    SCRIPT_DIR, "..", "..", "dissertation",
    "Ontology Foundation for EAS", "figures",
))


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RA3_MODEL_FILES = {
    "Claude Sonnet 4": "analysis_summary.json",
    "Qwen 2.5 72B": "analysis_summary_qwen72b.json",
    "Gemma 4 26B": "analysis_summary_gemma4_26b.json",
}

RA6_MODEL_FILES = {
    "Claude Sonnet 4": "analysis_summary.json",
    "Qwen 2.5 72B": "analysis_summary_qwen_2_5_72b.json",
    "Gemma 4 26B": "analysis_summary_gemma_4_26b_a4b_it.json",
}

RA3_CONDITIONS = ["C1_ungrounded", "C2_rag", "C3_ontology", "C4_ontology_process"]
RA3_CONDITION_LABELS = {
    "C1_ungrounded": "C1\nBaseline",
    "C2_rag": "C2\nRAG",
    "C3_ontology": "C3\nOntology",
    "C4_ontology_process": "C4\nOnt.+HO",
}
RA3_METRICS = ["TF", "MA", "RC", "RS"]
RA3_METRIC_LONG = {
    "TF": "Terminological Fidelity",
    "MA": "Metric Accuracy",
    "RC": "Role Consistency",
    "RS": "Response Stability",
}

RA6_CONDITIONS = ["G1_baseline", "G2_persona", "G3_rag", "G4_ontology"]
RA6_CONDITION_LABELS = {
    "G1_baseline": "G1\nBaseline",
    "G2_persona": "G2\nPersona",
    "G3_rag": "G3\nRAG",
    "G4_ontology": "G4\nOntology",
}

INDUSTRIES = ["fintech", "insurance", "healthcare", "banking_vn", "insurance_vn"]
INDUSTRY_LABELS = {
    "fintech": "FinTech",
    "insurance": "Insurance",
    "healthcare": "Healthcare",
    "banking_vn": "Banking (VN)",
    "insurance_vn": "Insurance (VN)",
}
VN_INDUSTRIES = {"banking_vn", "insurance_vn"}

MODEL_ORDER = ["Claude Sonnet 4", "Qwen 2.5 72B", "Gemma 4 26B"]
MODEL_SHORT = {
    "Claude Sonnet 4": "Claude",
    "Qwen 2.5 72B": "Qwen 72B",
    "Gemma 4 26B": "Gemma 26B",
}

# Okabe-Ito colorblind-safe palette
CB_COLORS = {
    "C1": "#E69F00",   # orange
    "C2": "#56B4E9",   # sky blue
    "C3": "#009E73",   # bluish green
    "C4": "#0072B2",   # blue
}
CONDITION_COLORS = [CB_COLORS["C1"], CB_COLORS["C2"], CB_COLORS["C3"], CB_COLORS["C4"]]

# Re-use the same ordered palette for G1..G4 so Figures A and C share a visual
# language. (G1=orange "baseline", G4=blue "full treatment")
RA6_COLORS = CONDITION_COLORS

MODEL_COLORS = {
    "Claude Sonnet 4": "#0072B2",   # blue
    "Qwen 2.5 72B": "#E69F00",      # orange
    "Gemma 4 26B": "#009E73",       # bluish green
}

# Distinct hatches as redundant encoding (accessibility)
MODEL_HATCHES = {
    "Claude Sonnet 4": "",
    "Qwen 2.5 72B": "//",
    "Gemma 4 26B": "xx",
}


# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------

def apply_dissertation_style() -> None:
    """Match the dissertation's serif aesthetic (thesis.cls)."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 9.5,
        "axes.labelsize": 10,
        "axes.titlesize": 10.5,
        "legend.fontsize": 8.5,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linestyle": "--",
        "axes.axisbelow": True,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_json(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_ra3() -> dict[str, dict[str, Any]]:
    out = {}
    for model, fname in RA3_MODEL_FILES.items():
        path = os.path.join(RA3_RESULTS, fname)
        out[model] = load_json(path)
    return out


def load_ra6_summaries() -> dict[str, dict[str, Any]]:
    out = {}
    for model, fname in RA6_MODEL_FILES.items():
        path = os.path.join(RA6_RESULTS, fname)
        out[model] = load_json(path)
    return out


def load_ra6_coverage() -> dict[tuple[str, str], float]:
    """Aggregate regulatory-coverage rate per (condition, industry) from
    the Claude-subject coverage_results.json. Each payload has list `rc`
    of requirement dicts with boolean `covered`. Aggregation is across 3
    replicates.
    """
    path = os.path.join(RA6_RESULTS, "coverage_results.json")
    data = load_json(path)
    agg: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {"covered": 0, "total": 0}
    )
    for key, payload in data.items():
        for cond in RA6_CONDITIONS:
            if key.startswith(cond + "_"):
                rest = key[len(cond) + 1:]
                for ind in INDUSTRIES:
                    if rest.startswith(ind + "_rep"):
                        for r in payload.get("rc", []):
                            if r.get("covered") is True:
                                agg[(cond, ind)]["covered"] += 1
                            agg[(cond, ind)]["total"] += 1
                        break
                break
    return {k: v["covered"] / v["total"] if v["total"] else 0.0
            for k, v in agg.items()}


def load_ra6_fdr() -> tuple[dict[tuple[str, str], float],
                             dict[tuple[str, str], float]]:
    """Aggregate design-stage and execution-stage fault detection rates
    per (condition, industry) from the Claude-subject fdr_results.json.
    Returns (design, execution).
    """
    path = os.path.join(RA6_RESULTS, "fdr_results.json")
    data = load_json(path)
    agg_d: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {"det": 0, "total": 0}
    )
    agg_e: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {"det": 0, "total": 0}
    )
    for key, payload in data.items():
        for cond in RA6_CONDITIONS:
            if key.startswith(cond + "_"):
                rest = key[len(cond) + 1:]
                for ind in INDUSTRIES:
                    if rest.startswith(ind + "_rep"):
                        for f in payload.get("stage_a", []):
                            if f.get("design_covered"):
                                agg_d[(cond, ind)]["det"] += 1
                            agg_d[(cond, ind)]["total"] += 1
                        for f in payload.get("stage_b", []):
                            if f.get("execution_detected"):
                                agg_e[(cond, ind)]["det"] += 1
                            agg_e[(cond, ind)]["total"] += 1
                        break
                break
    design = {k: v["det"] / v["total"] if v["total"] else 0.0
              for k, v in agg_d.items()}
    execu = {k: v["det"] / v["total"] if v["total"] else 0.0
             for k, v in agg_e.items()}
    return design, execu


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sig_stars(p: float) -> str:
    """APA-style significance markers."""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "n.s."


def save_fig(fig: plt.Figure, stem: str) -> tuple[str, str]:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pdf_path = os.path.join(OUTPUT_DIR, f"{stem}.pdf")
    png_path = os.path.join(OUTPUT_DIR, f"{stem}.png")
    fig.savefig(pdf_path, format="pdf")
    fig.savefig(png_path, format="png")
    plt.close(fig)
    return pdf_path, png_path


# ---------------------------------------------------------------------------
# Figure A — RA-3 Condition Effect Plot
# ---------------------------------------------------------------------------

def make_figure_a(ra3: dict[str, dict[str, Any]]) -> None:
    """Grouped bar chart, 4 metrics x 4 conditions, faceted by 3 models."""
    # Full-text width for legibility
    fig, axes = plt.subplots(
        1, 3, figsize=(7.0, 3.6), sharey=True,
    )

    n_metrics = len(RA3_METRICS)
    n_conds = len(RA3_CONDITIONS)
    bar_width = 0.18
    x = np.arange(n_metrics)

    for ax_idx, model in enumerate(MODEL_ORDER):
        ax = axes[ax_idx]
        summary = ra3[model]
        grand = summary["grand_means"]
        stats = summary["statistical_tests"]

        for j, cond in enumerate(RA3_CONDITIONS):
            values = [grand[cond][m] for m in RA3_METRICS]
            ax.bar(
                x + j * bar_width, values, bar_width,
                color=CONDITION_COLORS[j],
                edgecolor="white", linewidth=0.6, alpha=0.9,
                label=RA3_CONDITION_LABELS[cond] if ax_idx == 0 else None,
            )

        # Significance annotation for each metric's omnibus Friedman
        # (C1..C4 across tasks). Positioned above the tallest C4 bar.
        for i, m in enumerate(RA3_METRICS):
            p = stats[m]["p_value"]
            w = stats[m]["effect_size_W"]
            stars = sig_stars(p)
            c4_val = grand["C4_ontology_process"][m]
            c2_val = grand["C2_rag"][m]
            top = max(c4_val, c2_val, grand["C1_ungrounded"][m],
                      grand["C3_ontology"][m])
            ax.text(
                x[i] + bar_width * (n_conds - 1) / 2,
                min(top + 0.06, 1.02),
                f"{stars}\n$W$={w:.2f}",
                ha="center", va="bottom",
                fontsize=7, color="0.25",
            )

        ax.set_xticks(x + bar_width * (n_conds - 1) / 2)
        ax.set_xticklabels(RA3_METRICS, fontsize=9)
        ax.set_ylim(0, 1.22)
        ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_title(MODEL_SHORT[model], fontsize=10, fontweight="bold", pad=6)

        if ax_idx == 0:
            ax.set_ylabel("Mean score (0--1)")

    # Shared legend below figure
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=CONDITION_COLORS[j],
                      label=RA3_CONDITION_LABELS[c].replace("\n", " "))
        for j, c in enumerate(RA3_CONDITIONS)
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.05),
        ncol=4, framealpha=0.0, fontsize=8.5,
    )

    fig.suptitle(
        "RA-3 condition effect across four dependent variables and three subject models",
        fontsize=10.5, y=1.02,
    )
    fig.tight_layout()
    pdf, png = save_fig(fig, "ra3_condition_effect")
    print(f"  [A] Saved {pdf}")
    print(f"      Saved {png}")


# ---------------------------------------------------------------------------
# Figure B — Inverse Parametric Knowledge Effect
# ---------------------------------------------------------------------------

def make_figure_b(ra3: dict[str, dict[str, Any]]) -> None:
    """Per-industry C4-minus-C1 composite lift, cross-model replication.

    Composite lift = mean over the four metrics of (C4 - C1) industry means.
    Small-multiple of three panels (one per model), with Vietnamese
    industries highlighted and group means annotated.
    """
    fig, axes = plt.subplots(
        1, 3, figsize=(7.2, 4.6), sharey=True,
    )

    x = np.arange(len(INDUSTRIES))
    bar_width = 0.62

    # Compute all lifts first for y-axis consistency
    all_lifts: dict[str, list[float]] = {}
    for model in MODEL_ORDER:
        icond = ra3[model]["industry_condition_means"]
        lifts = []
        for ind in INDUSTRIES:
            delta = np.mean([
                icond[ind]["C4_ontology_process"][m]
                - icond[ind]["C1_ungrounded"][m]
                for m in RA3_METRICS
            ])
            lifts.append(delta)
        all_lifts[model] = lifts

    y_max = max(max(v) for v in all_lifts.values()) + 0.18
    y_min = min(0.0, min(min(v) for v in all_lifts.values()) - 0.03)

    for ax_idx, model in enumerate(MODEL_ORDER):
        ax = axes[ax_idx]
        lifts = all_lifts[model]

        # Shade VN block first so bars sit on top
        vn_start_idx = INDUSTRIES.index("banking_vn")
        ax.axvspan(
            vn_start_idx - 0.45, len(INDUSTRIES) - 0.55,
            alpha=0.10, color="#D55E00", zorder=0,
        )

        # Color-code by group (English vs Vietnamese) rather than by index
        # so the two groups are distinguishable without shading alone.
        colors = [
            "#0072B2" if ind not in VN_INDUSTRIES else "#D55E00"
            for ind in INDUSTRIES
        ]
        bars = ax.bar(
            x, lifts, bar_width,
            color=colors,
            edgecolor="white", linewidth=0.8, alpha=0.88,
            hatch=MODEL_HATCHES[model],
        )

        for bar, val in zip(bars, lifts):
            y_pos = bar.get_height()
            va = "bottom" if y_pos >= 0 else "top"
            offset = 0.010 if y_pos >= 0 else -0.010
            ax.text(
                bar.get_x() + bar.get_width() / 2, y_pos + offset,
                f"{val:+.2f}",
                ha="center", va=va, fontsize=7.2, color="0.2",
            )

        # Group means as horizontal dotted lines segmented per group
        en_mean = np.mean(lifts[:3])
        vn_mean = np.mean(lifts[3:])
        ratio = vn_mean / en_mean if en_mean > 0 else float("nan")
        # EN segment spans indices 0..2 (x - 0.4 to 2 + 0.4)
        ax.plot(
            [-0.45, 2.45], [en_mean, en_mean],
            color="#0072B2", linestyle=":", linewidth=1.2, zorder=4,
        )
        # VN segment spans indices 3..4
        ax.plot(
            [2.55, 4.45], [vn_mean, vn_mean],
            color="#D55E00", linestyle=":", linewidth=1.2, zorder=4,
        )

        # Ratio callout in the upper-right corner of the plot area
        ax.text(
            0.98, 0.97,
            f"VN/EN = {ratio:.2f}x",
            transform=ax.transAxes,
            fontsize=8, color="0.15", fontweight="bold",
            ha="right", va="top",
            bbox=dict(boxstyle="round,pad=0.3", fc="white",
                      ec="0.6", lw=0.6, alpha=0.9),
        )

        ax.set_xticks(x)
        ax.set_xticklabels(
            [INDUSTRY_LABELS[i] for i in INDUSTRIES],
            rotation=30, ha="right",
        )
        ax.set_ylim(y_min, y_max)
        ax.axhline(0, color="black", linewidth=0.7)
        ax.set_title(
            MODEL_SHORT[model], fontsize=10, fontweight="bold", pad=6,
        )
        if ax_idx == 0:
            ax.set_ylabel(r"Composite $\Delta$ score (C4 $-$ C1)")

    # Shared legend: bar colors + group-mean line styles
    handles = [
        plt.Rectangle((0, 0), 1, 1, color="#0072B2", label="English domain"),
        plt.Rectangle((0, 0), 1, 1, color="#D55E00", label="Vietnamese domain"),
        plt.Line2D([0], [0], color="#0072B2", linestyle=":", linewidth=1.5,
                   label="EN group mean"),
        plt.Line2D([0], [0], color="#D55E00", linestyle=":", linewidth=1.5,
                   label="VN group mean"),
    ]
    fig.legend(
        handles=handles, loc="lower center",
        bbox_to_anchor=(0.5, -0.04), ncol=4,
        framealpha=0.0, fontsize=8.5,
    )

    fig.suptitle(
        "Inverse parametric knowledge effect: full-ontology lift by industry "
        "and subject model",
        fontsize=10, y=1.02,
    )
    fig.tight_layout()
    pdf, png = save_fig(fig, "ra3_inverse_pke")
    print(f"  [B] Saved {pdf}")
    print(f"      Saved {png}")


# ---------------------------------------------------------------------------
# Figure C — RA-6 Coverage & Fault Detection
# ---------------------------------------------------------------------------

def make_figure_c(
    ra6_summaries: dict[str, dict[str, Any]],
    rc_by_ind: dict[tuple[str, str], float],
    fdr_design_by_ind: dict[tuple[str, str], float],
) -> None:
    """Two-panel figure: (left) Regulatory Coverage by industry x condition;
    (right) Design-stage Fault Detection Rate by industry x condition.
    Claude-subject data.
    """
    fig, (ax_l, ax_r) = plt.subplots(
        1, 2, figsize=(7.4, 4.8),
    )

    x = np.arange(len(INDUSTRIES))
    bar_width = 0.2

    def draw_panel(ax, data_map, title, ylabel, ylim):
        for j, cond in enumerate(RA6_CONDITIONS):
            values = [data_map.get((cond, ind), 0.0) for ind in INDUSTRIES]
            ax.bar(
                x + j * bar_width, values, bar_width,
                color=RA6_COLORS[j], edgecolor="white", linewidth=0.6,
                alpha=0.9,
                label=RA6_CONDITION_LABELS[cond],
            )
            for xi, v in zip(x, values):
                ax.text(
                    xi + j * bar_width, v + 0.008,
                    f"{v:.2f}",
                    ha="center", va="bottom", fontsize=5.8, color="0.3",
                    rotation=90,
                )
        ax.set_xticks(x + bar_width * (len(RA6_CONDITIONS) - 1) / 2)
        ax.set_xticklabels(
            [INDUSTRY_LABELS[i] for i in INDUSTRIES],
            rotation=25, ha="right",
        )
        ax.set_ylim(*ylim)
        ax.set_title(title, fontsize=10, fontweight="bold", pad=6)
        ax.set_ylabel(ylabel)

    # Extend y-axis to give room for callout box and rotated value labels
    draw_panel(ax_l, rc_by_ind, "Regulatory Coverage (RC)",
               "Coverage rate (proportion)", ylim=(0, 1.05))
    draw_panel(ax_r, fdr_design_by_ind,
               "Fault Detection Rate (design stage)",
               "Detection rate (proportion)", ylim=(0, 1.15))

    # G4-vs-G1 advantage annotations (overall means, per-panel)
    rc_claude = ra6_summaries["Claude Sonnet 4"]["H1_RC"]["condition_means"]
    rc_g1 = rc_claude["G1_baseline"]
    rc_g4 = rc_claude["G4_ontology"]
    rc_g2 = rc_claude["G2_persona"]
    rc_stat = ra6_summaries["Claude Sonnet 4"]["H1_RC"]
    ax_l.text(
        0.02, 0.985,
        (
            f"Overall (n=125): G4={rc_g4:.3f}, G1={rc_g1:.3f}\n"
            f"G4 - G1 = {(rc_g4 - rc_g1)*100:+.1f} pp (Bonferroni n.s., p={rc_stat['posthoc']['G4_vs_G1_baseline']['p_corrected']:.3f})\n"
            f"G4 - G2 = {(rc_g4 - rc_g2)*100:+.1f} pp (sig., p={rc_stat['posthoc']['G4_vs_G2_persona']['p_corrected']:.4f})"
        ),
        transform=ax_l.transAxes, fontsize=6.8, color="0.1",
        va="top", ha="left",
        bbox=dict(boxstyle="round,pad=0.35", fc="white",
                  ec="0.6", lw=0.5, alpha=0.92),
    )

    fdr_claude = ra6_summaries["Claude Sonnet 4"]["H2_FDR_design"]["condition_means"]
    fdr_g1 = fdr_claude["G1_baseline"]
    fdr_g4 = fdr_claude["G4_ontology"]
    fdr_stat = ra6_summaries["Claude Sonnet 4"]["H2_FDR_design"]
    ax_r.text(
        0.02, 0.985,
        (
            f"Overall (n=25): G4={fdr_g4:.3f}, G1={fdr_g1:.3f}\n"
            f"G4 - G1 = {(fdr_g4 - fdr_g1)*100:+.1f} pp (omnibus n.s.,\n"
            f"$\\chi^2$={fdr_stat['chi2']:.3f}, p={fdr_stat['p_value']:.3f})"
        ),
        transform=ax_r.transAxes, fontsize=6.8, color="0.1",
        va="top", ha="left",
        bbox=dict(boxstyle="round,pad=0.35", fc="white",
                  ec="0.6", lw=0.5, alpha=0.92),
    )

    # Single legend below
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=RA6_COLORS[j],
                      label=RA6_CONDITION_LABELS[c].replace("\n", " "))
        for j, c in enumerate(RA6_CONDITIONS)
    ]
    fig.legend(
        handles=handles, loc="lower center",
        bbox_to_anchor=(0.5, -0.04), ncol=4,
        framealpha=0.0, fontsize=8.5,
    )

    fig.suptitle(
        "RA-6 regulatory coverage and fault detection by condition and "
        "industry (Claude Sonnet 4 subject)",
        fontsize=10, y=1.02,
    )
    fig.tight_layout()
    pdf, png = save_fig(fig, "ra6_coverage_fdr")
    print(f"  [C] Saved {pdf}")
    print(f"      Saved {png}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    apply_dissertation_style()
    print("=" * 64)
    print("Dissertation Chapter 3 Figure Generator")
    print("=" * 64)
    print(f"Output directory: {OUTPUT_DIR}\n")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Loading RA-3 analysis summaries...")
    ra3 = load_ra3()
    for model, payload in ra3.items():
        n = payload.get("total_rows", "?")
        print(f"  - {model}: {n} rows")

    print("\nLoading RA-6 analysis summaries...")
    ra6_summaries = load_ra6_summaries()
    for model, payload in ra6_summaries.items():
        rc = payload["H1_RC"]["condition_means"]
        print(f"  - {model}: RC G1={rc['G1_baseline']:.3f}, "
              f"G4={rc['G4_ontology']:.3f}")

    print("\nAggregating RA-6 coverage and FDR by (condition, industry)...")
    rc_by_ind = load_ra6_coverage()
    fdr_design_by_ind, fdr_exec_by_ind = load_ra6_fdr()
    print(f"  - Coverage buckets: {len(rc_by_ind)}")
    print(f"  - FDR design buckets: {len(fdr_design_by_ind)}")

    print("\nGenerating figures...")
    make_figure_a(ra3)
    make_figure_b(ra3)
    make_figure_c(ra6_summaries, rc_by_ind, fdr_design_by_ind)

    print("\nAll figures saved to:")
    print(f"  {OUTPUT_DIR}")
    print("\nDone.")


if __name__ == "__main__":
    main()
