"""RA-6: Generate cross-model comparison figures for the paper.

Reads analysis_summary.json (Claude), analysis_summary_qwen_2_5_72b.json,
and coverage_results_gemma_4_26b_a4b_it.json to produce cross-model
comparison figures with academic styling.

Figures produced:
  Fig 5: Cross-model RC comparison (grouped bar)
  Fig 6: Cross-model ISS comparison (grouped bar)
  Fig 7: Cross-model radar overlay (3 models x 4 conditions → G4 only)
  Fig 8: RC by industry x model heatmap
"""

import json
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Academic styling (matching existing generate_paper_figures.py)
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

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
PAPER_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "papers", "RA-6-Agent-Simulation-Verification", "figures"
)
os.makedirs(PAPER_DIR, exist_ok=True)

# Model display labels and colors
MODEL_LABELS = {
    "claude": "Claude Sonnet 4",
    "qwen": "Qwen 2.5 72B",
    "gemma": "Gemma 4 26B",
}
MODEL_COLORS = ["#2E86AB", "#A23B72", "#F18F01"]

COND_LABELS = {
    "G1_baseline": "G1 (Baseline)",
    "G2_persona": "G2 (Persona)",
    "G3_rag": "G3 (RAG)",
    "G4_ontology": "G4 (Ontology)",
}
COND_KEYS = list(COND_LABELS.keys())

INDUSTRY_LABELS = {
    "fintech": "Fintech",
    "insurance": "Insurance",
    "healthcare": "Healthcare",
    "banking_vn": "Banking (VN)",
    "insurance_vn": "Insurance (VN)",
}


def load_claude_qwen():
    """Load pre-computed analysis summaries for Claude and Qwen."""
    with open(os.path.join(RESULTS_DIR, "analysis_summary.json")) as f:
        claude = json.load(f)
    with open(os.path.join(RESULTS_DIR,
                           "analysis_summary_qwen_2_5_72b.json")) as f:
        qwen = json.load(f)
    return claude, qwen


def compute_gemma_rc_iss():
    """Compute RC and ISS from raw Gemma coverage results.

    Since analysis_summary_gemma*.json doesn't exist yet (FDR incomplete),
    we compute RC and ISS directly from coverage_results.
    """
    with open(os.path.join(RESULTS_DIR,
                           "coverage_results_gemma_4_26b_a4b_it.json")) as f:
        coverage = json.load(f)

    # Parse suite keys
    rc_by_cond = defaultdict(list)
    iss_by_cond = defaultdict(list)
    rc_by_cond_industry = defaultdict(lambda: defaultdict(list))

    for suite_key, data in coverage.items():
        # Parse condition from key like "G1_baseline_fintech_rep1"
        cond = None
        for c in COND_KEYS:
            if suite_key.startswith(c + "_"):
                cond = c
                break
        if cond is None:
            continue

        # Parse industry
        remainder = suite_key[len(cond) + 1:]
        parts = remainder.rsplit("_rep", 1)
        industry = parts[0]

        # RC: proportion of requirements covered
        rc_items = data.get("rc", [])
        if rc_items:
            covered = sum(1 for r in rc_items if r.get("covered", False))
            rc_val = covered / len(rc_items)
            rc_by_cond[cond].append(rc_val)
            rc_by_cond_industry[cond][industry].append(rc_val)

        # ISS: from iss list or iss_mean
        iss_mean = data.get("iss_mean")
        if iss_mean is not None:
            iss_by_cond[cond].append(iss_mean)
        else:
            iss_items = data.get("iss", [])
            for item in iss_items:
                score = item.get("iss_score", 0)
                if score:
                    iss_by_cond[cond].append(score)

    # Compute means
    rc_means = {c: np.mean(v) if v else 0 for c, v in rc_by_cond.items()}
    iss_means = {c: np.mean(v) if v else 0 for c, v in iss_by_cond.items()}

    rc_industry_means = {}
    for cond, ind_dict in rc_by_cond_industry.items():
        rc_industry_means[cond] = {
            ind: np.mean(vals) for ind, vals in ind_dict.items()
        }

    return rc_means, iss_means, rc_industry_means


def fig5_crossmodel_rc(claude, qwen, gemma_rc):
    """Figure 5: Cross-model RC comparison — grouped bar chart."""
    conditions = list(COND_LABELS.values())
    n_conds = len(conditions)
    x = np.arange(n_conds)
    width = 0.25

    claude_rc = [claude["condition_summary"][c]["RC"] * 100
                 for c in COND_KEYS]
    qwen_rc = [qwen["condition_summary"][c]["RC"] * 100
               for c in COND_KEYS]
    gemma_rc_vals = [gemma_rc.get(c, 0) * 100 for c in COND_KEYS]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars1 = ax.bar(x - width, claude_rc, width, label="Claude Sonnet 4",
                   color=MODEL_COLORS[0])
    bars2 = ax.bar(x, qwen_rc, width, label="Qwen 2.5 72B",
                   color=MODEL_COLORS[1])
    bars3 = ax.bar(x + width, gemma_rc_vals, width, label="Gemma 4 26B",
                   color=MODEL_COLORS[2])

    # Value labels
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f"{h:.1f}",
                        xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=8)

    ax.set_ylabel("Regulatory Coverage (%)")
    ax.set_xlabel("Generation Condition")
    ax.set_xticks(x)
    ax.set_xticklabels(conditions)
    ax.set_ylim(0, 65)
    ax.legend(title="Model", frameon=True, loc="upper left")
    ax.grid(axis="y", alpha=0.3)
    ax.grid(axis="x", visible=False)
    plt.tight_layout()
    out = os.path.join(PAPER_DIR, "crossmodel_rc.pdf")
    plt.savefig(out)
    plt.close()
    print(f"  Saved: {out}")


def fig6_crossmodel_iss(claude, qwen, gemma_iss):
    """Figure 6: Cross-model ISS comparison — grouped bar chart."""
    conditions = list(COND_LABELS.values())
    n_conds = len(conditions)
    x = np.arange(n_conds)
    width = 0.25

    claude_iss = [claude["condition_summary"][c]["ISS (norm)"] * 5
                  for c in COND_KEYS]
    qwen_iss = [qwen["condition_summary"][c]["ISS (norm)"] * 5
                for c in COND_KEYS]
    gemma_iss_vals = [gemma_iss.get(c, 0) for c in COND_KEYS]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars1 = ax.bar(x - width, claude_iss, width, label="Claude Sonnet 4",
                   color=MODEL_COLORS[0])
    bars2 = ax.bar(x, qwen_iss, width, label="Qwen 2.5 72B",
                   color=MODEL_COLORS[1])
    bars3 = ax.bar(x + width, gemma_iss_vals, width, label="Gemma 4 26B",
                   color=MODEL_COLORS[2])

    # Value labels
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f"{h:.2f}",
                        xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=8)

    ax.set_ylabel("Industry Specificity Score (1\u20135)")
    ax.set_xlabel("Generation Condition")
    ax.set_xticks(x)
    ax.set_xticklabels(conditions)
    ax.set_ylim(3.0, 5.2)
    ax.legend(title="Model", frameon=True, loc="upper left")
    ax.grid(axis="y", alpha=0.3)
    ax.grid(axis="x", visible=False)
    plt.tight_layout()
    out = os.path.join(PAPER_DIR, "crossmodel_iss.pdf")
    plt.savefig(out)
    plt.close()
    print(f"  Saved: {out}")


def fig7_crossmodel_g4_radar(claude, qwen, gemma_rc, gemma_iss):
    """Figure 7: G4 (Ontology) radar overlay for all 3 models."""
    # Metrics for radar: RC, ISS(norm), FDR-design (Claude/Qwen only)
    # Use available metrics for each model
    categories = ["RC", "ISS (norm)"]
    n = len(categories)
    angles = [i / n * 2 * np.pi for i in range(n)]
    angles += angles[:1]

    # For a proper radar we need at least 3 axes — add FDR for Claude/Qwen
    categories = ["RC", "FDR-design", "ISS (norm)"]
    n = len(categories)
    angles = [i / n * 2 * np.pi for i in range(n)]
    angles += angles[:1]

    g4_claude = [
        claude["condition_summary"]["G4_ontology"]["RC"],
        claude["condition_summary"]["G4_ontology"]["FDR-design"],
        claude["condition_summary"]["G4_ontology"]["ISS (norm)"],
    ]
    g4_qwen = [
        qwen["condition_summary"]["G4_ontology"]["RC"],
        qwen["condition_summary"]["G4_ontology"]["FDR-design"],
        qwen["condition_summary"]["G4_ontology"]["ISS (norm)"],
    ]
    g4_gemma = [
        gemma_rc.get("G4_ontology", 0),
        0.0,  # FDR not available for Gemma
        gemma_iss.get("G4_ontology", 0) / 5.0,  # normalize to 0-1
    ]

    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    for values, label, color in [
        (g4_claude, "Claude Sonnet 4", MODEL_COLORS[0]),
        (g4_qwen, "Qwen 2.5 72B", MODEL_COLORS[1]),
        (g4_gemma, "Gemma 4 26B*", MODEL_COLORS[2]),
    ]:
        vals = values + values[:1]
        ax.plot(angles, vals, "o-", linewidth=2, label=label, color=color,
                markersize=5)
        ax.fill(angles, vals, alpha=0.08, color=color)

    display_cats = ["RC", "FDR\n(design)", "ISS\n(norm)"]
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(display_cats, fontsize=10)
    ax.set_ylim(0, 1.0)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], fontsize=8)
    ax.legend(loc="upper right", bbox_to_anchor=(1.45, 1.1), frameon=True,
              fancybox=False, edgecolor="gray", fontsize=9)
    ax.set_title("G4 (Ontology) Profile by Model", pad=20)
    plt.tight_layout()
    out = os.path.join(PAPER_DIR, "crossmodel_g4_radar.pdf")
    plt.savefig(out)
    plt.close()
    print(f"  Saved: {out}")


def fig8_rc_industry_model_heatmap(claude, qwen, gemma_rc_industry):
    """Figure 8: RC by industry x model heatmap (G4 condition only)."""
    industries = list(INDUSTRY_LABELS.keys())
    ind_labels = list(INDUSTRY_LABELS.values())
    models = ["Claude Sonnet 4", "Qwen 2.5 72B", "Gemma 4 26B"]

    # Extract G4 RC per industry from hardcoded data in fig2 + computed
    # Claude: from existing figure data
    claude_rc_industry = {
        "fintech": 0.39, "insurance": 0.39, "healthcare": 0.59,
        "banking_vn": 0.49, "insurance_vn": 0.56,
    }
    # Qwen: compute from condition_summary if available, else from coverage
    # The Qwen summary has overall means but not per-industry in the summary
    # Use the coverage data approach for consistency
    qwen_rc_industry = {}
    try:
        with open(os.path.join(RESULTS_DIR,
                               "coverage_results_qwen_2_5_72b.json")) as f:
            qwen_cov = json.load(f)
        for suite_key, data in qwen_cov.items():
            if not suite_key.startswith("G4_ontology_"):
                continue
            remainder = suite_key[len("G4_ontology_"):]
            parts = remainder.rsplit("_rep", 1)
            industry = parts[0]
            rc_items = data.get("rc", [])
            if rc_items:
                covered = sum(1 for r in rc_items if r.get("covered", False))
                rc_val = covered / len(rc_items)
                qwen_rc_industry.setdefault(industry, []).append(rc_val)
        qwen_rc_industry = {k: np.mean(v)
                            for k, v in qwen_rc_industry.items()}
    except FileNotFoundError:
        qwen_rc_industry = {ind: 0 for ind in industries}

    gemma_rc_ind = gemma_rc_industry.get("G4_ontology", {})

    matrix = np.array([
        [claude_rc_industry.get(ind, 0) * 100,
         qwen_rc_industry.get(ind, 0) * 100,
         gemma_rc_ind.get(ind, 0) * 100]
        for ind in industries
    ])

    fig, ax = plt.subplots(figsize=(5, 4.5))
    im = ax.imshow(matrix, cmap="YlGnBu", aspect="auto", vmin=15, vmax=65)

    ax.set_xticks(range(len(models)))
    ax.set_xticklabels(models, fontsize=9, rotation=15, ha="right")
    ax.set_yticks(range(len(ind_labels)))
    ax.set_yticklabels(ind_labels)

    # Annotate cells
    for i in range(len(ind_labels)):
        for j in range(len(models)):
            val = matrix[i, j]
            is_max = val == max(matrix[i, :])
            weight = "bold" if is_max else "normal"
            ax.text(j, i, f"{val:.1f}%", ha="center", va="center",
                    fontsize=10, fontweight=weight,
                    color="white" if val > 45 else "black")

    cbar = fig.colorbar(im, ax=ax, shrink=0.8, label="RC (%)")
    ax.set_title("G4 Regulatory Coverage by Industry and Model", fontsize=12)
    plt.tight_layout()
    out = os.path.join(PAPER_DIR, "crossmodel_rc_heatmap.pdf")
    plt.savefig(out)
    plt.close()
    print(f"  Saved: {out}")


if __name__ == "__main__":
    print("Generating cross-model comparison figures for RA-6...")
    print()

    print("Loading model data...")
    claude, qwen = load_claude_qwen()
    gemma_rc, gemma_iss, gemma_rc_industry = compute_gemma_rc_iss()

    print(f"  Gemma RC means: { {c: f'{v:.3f}' for c, v in gemma_rc.items()} }")
    print(f"  Gemma ISS means: { {c: f'{v:.2f}' for c, v in gemma_iss.items()} }")
    print()

    print("Generating figures...")
    fig5_crossmodel_rc(claude, qwen, gemma_rc)
    fig6_crossmodel_iss(claude, qwen, gemma_iss)
    fig7_crossmodel_g4_radar(claude, qwen, gemma_rc, gemma_iss)
    fig8_rc_industry_model_heatmap(claude, qwen, gemma_rc_industry)
    print()
    print(f"Done. Figures saved to: {PAPER_DIR}")
