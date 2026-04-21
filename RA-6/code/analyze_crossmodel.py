"""RA-6: Cross-Model Comparison Analysis.

Compares baseline Claude results with Qwen (OpenRouter) and Gemma 4 (Google)
replication runs. Produces summary statistics, delta comparison, and figures.

Usage:
  python analyze_crossmodel.py
  python analyze_crossmodel.py --models claude,qwen_2_5_72b_instruct,gemma_4_27b_it
"""

import argparse
import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config

# Academic styling
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

# Display labels for models
MODEL_LABELS = {
    "": "Claude Sonnet 4",
    "claude": "Claude Sonnet 4",
    "qwen_2_5_72b_instruct": "Qwen 2.5 72B",
    "qwen_2_5_72b": "Qwen 2.5 72B",
    "gemma_4_27b_it": "Gemma 4 27B",
    "gemma_4_27b": "Gemma 4 27B",
    "gemma_4_26b_a4b_it": "Gemma 4 26B",
    "gemma_4_26b_a4b": "Gemma 4 26B",
}


def load_model_results(suffix: str) -> dict | None:
    """Load analysis_summary.json for a given model suffix."""
    if suffix in ("", "claude"):
        path = os.path.join(config.RESULTS_DIR, "analysis_summary.json")
    else:
        path = os.path.join(config.RESULTS_DIR, f"analysis_summary_{suffix}.json")
    if not os.path.exists(path):
        print(f"  WARNING: {path} not found, skipping")
        return None
    with open(path) as f:
        return json.load(f)


def extract_key_metrics(data: dict) -> dict:
    """Extract key metrics from analysis summary."""
    metrics = {}

    # RC
    h1 = data.get("H1_RC", {})
    metrics["RC_chi2"] = h1.get("chi2", 0)
    metrics["RC_p"] = h1.get("p_value", 1)
    metrics["RC_W"] = h1.get("kendall_w", 0)
    rc_means = h1.get("condition_means", {})
    metrics["RC_G4"] = rc_means.get("G4_ontology", 0)
    metrics["RC_G1"] = rc_means.get("G1_baseline", 0)
    metrics["RC_G2"] = rc_means.get("G2_persona", 0)
    metrics["RC_G3"] = rc_means.get("G3_rag", 0)
    metrics["RC_delta"] = metrics["RC_G4"] - metrics["RC_G2"]

    # ISS
    h3 = data.get("H3_ISS", {})
    metrics["ISS_chi2"] = h3.get("chi2", 0)
    metrics["ISS_p"] = h3.get("p_value", 1)
    metrics["ISS_W"] = h3.get("kendall_w", 0)
    iss_means = h3.get("condition_means", {})
    metrics["ISS_G4"] = iss_means.get("G4_ontology", 0)
    metrics["ISS_G1"] = iss_means.get("G1_baseline", 0)

    # FDR
    cond_summary = data.get("condition_summary", {})
    g4 = cond_summary.get("G4_ontology", {})
    metrics["FDR_design_G4"] = g4.get("FDR-design", 0)
    metrics["FDR_exec_G4"] = g4.get("FDR-exec", 0)
    metrics["FDR_gap_G4"] = metrics["FDR_design_G4"] - metrics["FDR_exec_G4"]

    return metrics


def plot_crossmodel_radar(all_metrics: dict[str, dict], outdir: str):
    """Radar chart comparing G4 performance across generator models."""
    categories = ["RC (G4)", "ISS (G4, norm)", "FDR-design (G4)", "FDR-exec (G4)", "RC delta\n(G4-G2)"]
    n = len(categories)
    angles = [i / n * 2 * np.pi for i in range(n)]
    angles += angles[:1]

    colors = ["#4878CF", "#E8A838", "#6ACC65", "#D65F5F"]

    fig, ax = plt.subplots(figsize=(5.5, 5.5), subplot_kw=dict(polar=True))
    for (model_key, metrics), color in zip(all_metrics.items(), colors):
        values = [
            metrics["RC_G4"],
            metrics["ISS_G4"] / 5.0,
            metrics["FDR_design_G4"],
            metrics["FDR_exec_G4"],
            max(0, metrics["RC_delta"]),  # clip negative for radar
        ]
        values += values[:1]
        label = MODEL_LABELS.get(model_key, model_key)
        ax.plot(angles, values, "o-", linewidth=1.8, label=label, color=color, markersize=4)
        ax.fill(angles, values, alpha=0.08, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=9)
    ax.set_ylim(0, 1.0)
    ax.legend(loc="upper right", bbox_to_anchor=(1.4, 1.1), frameon=True, fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "crossmodel_radar.pdf"))
    plt.close()


def plot_crossmodel_bars(all_metrics: dict[str, dict], outdir: str):
    """Grouped bar chart: key metrics across generator models."""
    model_keys = list(all_metrics.keys())
    model_labels = [MODEL_LABELS.get(k, k) for k in model_keys]
    metric_names = ["RC (G4)", "RC (G2)", "ISS (G4, /5)", "FDR-d (G4)", "FDR-e (G4)"]

    data = []
    for mk in model_keys:
        m = all_metrics[mk]
        data.append([
            m["RC_G4"] * 100,
            m["RC_G2"] * 100,
            m["ISS_G4"] / 5 * 100,
            m["FDR_design_G4"] * 100,
            m["FDR_exec_G4"] * 100,
        ])
    data = np.array(data)

    x = np.arange(len(metric_names))
    width = 0.8 / len(model_keys)
    colors = ["#4878CF", "#E8A838", "#6ACC65"]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for i, (label, color) in enumerate(zip(model_labels, colors)):
        offset = (i - (len(model_keys) - 1) / 2) * width
        ax.bar(x + offset, data[i], width * 0.9, label=label, color=color)

    ax.set_ylabel("Score (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(metric_names)
    ax.set_ylim(0, 100)
    ax.legend(frameon=True, fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    ax.grid(axis="x", visible=False)
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "crossmodel_comparison.pdf"))
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="RA-6 Cross-Model Comparison")
    parser.add_argument("--models", type=str,
                        default=",qwen_2_5_72b_instruct,gemma_4_27b_it",
                        help="Comma-separated model suffixes (empty = baseline Claude)")
    args = parser.parse_args()

    model_suffixes = [s.strip() for s in args.models.split(",")]

    print("=" * 60)
    print("RA-6 CROSS-MODEL COMPARISON")
    print("=" * 60)

    all_metrics = {}
    for suffix in model_suffixes:
        label = MODEL_LABELS.get(suffix, suffix or "Claude Sonnet 4")
        print(f"\nLoading: {label} (suffix='{suffix}')")
        data = load_model_results(suffix)
        if data is None:
            continue
        metrics = extract_key_metrics(data)
        all_metrics[suffix] = metrics

        print(f"  RC:  G4={metrics['RC_G4']:.1%}, G2={metrics['RC_G2']:.1%}, "
              f"delta={metrics['RC_delta']:+.1%}")
        print(f"  ISS: G4={metrics['ISS_G4']:.2f}/5.0")
        print(f"  FDR: design={metrics['FDR_design_G4']:.1%}, "
              f"exec={metrics['FDR_exec_G4']:.1%}, gap={metrics['FDR_gap_G4']:+.1%}")
        print(f"  Stats: RC chi2={metrics['RC_chi2']:.2f} p={metrics['RC_p']:.4f}, "
              f"ISS chi2={metrics['ISS_chi2']:.2f} p={metrics['ISS_p']:.6f}")

    if len(all_metrics) < 2:
        print("\nNeed at least 2 models for comparison. Run experiments first.")
        return

    # Generate figures
    outdir = os.path.join(config.RESULTS_DIR, "crossmodel")
    os.makedirs(outdir, exist_ok=True)

    plot_crossmodel_radar(all_metrics, outdir)
    print(f"\nSaved: {outdir}/crossmodel_radar.pdf")

    plot_crossmodel_bars(all_metrics, outdir)
    print(f"Saved: {outdir}/crossmodel_comparison.pdf")

    # Save summary JSON
    summary = {
        "models": {
            suffix: {
                "label": MODEL_LABELS.get(suffix, suffix),
                **metrics,
            }
            for suffix, metrics in all_metrics.items()
        },
        "hypotheses": {
            "H5_RC_replicates": all(
                m["RC_G4"] > m["RC_G2"] for m in all_metrics.values()
            ),
            "H6_ISS_replicates": all(
                m["ISS_G4"] > m["ISS_G1"] for m in all_metrics.values()
            ),
            "H7_coverage_precision_tradeoff": all(
                m["FDR_gap_G4"] > 0.05 for m in all_metrics.values()
            ),
        },
    }
    summary_path = os.path.join(outdir, "crossmodel_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved: {summary_path}")

    # Print hypothesis verdicts
    print("\n--- Cross-Model Hypotheses ---")
    for h, result in summary["hypotheses"].items():
        verdict = "SUPPORTED" if result else "NOT SUPPORTED"
        print(f"  {h}: {verdict}")


if __name__ == "__main__":
    main()
