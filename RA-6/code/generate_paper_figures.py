"""RA-6: Generate publication-quality figures for the paper.

Reads analysis_summary.json and produces 4 PDF figures with
academic styling (serif fonts, proper labels, no underscores).
"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Academic styling
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

PAPER_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "papers", "RA-6-Agent-Simulation-Verification", "figures"
)
os.makedirs(PAPER_DIR, exist_ok=True)

# Condition display names and colors
COND_LABELS = {
    "G1_baseline": "G1 (Baseline)",
    "G2_persona": "G2 (Persona)",
    "G3_rag": "G3 (RAG)",
    "G4_ontology": "G4 (Ontology)",
}
COND_COLORS = ["#4878CF", "#E8A838", "#6ACC65", "#D65F5F"]

INDUSTRY_LABELS = {
    "fintech": "Fintech",
    "insurance": "Insurance",
    "healthcare": "Healthcare",
    "banking_vn": "Banking (VN)",
    "insurance_vn": "Insurance (VN)",
}


COVERAGE_FILES = {
    "Claude": "coverage_results.json",
    "Qwen": "coverage_results_qwen_2_5_72b.json",
    "Gemma": "coverage_results_gemma_4_26b_a4b_it.json",
}

CONDITION_KEYS = ["G1_baseline", "G2_persona", "G3_rag", "G4_ontology"]


def load_data():
    summary_path = os.path.join(
        os.path.dirname(__file__), "results", "analysis_summary.json"
    )
    with open(summary_path) as f:
        return json.load(f)


def load_coverage(filename):
    """Load a coverage_results JSON and return the raw dict."""
    path = os.path.join(os.path.dirname(__file__), "results", filename)
    with open(path) as f:
        return json.load(f)


def compute_per_industry_means(coverage, metric="rc"):
    """Compute per-industry, per-condition means from coverage_results.

    Returns dict like {"Fintech": [g1_mean, g2_mean, g3_mean, g4_mean], ...}.
    metric: "rc" for RC scores, "iss" for ISS scores.
    """
    # Collect values: {(condition, industry): [values]}
    from collections import defaultdict
    buckets = defaultdict(list)

    for key, entry in coverage.items():
        # key format: G1_baseline_fintech_rep1
        parts = key.split("_")
        # condition is first two parts (e.g. G1_baseline, G2_persona)
        cond = parts[0] + "_" + parts[1]
        # industry is everything between condition and repN
        industry = "_".join(parts[2:-1])
        # rep suffix is last part

        if metric == "rc":
            buckets[(cond, industry)].append(entry["rc_score"])
        elif metric == "iss":
            # ISS: mean of per-scenario iss_score values
            scores = [s["iss_score"] for s in entry["iss"]]
            buckets[(cond, industry)].append(np.mean(scores))

    # Build result dict with display names
    result = {}
    for industry_key, display_name in INDUSTRY_LABELS.items():
        row = []
        for cond in CONDITION_KEYS:
            vals = buckets.get((cond, industry_key), [])
            row.append(float(np.mean(vals)) if vals else 0.0)
        result[display_name] = row

    return result


def fig1_summary_radar(data):
    """Figure 1: Multi-DV radar chart comparing all conditions."""
    cond_summary = data["condition_summary"]
    categories = ["RC", "FDR-design", "FDR-exec", "ISS (norm)", "AC"]
    n = len(categories)
    angles = [i / n * 2 * np.pi for i in range(n)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))

    for (cond_key, scores), color in zip(cond_summary.items(), COND_COLORS):
        values = [scores.get(c, 0) for c in categories]
        values += values[:1]
        label = COND_LABELS.get(cond_key, cond_key)
        ax.plot(angles, values, "o-", linewidth=1.8, label=label, color=color,
                markersize=4)
        ax.fill(angles, values, alpha=0.08, color=color)

    display_cats = ["RC", "FDR\n(design)", "FDR\n(exec)", "ISS\n(norm)", "AC"]
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(display_cats, fontsize=10)
    ax.set_ylim(0, 1.0)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], fontsize=8)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), frameon=True,
              fancybox=False, edgecolor="gray")
    plt.tight_layout()
    out = os.path.join(PAPER_DIR, "summary_radar.pdf")
    plt.savefig(out)
    plt.close()
    print(f"  Saved: {out}")


def fig2_rc_by_condition(data, coverage=None):
    """Figure 2: Regulatory Coverage grouped bar chart by industry."""
    if coverage is None:
        coverage = load_coverage(COVERAGE_FILES["Claude"])
    rc_data = compute_per_industry_means(coverage, metric="rc")

    industries = list(rc_data.keys())
    conditions = ["G1 (Baseline)", "G2 (Persona)", "G3 (RAG)", "G4 (Ontology)"]
    x = np.arange(len(conditions))
    width = 0.15
    offsets = np.arange(len(industries)) - (len(industries) - 1) / 2

    ind_colors = ["#4878CF", "#E8A838", "#6ACC65", "#D65F5F", "#8C6BB1"]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for i, (ind, color) in enumerate(zip(industries, ind_colors)):
        vals = [v * 100 for v in rc_data[ind]]
        ax.bar(x + offsets[i] * width, vals, width * 0.9, label=ind, color=color)

    ax.set_ylabel("Regulatory Coverage (%)")
    ax.set_xlabel("Generation Condition")
    ax.set_xticks(x)
    ax.set_xticklabels(conditions)
    ax.set_ylim(0, 70)
    ax.legend(title="Industry", loc="upper left", frameon=True, fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    ax.grid(axis="x", visible=False)
    plt.tight_layout()
    out = os.path.join(PAPER_DIR, "rc_by_condition.pdf")
    plt.savefig(out)
    plt.close()
    print(f"  Saved: {out}")


def fig3_fdr_comparison(data):
    """Figure 3: FDR design vs execution paired bar chart."""
    cond_summary = data["condition_summary"]
    conditions = list(COND_LABELS.values())
    cond_keys = list(COND_LABELS.keys())

    fdr_design = [cond_summary[k]["FDR-design"] * 100 for k in cond_keys]
    fdr_exec = [cond_summary[k]["FDR-exec"] * 100 for k in cond_keys]

    x = np.arange(len(conditions))
    width = 0.35

    fig, ax = plt.subplots(figsize=(6, 4))
    bars1 = ax.bar(x - width/2, fdr_design, width, label="FDR-design",
                   color="#4878CF")
    bars2 = ax.bar(x + width/2, fdr_exec, width, label="FDR-execution",
                   color="#E8A838")

    # Add gap annotations
    for i in range(len(conditions)):
        gap = fdr_design[i] - fdr_exec[i]
        ax.annotate(f"+{gap:.0f}pp",
                    xy=(x[i], max(fdr_design[i], fdr_exec[i]) + 1),
                    ha="center", fontsize=8, color="gray", style="italic")

    ax.set_ylabel("Fault Detection Rate (%)")
    ax.set_xlabel("Generation Condition")
    ax.set_xticks(x)
    ax.set_xticklabels(conditions)
    ax.set_ylim(0, 80)
    ax.legend(frameon=True)
    ax.grid(axis="y", alpha=0.3)
    ax.grid(axis="x", visible=False)
    plt.tight_layout()
    out = os.path.join(PAPER_DIR, "fdr_comparison.pdf")
    plt.savefig(out)
    plt.close()
    print(f"  Saved: {out}")


def fig4_iss_by_industry(data, coverage=None):
    """Figure 4: ISS by condition and industry (heatmap-style)."""
    if coverage is None:
        coverage = load_coverage(COVERAGE_FILES["Claude"])
    iss_data = compute_per_industry_means(coverage, metric="iss")

    conditions = ["G1\n(Base)", "G2\n(Persona)", "G3\n(RAG)", "G4\n(Onto)"]
    industries = list(iss_data.keys())

    matrix = np.array([iss_data[ind] for ind in industries])

    fig, ax = plt.subplots(figsize=(5.5, 4))
    im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto", vmin=4.0, vmax=5.0)

    ax.set_xticks(range(len(conditions)))
    ax.set_xticklabels(conditions)
    ax.set_yticks(range(len(industries)))
    ax.set_yticklabels(industries)

    # Annotate cells
    for i in range(len(industries)):
        for j in range(len(conditions)):
            val = matrix[i, j]
            # Bold the max per row
            is_max = val == max(matrix[i, :])
            weight = "bold" if is_max else "normal"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=10, fontweight=weight,
                    color="white" if val > 4.7 else "black")

    cbar = fig.colorbar(im, ax=ax, shrink=0.8, label="ISS (1--5 scale)")
    ax.set_xlabel("Generation Condition")
    plt.tight_layout()
    out = os.path.join(PAPER_DIR, "iss_heatmap.pdf")
    plt.savefig(out)
    plt.close()
    print(f"  Saved: {out}")


if __name__ == "__main__":
    print("Generating publication figures for RA-6...")
    data = load_data()
    coverage = load_coverage(COVERAGE_FILES["Claude"])
    fig1_summary_radar(data)
    fig2_rc_by_condition(data, coverage)
    fig3_fdr_comparison(data)
    fig4_iss_by_industry(data, coverage)
    print("Done. Figures saved to:", PAPER_DIR)
