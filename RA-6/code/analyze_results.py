"""RA-6 Pilot: Statistical Analysis and Visualization.

Implements the analysis plan from protocol §5:
- H1: RC across conditions (Friedman + Wilcoxon post-hoc)
- H2: FDR across conditions
- H3: ISS across conditions
- H4: AC equivalence (TOST)
- Secondary: cross-industry CV, marginal improvement, cost-efficiency
"""

import json
import os
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

import config


def load_results() -> tuple[dict, dict]:
    """Load coverage and FDR results."""
    with open(config.COVERAGE_FILE) as f:
        coverage = json.load(f)
    with open(config.FDR_FILE) as f:
        fdr = json.load(f)
    return coverage, fdr


def parse_suite_key(key: str) -> tuple[str, str, int]:
    """Parse 'G1_baseline_fintech_rep1' or 'G1_baseline_banking_vn_rep1'."""
    for cond in config.CONDITIONS:
        if key.startswith(cond + "_"):
            remainder = key[len(cond) + 1:]  # e.g. "fintech_rep1" or "banking_vn_rep1"
            parts = remainder.rsplit("_rep", 1)
            industry = parts[0]
            rep = int(parts[1])
            return cond, industry, rep
    raise ValueError(f"Cannot parse suite key: {key}")


def build_rc_dataframe(coverage: dict) -> pd.DataFrame:
    """Build per-requirement RC dataframe for statistical testing."""
    rows = []
    for suite_key, data in coverage.items():
        condition, industry, rep = parse_suite_key(suite_key)
        for req_result in data.get("rc", []):
            rows.append({
                "condition": condition,
                "industry": industry,
                "rep": rep,
                "requirement_id": req_result["requirement_id"],
                "regulation": req_result.get("regulation", ""),
                "covered": 1 if req_result["covered"] else 0,
            })
    return pd.DataFrame(rows)


def build_iss_dataframe(coverage: dict) -> pd.DataFrame:
    """Build per-scenario ISS dataframe."""
    rows = []
    for suite_key, data in coverage.items():
        condition, industry, rep = parse_suite_key(suite_key)
        for iss_result in data.get("iss", []):
            rows.append({
                "condition": condition,
                "industry": industry,
                "rep": rep,
                "scenario_id": iss_result["scenario_id"],
                "iss_score": iss_result["iss_score"],
            })
    return pd.DataFrame(rows)


def build_fdr_dataframe(fdr: dict) -> pd.DataFrame:
    """Build per-fault FDR dataframe."""
    rows = []
    for suite_key, data in fdr.items():
        condition, industry, rep = parse_suite_key(suite_key)
        for stage_a, stage_b in zip(data.get("stage_a", []), data.get("stage_b", [])):
            rows.append({
                "condition": condition,
                "industry": industry,
                "rep": rep,
                "fault_id": stage_a["fault_id"],
                "design_covered": 1 if stage_a.get("design_covered") else 0,
                "execution_detected": 1 if stage_b.get("execution_detected") else 0,
            })
    return pd.DataFrame(rows)


def build_ac_dataframe(coverage: dict) -> pd.DataFrame:
    """Build per-category AC dataframe."""
    rows = []
    for suite_key, data in coverage.items():
        condition, industry, rep = parse_suite_key(suite_key)
        ac = data.get("ac", {})
        covered_cats = set(ac.get("covered", []))
        for cat in config.ADVERSARIAL_CATEGORIES:
            rows.append({
                "condition": condition,
                "industry": industry,
                "rep": rep,
                "category": cat,
                "covered": 1 if cat in covered_cats else 0,
            })
    return pd.DataFrame(rows)


def friedman_with_posthoc(df: pd.DataFrame, value_col: str, label: str, id_col: str = None) -> dict:
    """Run Friedman test + Wilcoxon post-hoc with Bonferroni correction."""
    conditions = sorted(df["condition"].unique())
    # Determine the ID column for grouping
    if id_col is None:
        for candidate in ["requirement_id", "fault_id", "scenario_id", "category"]:
            if candidate in df.columns:
                id_col = candidate
                break
    if id_col is None:
        return {"label": label, "error": "No ID column found for grouping"}

    # Aggregate by condition: mean per unit across reps
    agg = df.groupby(["condition", id_col])[value_col].mean().reset_index()

    # Pivot for Friedman
    groups = []
    for c in conditions:
        vals = agg[agg["condition"] == c][value_col].values
        groups.append(vals)

    # Align lengths (take min)
    min_len = min(len(g) for g in groups)
    groups = [g[:min_len] for g in groups]

    if min_len < 5:
        return {"label": label, "error": f"Insufficient data (n={min_len})"}

    stat, p_value = stats.friedmanchisquare(*groups)
    n = min_len
    k = len(conditions)
    kendall_w = stat / (n * (k - 1))

    # Handle NaN from degenerate data (e.g., all zeros in dry run)
    chi2_val = round(float(stat), 3) if not np.isnan(stat) else None
    p_val = round(float(p_value), 6) if not np.isnan(p_value) else None
    w_val = round(float(kendall_w), 4) if not np.isnan(kendall_w) else None

    result = {
        "label": label,
        "n": int(n),
        "k": int(k),
        "chi2": chi2_val,
        "p_value": p_val,
        "significant": bool(p_val is not None and p_val < 0.05),
        "kendall_w": w_val,
        "condition_means": {},
    }

    for i, c in enumerate(conditions):
        result["condition_means"][c] = round(float(np.mean(groups[i])), 4)

    # Post-hoc: G4 vs each other (Bonferroni correction for 3 comparisons)
    g4_idx = next((i for i, c in enumerate(conditions) if "G4" in c), None)
    if g4_idx is not None and p_value < 0.05:
        posthoc = {}
        for i, c in enumerate(conditions):
            if i == g4_idx:
                continue
            w_stat, w_p = stats.wilcoxon(groups[g4_idx], groups[i])
            corrected_p = min(float(w_p) * 3, 1.0)  # Bonferroni for 3 comparisons
            posthoc[f"G4_vs_{c}"] = {
                "w_stat": round(float(w_stat), 3),
                "p_raw": round(float(w_p), 6),
                "p_corrected": round(corrected_p, 6),
                "significant": bool(corrected_p < 0.05),
            }
        result["posthoc"] = posthoc

    return result


def plot_rc_by_condition(df: pd.DataFrame):
    """Grouped bar chart: RC by condition and industry."""
    agg = df.groupby(["condition", "industry"])["covered"].mean().reset_index()
    agg["covered_pct"] = agg["covered"] * 100

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=agg, x="condition", y="covered_pct", hue="industry", ax=ax)
    ax.set_ylabel("Regulatory Coverage (%)")
    ax.set_xlabel("Generation Condition")
    ax.set_title("DV1: Regulatory Coverage by Condition and Industry")
    ax.set_ylim(0, 100)
    ax.legend(title="Industry")
    plt.tight_layout()
    plt.savefig(os.path.join(config.FIGURES_DIR, "rc_by_condition.png"), dpi=150)
    plt.close()


def plot_iss_distribution(df: pd.DataFrame):
    """Violin plot: ISS distribution by condition."""
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.violinplot(data=df, x="condition", y="iss_score", ax=ax, inner="box")
    ax.set_ylabel("Industry Specificity Score (1-5)")
    ax.set_xlabel("Generation Condition")
    ax.set_title("DV3: Industry Specificity Score Distribution")
    ax.set_ylim(0, 5.5)
    plt.tight_layout()
    plt.savefig(os.path.join(config.FIGURES_DIR, "iss_distribution.png"), dpi=150)
    plt.close()


def plot_fdr_comparison(df: pd.DataFrame):
    """Grouped bar chart comparing FDR-design vs FDR-execution."""
    design = df.groupby("condition")["design_covered"].mean().reset_index()
    design.columns = ["condition", "rate"]
    design["stage"] = "FDR-design"

    execution = df.groupby("condition")["execution_detected"].mean().reset_index()
    execution.columns = ["condition", "rate"]
    execution["stage"] = "FDR-execution"

    combined = pd.concat([design, execution])
    combined["rate_pct"] = combined["rate"] * 100

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=combined, x="condition", y="rate_pct", hue="stage", ax=ax)
    ax.set_ylabel("Fault Detection Rate (%)")
    ax.set_xlabel("Generation Condition")
    ax.set_title("DV2: Fault Detection Rate (Design vs. Execution)")
    ax.set_ylim(0, 100)
    ax.legend(title="Stage")
    plt.tight_layout()
    plt.savefig(os.path.join(config.FIGURES_DIR, "fdr_comparison.png"), dpi=150)
    plt.close()


def plot_summary_radar(condition_scores: dict):
    """Radar chart summarizing all DVs per condition."""
    categories = ["RC", "FDR-design", "FDR-exec", "ISS (norm)", "AC"]
    n_cats = len(categories)
    angles = [n / float(n_cats) * 2 * np.pi for n in range(n_cats)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

    for (cond, scores), color in zip(condition_scores.items(), colors):
        values = [scores.get(c, 0) for c in categories]
        values += values[:1]
        ax.plot(angles, values, "o-", linewidth=2, label=cond, color=color)
        ax.fill(angles, values, alpha=0.1, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=11)
    ax.set_ylim(0, 1)
    ax.set_title("RA-6 Pilot: Multi-DV Summary by Condition", pad=20, fontsize=13)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    plt.tight_layout()
    plt.savefig(os.path.join(config.FIGURES_DIR, "summary_radar.png"), dpi=150)
    plt.close()


def run_analysis():
    """Run full analysis pipeline."""
    coverage, fdr = load_results()

    os.makedirs(config.FIGURES_DIR, exist_ok=True)

    # Build dataframes
    rc_df = build_rc_dataframe(coverage)
    iss_df = build_iss_dataframe(coverage)
    fdr_df = build_fdr_dataframe(fdr)
    ac_df = build_ac_dataframe(coverage)

    print(f"Data loaded: RC={len(rc_df)} rows, ISS={len(iss_df)}, FDR={len(fdr_df)}, AC={len(ac_df)}")

    results = {}

    # H1: RC
    if len(rc_df) > 0:
        print("\n=== H1: Regulatory Coverage ===")
        h1 = friedman_with_posthoc(rc_df, "covered", "H1_RC")
        results["H1_RC"] = h1
        print(f"  Friedman chi2={h1.get('chi2')}, p={h1.get('p_value')}")
        for c, m in h1.get("condition_means", {}).items():
            print(f"  {c}: {m:.1%}")
        plot_rc_by_condition(rc_df)

    # H2: FDR-design
    if len(fdr_df) > 0:
        print("\n=== H2: FDR-design ===")
        # Use fault_id as the grouping key
        h2 = friedman_with_posthoc(fdr_df, "design_covered", "H2_FDR_design")
        results["H2_FDR_design"] = h2
        print(f"  Friedman chi2={h2.get('chi2')}, p={h2.get('p_value')}")
        plot_fdr_comparison(fdr_df)

    # H3: ISS
    if len(iss_df) > 0:
        print("\n=== H3: Industry Specificity ===")
        h3 = friedman_with_posthoc(iss_df, "iss_score", "H3_ISS")
        results["H3_ISS"] = h3
        print(f"  Friedman chi2={h3.get('chi2')}, p={h3.get('p_value')}")
        for c, m in h3.get("condition_means", {}).items():
            print(f"  {c}: {m:.2f}/5.0")
        plot_iss_distribution(iss_df)

    # H4: AC (expect non-significant)
    if len(ac_df) > 0:
        print("\n=== H4: Adversarial Coverage ===")
        h4 = friedman_with_posthoc(ac_df, "covered", "H4_AC")
        results["H4_AC"] = h4
        print(f"  Friedman chi2={h4.get('chi2')}, p={h4.get('p_value')}")
        print(f"  Expected: non-significant (adversarial coverage is not ontology-dependent)")

    # Summary radar
    if len(rc_df) > 0:
        condition_scores = {}
        for cond in config.CONDITIONS:
            rc_mean = rc_df[rc_df["condition"] == cond]["covered"].mean() if len(rc_df) > 0 else 0
            fdr_d = fdr_df[fdr_df["condition"] == cond]["design_covered"].mean() if len(fdr_df) > 0 else 0
            fdr_e = fdr_df[fdr_df["condition"] == cond]["execution_detected"].mean() if len(fdr_df) > 0 else 0
            iss_mean = iss_df[iss_df["condition"] == cond]["iss_score"].mean() / 5.0 if len(iss_df) > 0 else 0
            ac_mean = ac_df[ac_df["condition"] == cond]["covered"].mean() if len(ac_df) > 0 else 0
            condition_scores[cond] = {
                "RC": rc_mean,
                "FDR-design": fdr_d,
                "FDR-exec": fdr_e,
                "ISS (norm)": iss_mean,
                "AC": ac_mean,
            }
        plot_summary_radar(condition_scores)
        results["condition_summary"] = condition_scores

    # Save
    with open(config.ANALYSIS_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nAnalysis saved to {config.ANALYSIS_FILE}")
    print(f"Figures saved to {config.FIGURES_DIR}/")

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="RA-6 Analysis")
    parser.add_argument("--output-suffix", type=str, default=None,
                        help="Analyze suffixed results (e.g. qwen72b, gemma4)")
    args = parser.parse_args()
    if args.output_suffix:
        config.OUTPUT_SUFFIX = config._normalize_suffix(args.output_suffix)
        config.COVERAGE_FILE = config._suffixed("coverage_results", ".json")
        config.FDR_FILE = config._suffixed("fdr_results", ".json")
        config.ANALYSIS_FILE = config._suffixed("analysis_summary", ".json")
    run_analysis()
