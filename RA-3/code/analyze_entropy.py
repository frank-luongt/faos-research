#!/usr/bin/env python3
"""RA-3 Retroactive Entropy Analysis.

Computes entropy-based metrics from existing RA-3 experimental data (1,800 runs
across 3 models) to test whether entropy measures predict Inverse PKE and
ontology grounding effects.

Five entropy analyses:
  E1 — Score Distribution Entropy: H(scores) per condition × metric
  E2 — Repetition Variability Entropy: Cross-rep variance as uncertainty proxy
  E3 — Judge Detail Entropy: Term/metric/regulation diversity from judge JSON
  E4 — Cross-Model Agreement Entropy: Inter-model score divergence
  E5 — Ontology Structural Entropy: Graph entropy of industry ontology files

Usage:
    python analyze_entropy.py                     # Full analysis
    python analyze_entropy.py --models-only       # E4 cross-model only
    python analyze_entropy.py --ontology-only     # E5 ontology entropy only

Output:
    results/entropy_analysis.json    — Full numerical results
    results/figures_entropy/         — Publication-quality figures

Citation context:
    Farquhar et al. (2024) Nature 630:625  — Semantic entropy
    Wei et al. (2025) arXiv:2505.07184     — Structural entropy for KG
    Su et al. (2025) IJCAI Survey          — Structural entropy theory

Author: Dr. FrankL session, 2026-04-14
"""

import argparse
import json
import math
import os
import sys
from collections import Counter
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

import config

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CONDITION_ORDER = ["C1_ungrounded", "C2_rag", "C3_ontology", "C4_ontology_process"]
CONDITION_LABELS = {
    "C1_ungrounded": "C1: Ungrounded",
    "C2_rag": "C2: RAG",
    "C3_ontology": "C3: Ontology",
    "C4_ontology_process": "C4: Onto+Process",
}
CONDITION_SHORT = {
    "C1_ungrounded": "C1",
    "C2_rag": "C2",
    "C3_ontology": "C3",
    "C4_ontology_process": "C4",
}
METRICS = ["TF", "MA", "RC", "RS"]
INDUSTRIES = config.INDUSTRIES
EN_INDUSTRIES = ["fintech", "insurance", "healthcare"]
VN_INDUSTRIES = ["banking_vn", "insurance_vn"]

RESULTS_DIR = config.RESULTS_DIR
ENTROPY_DIR = os.path.join(RESULTS_DIR, "figures_entropy")

MODEL_FILES = {
    "Claude Sonnet 4": os.path.join(RESULTS_DIR, "results_raw.csv"),
    "Qwen 2.5 72B": os.path.join(RESULTS_DIR, "results_raw_qwen72b.csv"),
    "Gemma 4 26B": os.path.join(RESULTS_DIR, "results_raw_gemma4_26b.csv"),
}


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def shannon_entropy(values: list[float], bins: int = 10) -> float:
    """Compute Shannon entropy of a distribution of continuous values.

    Uses histogram binning to estimate probability distribution.
    Returns entropy in bits (log base 2).
    """
    if len(values) < 2:
        return 0.0
    counts, _ = np.histogram(values, bins=bins, range=(0.0, 1.0))
    probs = counts / counts.sum()
    probs = probs[probs > 0]
    return float(-np.sum(probs * np.log2(probs)))


def discrete_entropy(labels: list[str]) -> float:
    """Shannon entropy of discrete labels (bits)."""
    if not labels:
        return 0.0
    counter = Counter(labels)
    total = sum(counter.values())
    probs = np.array([c / total for c in counter.values()])
    probs = probs[probs > 0]
    return float(-np.sum(probs * np.log2(probs)))


def variance_entropy(values: list[float]) -> float:
    """Differential entropy of a Gaussian estimated from sample variance.

    h(X) = 0.5 * ln(2*pi*e*sigma^2) / ln(2)  [bits]

    Higher variance → higher entropy → more uncertain.
    """
    if len(values) < 2:
        return 0.0
    var = np.var(values, ddof=1)
    if var <= 0:
        return 0.0
    return float(0.5 * np.log2(2 * np.pi * np.e * var))


def load_model_data(filepath: str) -> pd.DataFrame:
    """Load and deduplicate a model's results CSV."""
    df = pd.read_csv(filepath)
    for m in METRICS:
        df[m] = pd.to_numeric(df[m], errors="coerce").fillna(0.0)
    df = df.drop_duplicates(subset=["task_id", "condition", "rep"], keep="last")
    return df


def safe_json_parse(s: str) -> dict:
    """Safely parse judge_detail JSON."""
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return {}


# ---------------------------------------------------------------------------
# E1: Score Distribution Entropy
# ---------------------------------------------------------------------------

def e1_score_distribution_entropy(df: pd.DataFrame) -> dict:
    """Compute Shannon entropy of score distributions per condition × metric.

    Hypothesis: Ontology grounding (C3/C4) should produce LOWER entropy
    (more concentrated scores → more certain agent behavior) compared to
    C1 (ungrounded). If entropy INCREASES with ontology for some metrics,
    this signals Inverse PKE (destructive interference).
    """
    results = {}
    for cond in CONDITION_ORDER:
        cond_df = df[df["condition"] == cond]
        for metric in METRICS:
            # Filter to tasks that test this metric
            metric_df = cond_df[
                (cond_df["metric_tested"] == metric) |
                (cond_df["metric_tested"] == "ALL")
            ]
            scores = metric_df[metric].dropna().tolist()
            h = shannon_entropy(scores, bins=10)
            results[f"{CONDITION_SHORT[cond]}_{metric}"] = {
                "entropy_bits": round(h, 4),
                "mean_score": round(float(np.mean(scores)), 4) if scores else 0.0,
                "std_score": round(float(np.std(scores, ddof=1)), 4) if len(scores) > 1 else 0.0,
                "n": len(scores),
            }

    # Compute delta entropy: ΔH = H(C3) - H(C1) per metric
    deltas = {}
    for metric in METRICS:
        h_c1 = results.get(f"C1_{metric}", {}).get("entropy_bits", 0)
        h_c3 = results.get(f"C3_{metric}", {}).get("entropy_bits", 0)
        h_c2 = results.get(f"C2_{metric}", {}).get("entropy_bits", 0)
        deltas[metric] = {
            "delta_H_C3_C1": round(h_c3 - h_c1, 4),
            "delta_H_C2_C1": round(h_c2 - h_c1, 4),
            "interpretation": (
                "entropy_reduction (constructive)" if h_c3 < h_c1
                else "entropy_increase (destructive/Inverse_PKE)" if h_c3 > h_c1
                else "no_change"
            ),
        }

    return {"per_condition_metric": results, "entropy_deltas": deltas}


# ---------------------------------------------------------------------------
# E1b: Score Distribution Entropy by Industry
# ---------------------------------------------------------------------------

def e1b_score_entropy_by_industry(df: pd.DataFrame) -> dict:
    """Score distribution entropy per industry × condition.

    Tests whether Vietnamese domains (low κ) show entropy reduction
    while English domains (high κ) show entropy increase under ontology.
    """
    results = {}
    for industry in INDUSTRIES:
        ind_df = df[df["industry"] == industry]
        for cond in CONDITION_ORDER:
            cond_df = ind_df[ind_df["condition"] == cond]
            # Use primary metric score per task
            scores = []
            for _, row in cond_df.iterrows():
                mt = row.get("metric_tested", "ALL")
                if mt in METRICS:
                    scores.append(row[mt])
                else:
                    # ALL: average of all metrics
                    scores.append(np.mean([row[m] for m in METRICS]))
            h = shannon_entropy(scores, bins=8)
            results[f"{industry}_{CONDITION_SHORT[cond]}"] = {
                "entropy_bits": round(h, 4),
                "mean_score": round(float(np.mean(scores)), 4) if scores else 0.0,
                "n": len(scores),
            }

    # Delta H per industry
    deltas = {}
    for industry in INDUSTRIES:
        h_c1 = results.get(f"{industry}_C1", {}).get("entropy_bits", 0)
        h_c3 = results.get(f"{industry}_C3", {}).get("entropy_bits", 0)
        deltas[industry] = {
            "delta_H_C3_C1": round(h_c3 - h_c1, 4),
            "domain_type": "Vietnamese" if industry in VN_INDUSTRIES else "English",
            "interpretation": (
                "entropy_reduction" if h_c3 < h_c1
                else "entropy_increase" if h_c3 > h_c1
                else "no_change"
            ),
        }

    # Aggregate: EN vs VN mean delta
    en_deltas = [deltas[i]["delta_H_C3_C1"] for i in EN_INDUSTRIES if i in deltas]
    vn_deltas = [deltas[i]["delta_H_C3_C1"] for i in VN_INDUSTRIES if i in deltas]
    summary = {
        "EN_mean_delta_H": round(float(np.mean(en_deltas)), 4) if en_deltas else 0.0,
        "VN_mean_delta_H": round(float(np.mean(vn_deltas)), 4) if vn_deltas else 0.0,
    }

    return {"per_industry_condition": results, "deltas": deltas, "en_vn_summary": summary}


# ---------------------------------------------------------------------------
# E2: Repetition Variability Entropy (Proxy for Semantic Uncertainty)
# ---------------------------------------------------------------------------

def e2_repetition_entropy(df: pd.DataFrame) -> dict:
    """Compute cross-repetition variance entropy per task × condition.

    With 3 repetitions per (task, condition), variance across reps measures
    output uncertainty. This is a proxy for semantic entropy: high variance
    across repetitions → model is uncertain → high entropy state.

    Hypothesis: C3/C4 should have LOWER rep variance (lower entropy) for
    tasks where ontology helps (constructive interference), but HIGHER
    rep variance for Inverse PKE scenarios.
    """
    results = {}
    for cond in CONDITION_ORDER:
        cond_df = df[df["condition"] == cond]
        task_entropies = []

        for task_id in cond_df["task_id"].unique():
            task_df = cond_df[cond_df["task_id"] == task_id]
            mt = task_df["metric_tested"].iloc[0]

            if mt in METRICS:
                scores = task_df[mt].tolist()
            else:
                # ALL: average across metrics per rep
                scores = [np.mean([row[m] for m in METRICS]) for _, row in task_df.iterrows()]

            ve = variance_entropy(scores)
            task_entropies.append({
                "task_id": task_id,
                "industry": task_df["industry"].iloc[0],
                "metric_tested": mt,
                "scores": [round(s, 3) for s in scores],
                "variance": round(float(np.var(scores, ddof=1)) if len(scores) > 1 else 0.0, 6),
                "variance_entropy_bits": round(ve, 4),
            })

        mean_ve = np.mean([t["variance_entropy_bits"] for t in task_entropies])
        mean_var = np.mean([t["variance"] for t in task_entropies])
        results[CONDITION_SHORT[cond]] = {
            "mean_variance_entropy": round(float(mean_ve), 4),
            "mean_variance": round(float(mean_var), 6),
            "n_tasks": len(task_entropies),
            "tasks": task_entropies,
        }

    # Deltas
    c1_ve = results["C1"]["mean_variance_entropy"]
    c3_ve = results["C3"]["mean_variance_entropy"]
    c2_ve = results["C2"]["mean_variance_entropy"]

    deltas = {
        "delta_VE_C3_C1": round(c3_ve - c1_ve, 4),
        "delta_VE_C2_C1": round(c2_ve - c1_ve, 4),
        "interpretation": (
            "ontology_reduces_uncertainty" if c3_ve < c1_ve
            else "ontology_increases_uncertainty" if c3_ve > c1_ve
            else "no_change"
        ),
    }

    return {"per_condition": {k: {kk: vv for kk, vv in v.items() if kk != "tasks"}
                              for k, v in results.items()},
            "deltas": deltas,
            "task_detail": {k: v["tasks"] for k, v in results.items()}}


# ---------------------------------------------------------------------------
# E3: Judge Detail Entropy (Term/Element Diversity)
# ---------------------------------------------------------------------------

def e3_judge_detail_entropy(df: pd.DataFrame) -> dict:
    """Compute entropy of elements extracted by the judge (terms, metrics, regs).

    For TF tasks: entropy of terms_found distribution
    For MA tasks: entropy of metrics_found distribution
    For RC tasks: entropy of regulations_cited distribution

    Hypothesis: Ontology-grounded responses should use MORE DIVERSE correct
    terms (higher element entropy) but FEWER incorrect terms. The ratio
    H(correct)/H(total) should increase with ontology grounding.
    """
    results = {}

    for cond in CONDITION_ORDER:
        cond_df = df[df["condition"] == cond]
        cond_key = CONDITION_SHORT[cond]

        all_correct = []
        all_incorrect = []
        all_found = []
        correct_counts = []
        incorrect_counts = []

        for _, row in cond_df.iterrows():
            detail = safe_json_parse(str(row.get("judge_detail", "{}")))
            if not detail:
                continue
            mt = row.get("metric_tested", "")

            if mt == "TF":
                correct = detail.get("correct_terms", [])
                incorrect = detail.get("incorrect_terms", [])
                found = detail.get("terms_found", [])
            elif mt == "MA":
                correct = detail.get("correct_metrics", [])
                incorrect = detail.get("incorrect_metrics", [])
                found = detail.get("metrics_found", [])
            elif mt == "RC":
                correct = detail.get("correct_citations", [])
                incorrect = detail.get("incorrect_citations", [])
                found = detail.get("regulations_cited", [])
            else:
                continue

            # Normalize to strings
            correct = [str(x) for x in correct] if isinstance(correct, list) else []
            incorrect = [str(x) for x in incorrect] if isinstance(incorrect, list) else []
            found = [str(x) for x in found] if isinstance(found, list) else []

            all_correct.extend(correct)
            all_incorrect.extend(incorrect)
            all_found.extend(found)
            correct_counts.append(len(correct))
            incorrect_counts.append(len(incorrect))

        h_correct = discrete_entropy(all_correct)
        h_incorrect = discrete_entropy(all_incorrect)
        h_all = discrete_entropy(all_found)

        results[cond_key] = {
            "H_correct_elements": round(h_correct, 4),
            "H_incorrect_elements": round(h_incorrect, 4),
            "H_all_elements": round(h_all, 4),
            "precision_entropy_ratio": round(h_correct / h_all, 4) if h_all > 0 else 0.0,
            "n_correct": len(all_correct),
            "n_incorrect": len(all_incorrect),
            "n_total": len(all_found),
            "mean_correct_per_task": round(float(np.mean(correct_counts)), 2) if correct_counts else 0,
            "mean_incorrect_per_task": round(float(np.mean(incorrect_counts)), 2) if incorrect_counts else 0,
            "incorrect_ratio": round(len(all_incorrect) / len(all_found), 4) if all_found else 0,
        }

    return results


# ---------------------------------------------------------------------------
# E4: Cross-Model Agreement Entropy
# ---------------------------------------------------------------------------

def e4_cross_model_entropy() -> dict:
    """Compute entropy of cross-model score agreement per task × condition.

    For each (task, condition), measure how much the 3 models agree on the
    primary metric score. Low variance across models → low entropy → robust
    finding. High variance → high entropy → model-dependent result.

    Hypothesis: Ontology grounding (C3/C4) should REDUCE cross-model
    disagreement (lower entropy) because the ontology constrains outputs.
    """
    # Load all three model datasets
    dfs = {}
    for model_name, filepath in MODEL_FILES.items():
        if os.path.exists(filepath):
            dfs[model_name] = load_model_data(filepath)
    if len(dfs) < 2:
        return {"error": "Need at least 2 model datasets for cross-model analysis"}

    model_names = list(dfs.keys())
    results = {}

    for cond in CONDITION_ORDER:
        cond_key = CONDITION_SHORT[cond]
        task_agreements = []

        # Get task list from first model
        first_df = list(dfs.values())[0]
        tasks = first_df[first_df["condition"] == cond]["task_id"].unique()

        for task_id in tasks:
            scores = []
            for mn in model_names:
                task_df = dfs[mn][
                    (dfs[mn]["task_id"] == task_id) & (dfs[mn]["condition"] == cond)
                ]
                if task_df.empty:
                    continue
                mt = task_df["metric_tested"].iloc[0]
                if mt in METRICS:
                    score = task_df[mt].mean()  # mean across reps
                else:
                    score = np.mean([task_df[m].mean() for m in METRICS])
                scores.append(score)

            if len(scores) >= 2:
                agreement_var = float(np.var(scores, ddof=1))
                agreement_entropy = variance_entropy(scores)
                task_agreements.append({
                    "task_id": task_id,
                    "model_scores": {mn: round(scores[i], 3)
                                      for i, mn in enumerate(model_names[:len(scores)])},
                    "cross_model_variance": round(agreement_var, 6),
                    "cross_model_entropy": round(agreement_entropy, 4),
                })

        mean_entropy = np.mean([t["cross_model_entropy"] for t in task_agreements])
        mean_var = np.mean([t["cross_model_variance"] for t in task_agreements])
        results[cond_key] = {
            "mean_cross_model_entropy": round(float(mean_entropy), 4),
            "mean_cross_model_variance": round(float(mean_var), 6),
            "n_tasks": len(task_agreements),
        }

    # Delta
    if "C1" in results and "C3" in results:
        c1_cme = results["C1"]["mean_cross_model_entropy"]
        c3_cme = results["C3"]["mean_cross_model_entropy"]
        results["delta_CME_C3_C1"] = round(c3_cme - c1_cme, 4)
        results["interpretation"] = (
            "ontology_aligns_models" if c3_cme < c1_cme
            else "ontology_diverges_models" if c3_cme > c1_cme
            else "no_change"
        )

    return results


# ---------------------------------------------------------------------------
# E5: Ontology Structural Entropy
# ---------------------------------------------------------------------------

def e5_ontology_structural_entropy() -> dict:
    """Compute structural complexity entropy of industry ontology files.

    Measures: node count, depth, branching factor, relation diversity.
    Uses Shannon entropy of the property/concept distribution as a proxy
    for structural entropy (exact SE requires encoding tree decomposition).

    Hypothesis: Industries with higher structural entropy should show
    LARGER ontology grounding effects (more information to inject).
    """
    results = {}

    for industry in INDUSTRIES:
        filepath = os.path.join(config.ONTOLOGY_DIR, f"{industry}.json")
        if not os.path.exists(filepath):
            continue

        with open(filepath) as f:
            ont = json.load(f)

        # Count nodes at each layer
        role_layer = ont.get("role_layer", {})
        domain_layer = ont.get("domain_layer", {})
        interaction_layer = ont.get("interaction_layer", {})
        rag_chunks = ont.get("rag_chunks", [])

        # Role layer: count roles, KPIs, vocabulary
        n_roles = len(role_layer)
        all_kpis = []
        all_vocab = []
        for role_data in role_layer.values():
            all_kpis.extend(role_data.get("kpis", []))
            all_vocab.extend(role_data.get("vocabulary", []))

        # Domain layer: concepts and regulations
        concepts = domain_layer.get("concepts", {})
        regulations = domain_layer.get("regulations", {})
        n_concepts = len(concepts)
        n_regulations = len(regulations)

        # Interaction layer: handoffs
        handoffs = interaction_layer.get("handoffs", {})
        n_handoffs = len(handoffs)

        # Compute layer size distribution entropy
        layer_sizes = [n_roles, n_concepts, n_regulations, n_handoffs]
        total_nodes = sum(layer_sizes)
        if total_nodes > 0:
            layer_probs = np.array([s / total_nodes for s in layer_sizes if s > 0])
            layer_entropy = float(-np.sum(layer_probs * np.log2(layer_probs)))
        else:
            layer_entropy = 0.0

        # Concept property entropy (how many different properties defined)
        concept_property_counts = []
        for cname, cdata in concepts.items():
            if isinstance(cdata, dict):
                concept_property_counts.append(len(cdata))
            else:
                concept_property_counts.append(1)
        concept_entropy = shannon_entropy(
            [c / max(concept_property_counts) if max(concept_property_counts) > 0 else 0
             for c in concept_property_counts],
            bins=5
        ) if concept_property_counts else 0.0

        # Vocabulary diversity entropy
        vocab_entropy = discrete_entropy(all_vocab)

        results[industry] = {
            "n_roles": n_roles,
            "n_concepts": n_concepts,
            "n_regulations": n_regulations,
            "n_handoffs": n_handoffs,
            "n_kpis": len(all_kpis),
            "n_vocab_terms": len(all_vocab),
            "n_rag_chunks": len(rag_chunks),
            "total_nodes": total_nodes,
            "layer_distribution_entropy": round(layer_entropy, 4),
            "concept_property_entropy": round(concept_entropy, 4),
            "vocabulary_diversity_entropy": round(vocab_entropy, 4),
            "composite_structural_entropy": round(
                (layer_entropy + concept_entropy + vocab_entropy) / 3, 4
            ),
        }

    return results


# ---------------------------------------------------------------------------
# Correlation Analysis: Structural Entropy vs Ontology Lift
# ---------------------------------------------------------------------------

def correlate_entropy_with_lift(
    ontology_entropy: dict,
    df: pd.DataFrame,
) -> dict:
    """Correlate ontology structural entropy with ontology grounding lift.

    Tests: Does higher structural entropy → larger C3-C1 score improvement?
    """
    industries = []
    se_values = []
    lifts = []

    for industry in INDUSTRIES:
        if industry not in ontology_entropy:
            continue
        se = ontology_entropy[industry]["composite_structural_entropy"]

        ind_df = df[df["industry"] == industry]
        c1_scores = []
        c3_scores = []
        for _, row in ind_df.iterrows():
            mt = row.get("metric_tested", "ALL")
            if mt in METRICS:
                if row["condition"] == "C1_ungrounded":
                    c1_scores.append(row[mt])
                elif row["condition"] == "C3_ontology":
                    c3_scores.append(row[mt])

        if c1_scores and c3_scores:
            lift = float(np.mean(c3_scores) - np.mean(c1_scores))
            industries.append(industry)
            se_values.append(se)
            lifts.append(lift)

    if len(industries) >= 3:
        r, p = stats.spearmanr(se_values, lifts)
        return {
            "industries": industries,
            "structural_entropy": [round(s, 4) for s in se_values],
            "ontology_lift_C3_C1": [round(l, 4) for l in lifts],
            "spearman_r": round(float(r), 4),
            "spearman_p": round(float(p), 4),
            "interpretation": (
                f"{'Positive' if r > 0 else 'Negative'} correlation (r={r:.3f}, p={p:.3f}): "
                f"{'higher structural entropy → larger ontology lift' if r > 0 else 'higher structural entropy → smaller ontology lift'}"
            ),
        }
    return {"error": "Insufficient data for correlation"}


# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------

def plot_e1_entropy_heatmap(e1_results: dict, output_dir: str) -> str:
    """Heatmap of score distribution entropy: conditions × metrics."""
    data = np.zeros((4, 4))
    for i, cond in enumerate(["C1", "C2", "C3", "C4"]):
        for j, metric in enumerate(METRICS):
            key = f"{cond}_{metric}"
            data[i, j] = e1_results["per_condition_metric"].get(key, {}).get("entropy_bits", 0)

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.heatmap(
        data,
        xticklabels=METRICS,
        yticklabels=["C1: Ungrounded", "C2: RAG", "C3: Ontology", "C4: Onto+Process"],
        annot=True, fmt=".3f", cmap="RdYlGn_r",
        cbar_kws={"label": "Shannon Entropy (bits)"},
        ax=ax,
    )
    ax.set_title("E1: Score Distribution Entropy by Condition × Metric")
    ax.set_xlabel("Metric")
    ax.set_ylabel("Condition")
    plt.tight_layout()
    path = os.path.join(output_dir, "e1_entropy_heatmap.pdf")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_e1b_industry_entropy(e1b_results: dict, output_dir: str) -> str:
    """Bar chart of ΔH(C3-C1) by industry, colored by EN/VN."""
    deltas = e1b_results["deltas"]
    industries = list(deltas.keys())
    delta_values = [deltas[i]["delta_H_C3_C1"] for i in industries]
    colors = ["#2196F3" if i in EN_INDUSTRIES else "#FF5722" for i in industries]
    labels = [i.replace("_", " ").title() for i in industries]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, delta_values, color=colors, edgecolor="black", linewidth=0.5)
    ax.axhline(y=0, color="black", linewidth=0.8, linestyle="-")
    ax.set_ylabel("ΔH = H(C3) − H(C1)  [bits]")
    ax.set_title("E1b: Entropy Change with Ontology Grounding by Industry")

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#2196F3", label="English domains"),
        Patch(facecolor="#FF5722", label="Vietnamese domains"),
    ]
    ax.legend(handles=legend_elements, loc="upper right")

    # Annotation
    ax.annotate("↓ Entropy reduction\n(constructive)", xy=(0.02, 0.02),
                xycoords="axes fraction", fontsize=8, color="green", va="bottom")
    ax.annotate("↑ Entropy increase\n(destructive/Inverse PKE)", xy=(0.02, 0.98),
                xycoords="axes fraction", fontsize=8, color="red", va="top")

    plt.tight_layout()
    path = os.path.join(output_dir, "e1b_industry_entropy_delta.pdf")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_e2_variability(e2_results: dict, output_dir: str) -> str:
    """Bar chart of mean variance entropy across conditions."""
    conds = ["C1", "C2", "C3", "C4"]
    values = [e2_results["per_condition"][c]["mean_variance_entropy"] for c in conds]
    cond_labels = ["C1: Ungrounded", "C2: RAG", "C3: Ontology", "C4: Onto+Process"]
    colors = ["#9E9E9E", "#FFC107", "#4CAF50", "#2196F3"]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(cond_labels, values, color=colors, edgecolor="black", linewidth=0.5)
    ax.set_ylabel("Mean Variance Entropy (bits)")
    ax.set_title("E2: Repetition Variability Entropy\n(proxy for output uncertainty)")
    ax.annotate("Lower = more deterministic output", xy=(0.5, 0.02),
                xycoords="axes fraction", fontsize=9, ha="center", style="italic")
    plt.tight_layout()
    path = os.path.join(output_dir, "e2_variability_entropy.pdf")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_e3_judge_detail(e3_results: dict, output_dir: str) -> str:
    """Grouped bar chart: correct vs incorrect element counts & entropy."""
    conds = ["C1", "C2", "C3", "C4"]
    correct_counts = [e3_results[c]["n_correct"] for c in conds]
    incorrect_counts = [e3_results[c]["n_incorrect"] for c in conds]
    incorrect_ratios = [e3_results[c]["incorrect_ratio"] for c in conds]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    x = np.arange(len(conds))
    width = 0.35
    ax1.bar(x - width/2, correct_counts, width, label="Correct", color="#4CAF50")
    ax1.bar(x + width/2, incorrect_counts, width, label="Incorrect", color="#F44336")
    ax1.set_xticks(x)
    ax1.set_xticklabels(["C1", "C2", "C3", "C4"])
    ax1.set_ylabel("Count")
    ax1.set_title("E3a: Correct vs Incorrect Elements")
    ax1.legend()

    ax2.bar(conds, incorrect_ratios, color="#FF9800", edgecolor="black", linewidth=0.5)
    ax2.set_ylabel("Incorrect / Total Ratio")
    ax2.set_title("E3b: Error Rate by Condition")
    ax2.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))

    plt.tight_layout()
    path = os.path.join(output_dir, "e3_judge_detail_entropy.pdf")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_e5_structural_vs_lift(corr_results: dict, output_dir: str) -> str:
    """Scatter plot: ontology structural entropy vs ontology lift."""
    if "error" in corr_results:
        return ""

    industries = corr_results["industries"]
    se = corr_results["structural_entropy"]
    lift = corr_results["ontology_lift_C3_C1"]

    fig, ax = plt.subplots(figsize=(7, 5))
    colors = ["#FF5722" if i in VN_INDUSTRIES else "#2196F3" for i in industries]
    ax.scatter(se, lift, c=colors, s=120, edgecolors="black", linewidth=0.5, zorder=5)

    for i, ind in enumerate(industries):
        ax.annotate(ind.replace("_", " ").title(),
                    (se[i], lift[i]), textcoords="offset points",
                    xytext=(8, 4), fontsize=9)

    # Trend line
    if len(se) >= 3:
        z = np.polyfit(se, lift, 1)
        p = np.poly1d(z)
        x_line = np.linspace(min(se) - 0.1, max(se) + 0.1, 50)
        ax.plot(x_line, p(x_line), "--", color="gray", alpha=0.7)

    ax.set_xlabel("Composite Structural Entropy (bits)")
    ax.set_ylabel("Ontology Lift (C3 − C1 mean score)")
    r = corr_results["spearman_r"]
    p_val = corr_results["spearman_p"]
    ax.set_title(f"E5: Structural Entropy vs Ontology Lift\n(Spearman r={r:.3f}, p={p_val:.3f})")

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#2196F3", label="English domains"),
        Patch(facecolor="#FF5722", label="Vietnamese domains"),
    ]
    ax.legend(handles=legend_elements)

    plt.tight_layout()
    path = os.path.join(output_dir, "e5_structural_vs_lift.pdf")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_per_model_entropy(model_name: str, filepath: str, output_dir: str) -> dict:
    """Run E1, E1b, E2, E3 on a single model's data and save figures."""
    model_dir = os.path.join(output_dir, model_name.lower().replace(" ", "_"))
    os.makedirs(model_dir, exist_ok=True)

    df = load_model_data(filepath)
    print(f"\n{'='*60}")
    print(f"  {model_name}: {len(df)} rows")
    print(f"{'='*60}")

    e1 = e1_score_distribution_entropy(df)
    for metric in METRICS:
        d = e1["entropy_deltas"][metric]
        print(f"  E1 {metric}: ΔH(C3-C1) = {d['delta_H_C3_C1']:+.4f} → {d['interpretation']}")
    plot_e1_entropy_heatmap(e1, model_dir)

    e1b = e1b_score_entropy_by_industry(df)
    s = e1b["en_vn_summary"]
    print(f"  E1b EN mean ΔH: {s['EN_mean_delta_H']:+.4f} | VN mean ΔH: {s['VN_mean_delta_H']:+.4f}")
    plot_e1b_industry_entropy(e1b, model_dir)

    e2 = e2_repetition_entropy(df)
    print(f"  E2 ΔVE(C3-C1) = {e2['deltas']['delta_VE_C3_C1']:+.4f} → {e2['deltas']['interpretation']}")
    plot_e2_variability(e2, model_dir)

    e3 = e3_judge_detail_entropy(df)
    for cond in ["C1", "C3"]:
        d = e3[cond]
        print(f"  E3 {cond}: error_rate={d['incorrect_ratio']:.3f}, precision_ratio={d['precision_entropy_ratio']:.3f}")
    plot_e3_judge_detail(e3, model_dir)

    return {
        "model": model_name,
        "n_rows": len(df),
        "E1": e1,
        "E1b": e1b,
        "E2": {"per_condition": e2["per_condition"], "deltas": e2["deltas"]},
        "E3": e3,
    }


def main():
    parser = argparse.ArgumentParser(description="RA-3 Retroactive Entropy Analysis")
    parser.add_argument("--models-only", action="store_true", help="Run E4 cross-model only")
    parser.add_argument("--ontology-only", action="store_true", help="Run E5 ontology entropy only")
    parser.add_argument("--all-models", action="store_true", help="Run E1-E3 on all 3 models")
    parser.add_argument("--output-suffix", default="", help="Output file suffix")
    args = parser.parse_args()

    os.makedirs(ENTROPY_DIR, exist_ok=True)

    # --- All-models mode: run E1-E3 on each model separately ---
    if args.all_models:
        all_model_results = {}
        for model_name, filepath in MODEL_FILES.items():
            if os.path.exists(filepath):
                all_model_results[model_name] = run_per_model_entropy(
                    model_name, filepath, ENTROPY_DIR
                )

        # Cross-model entropy delta comparison table
        print("\n" + "="*70)
        print("CROSS-MODEL ENTROPY DELTA COMPARISON")
        print("="*70)
        print(f"{'Metric':<8} ", end="")
        for mn in all_model_results:
            print(f"  {mn:<18}", end="")
        print()
        for metric in METRICS:
            print(f"{metric:<8} ", end="")
            for mn, mr in all_model_results.items():
                d = mr["E1"]["entropy_deltas"].get(metric, {}).get("delta_H_C3_C1", 0)
                sign = "↓" if d < 0 else "↑" if d > 0 else "="
                print(f"  {d:+.4f} {sign:<11}", end="")
            print()
        print()
        print(f"{'VE(C3-C1)':<8} ", end="")
        for mn, mr in all_model_results.items():
            d = mr["E2"]["deltas"]["delta_VE_C3_C1"]
            sign = "↓" if d < 0 else "↑"
            print(f"  {d:+.4f} {sign:<11}", end="")
        print()

        # Save
        output_file = os.path.join(RESULTS_DIR, "entropy_analysis_all_models.json")
        with open(output_file, "w") as f:
            json.dump(all_model_results, f, indent=2, default=str)
        print(f"\n✓ All-models results saved to {output_file}")
        return

    # Load baseline (Claude) data
    baseline_file = MODEL_FILES["Claude Sonnet 4"]
    print(f"Loading baseline data: {baseline_file}")
    df = load_model_data(baseline_file)
    print(f"  Loaded {len(df)} rows ({df['task_id'].nunique()} tasks)")

    results: dict[str, Any] = {"meta": {
        "analysis": "RA-3 Retroactive Entropy Analysis",
        "date": "2026-04-14",
        "baseline_model": "Claude Sonnet 4",
        "n_rows": len(df),
        "n_tasks": int(df["task_id"].nunique()),
    }}

    if not args.models_only and not args.ontology_only:
        # E1: Score Distribution Entropy
        print("\n=== E1: Score Distribution Entropy ===")
        e1 = e1_score_distribution_entropy(df)
        results["E1_score_distribution_entropy"] = e1
        for metric in METRICS:
            d = e1["entropy_deltas"][metric]
            print(f"  {metric}: ΔH(C3-C1) = {d['delta_H_C3_C1']:+.4f} → {d['interpretation']}")
        plot_e1_entropy_heatmap(e1, ENTROPY_DIR)

        # E1b: By industry
        print("\n=== E1b: Score Entropy by Industry ===")
        e1b = e1b_score_entropy_by_industry(df)
        results["E1b_industry_entropy"] = e1b
        for ind, d in e1b["deltas"].items():
            print(f"  {ind}: ΔH(C3-C1) = {d['delta_H_C3_C1']:+.4f} ({d['domain_type']}) → {d['interpretation']}")
        s = e1b["en_vn_summary"]
        print(f"  EN mean ΔH: {s['EN_mean_delta_H']:+.4f} | VN mean ΔH: {s['VN_mean_delta_H']:+.4f}")
        plot_e1b_industry_entropy(e1b, ENTROPY_DIR)

        # E2: Repetition Variability Entropy
        print("\n=== E2: Repetition Variability Entropy ===")
        e2 = e2_repetition_entropy(df)
        results["E2_repetition_entropy"] = {
            "per_condition": e2["per_condition"],
            "deltas": e2["deltas"],
        }
        for cond in ["C1", "C2", "C3", "C4"]:
            ve = e2["per_condition"][cond]["mean_variance_entropy"]
            var = e2["per_condition"][cond]["mean_variance"]
            print(f"  {cond}: mean_VE = {ve:.4f} bits, mean_var = {var:.6f}")
        print(f"  ΔVE(C3-C1) = {e2['deltas']['delta_VE_C3_C1']:+.4f} → {e2['deltas']['interpretation']}")
        plot_e2_variability(e2, ENTROPY_DIR)

        # E3: Judge Detail Entropy
        print("\n=== E3: Judge Detail Entropy ===")
        e3 = e3_judge_detail_entropy(df)
        results["E3_judge_detail_entropy"] = e3
        for cond in ["C1", "C2", "C3", "C4"]:
            d = e3[cond]
            print(f"  {cond}: correct={d['n_correct']}, incorrect={d['n_incorrect']}, "
                  f"error_rate={d['incorrect_ratio']:.3f}, "
                  f"H_correct={d['H_correct_elements']:.3f}, "
                  f"precision_ratio={d['precision_entropy_ratio']:.3f}")
        plot_e3_judge_detail(e3, ENTROPY_DIR)

    # E4: Cross-Model Agreement Entropy
    if not args.ontology_only:
        print("\n=== E4: Cross-Model Agreement Entropy ===")
        e4 = e4_cross_model_entropy()
        results["E4_cross_model_entropy"] = e4
        if "error" not in e4:
            for cond in ["C1", "C2", "C3", "C4"]:
                if cond in e4:
                    cme = e4[cond]["mean_cross_model_entropy"]
                    cmv = e4[cond]["mean_cross_model_variance"]
                    print(f"  {cond}: mean_CME = {cme:.4f} bits, mean_var = {cmv:.6f}")
            if "delta_CME_C3_C1" in e4:
                print(f"  ΔCME(C3-C1) = {e4['delta_CME_C3_C1']:+.4f} → {e4.get('interpretation', '')}")
        else:
            print(f"  {e4['error']}")

    # E5: Ontology Structural Entropy
    print("\n=== E5: Ontology Structural Entropy ===")
    e5 = e5_ontology_structural_entropy()
    results["E5_ontology_structural_entropy"] = e5
    for ind, d in e5.items():
        print(f"  {ind}: nodes={d['total_nodes']}, "
              f"layer_H={d['layer_distribution_entropy']:.3f}, "
              f"vocab_H={d['vocabulary_diversity_entropy']:.3f}, "
              f"composite={d['composite_structural_entropy']:.3f}")

    # Correlation: SE vs Lift
    if not args.models_only and not args.ontology_only:
        print("\n=== Correlation: Structural Entropy vs Ontology Lift ===")
        corr = correlate_entropy_with_lift(e5, df)
        results["correlation_SE_vs_lift"] = corr
        if "error" not in corr:
            print(f"  Spearman r = {corr['spearman_r']:.4f}, p = {corr['spearman_p']:.4f}")
            print(f"  {corr['interpretation']}")
            for i, ind in enumerate(corr["industries"]):
                print(f"    {ind}: SE={corr['structural_entropy'][i]:.3f}, "
                      f"lift={corr['ontology_lift_C3_C1'][i]:+.3f}")
            plot_e5_structural_vs_lift(corr, ENTROPY_DIR)

    # Save results
    output_file = os.path.join(RESULTS_DIR, "entropy_analysis.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n✓ Results saved to {output_file}")
    print(f"✓ Figures saved to {ENTROPY_DIR}/")


if __name__ == "__main__":
    main()
