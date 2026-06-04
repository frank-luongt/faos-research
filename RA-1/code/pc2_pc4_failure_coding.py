#!/usr/bin/env python3
"""Systematic failure-mode coding for RA-1 PC2 and PC4 coordination-harm rows.

The ScholarPeer review (P2 finding) asked the PC2/PC4 mechanism claims to be
backed by a systematic coding of all low-scoring rows rather than a sampled set
of worst-gap examples. This script codes every coordination-condition row in PC2
and PC4 that under-performs its paired single-agent baseline, using the judge's
own structured rationale fields (not new heuristics on the raw text).

Two judge schemas exist in judge_detail:

- Compliance schema (PC4 RC-tested rows): keys include `incorrect_citations` and
  `requirements_wrong`. These directly encode citation overreach and requirement
  misses.
- Four-metric rubric (PC2 and ALL-tested rows): keys `TF_score`, `MA_score`,
  `RC_score`, `RS_score` with per-dimension rationales. The lowest-scoring
  dimension names the dominant failure mode.

Coordination-harm population: condition in {consensus, debate, synthesis} with a
paired single_agent baseline in the same (model, task, rep) and a negative delta.
Two cuts are reported: any negative delta, and material harm (delta <= -0.05).

Outputs:
- results/pc2_pc4_failure_coding.json
- PC2-PC4-SYSTEMATIC-CODING-2026-05-29.md
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from formal_analysis import default_result_paths, load_rows

EXPERIMENT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = EXPERIMENT_DIR / "results"
DEFAULT_JSON = RESULTS_DIR / "pc2_pc4_failure_coding.json"
DEFAULT_MARKDOWN = EXPERIMENT_DIR / "PC2-PC4-SYSTEMATIC-CODING-2026-05-29.md"

COORD_CONDITIONS = ("consensus", "debate", "synthesis")
PRE_REGISTERED_ARMS = ("sonnet", "qwen_local", "gemma_openrouter")
MATERIAL_CUT = -0.05
SUBMETRIC_LOW = 0.5
BLOAT_RATIO = 1.5

# Codebook label definitions surfaced in the appendix for transparency.
LABEL_DEFINITIONS = {
    # PC4 compliance schema
    "citation_overreach": "Judge marks one or more cited regulations/sanctions lists as incorrect (incorrect_citations non-empty).",
    "requirement_miss": "Judge marks one or more required compliance obligations as wrong or missing (requirements_wrong non-empty).",
    # PC2 / four-metric rubric schema
    "metric_accuracy_loss": "Lowest sub-metric is Metric Accuracy (MA): missing benchmarks, ratios, or quantitative targets.",
    "terminology_incomplete": "Lowest sub-metric is Terminology Fidelity (TF): omits required domain terms.",
    "reasoning_incoherence": "Lowest sub-metric is Reasoning Coherence (RC): thin or unsound argument structure.",
    "instability": "Lowest sub-metric is Response Stability (RS): inconsistent or unreliable output across the rubric.",
    # cross-schema
    "verbosity_bloat": f"Coordination response length >= {BLOAT_RATIO}x the paired single-agent response length.",
}


def parse_judge_detail(raw: str) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except (ValueError, TypeError):
        return None


def parse_len(value: Any) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def code_row(row: dict[str, Any], single_len: int | None) -> dict[str, Any]:
    detail = parse_judge_detail(row.get("judge_detail", ""))
    labels: list[str] = []
    facts: dict[str, Any] = {}
    schema = "unknown"
    if detail is not None:
        if "incorrect_citations" in detail or "requirements_wrong" in detail:
            schema = "compliance"
            incorrect = detail.get("incorrect_citations") or []
            wrong = detail.get("requirements_wrong") or []
            facts["n_incorrect_citations"] = len(incorrect)
            facts["n_requirements_wrong"] = len(wrong)
            if incorrect:
                labels.append("citation_overreach")
            if wrong:
                labels.append("requirement_miss")
        elif any(k in detail for k in ("TF_score", "MA_score", "RC_score", "RS_score")):
            schema = "four_metric"
            submetrics = {
                "TF": detail.get("TF_score"),
                "MA": detail.get("MA_score"),
                "RC": detail.get("RC_score"),
                "RS": detail.get("RS_score"),
            }
            present = {k: v for k, v in submetrics.items() if isinstance(v, (int, float))}
            facts["submetrics"] = present
            if present:
                lowest_value = min(present.values())
                lowest_dims = [k for k, v in present.items() if v == lowest_value]
                facts["lowest_dim"] = lowest_dims
                if lowest_value < SUBMETRIC_LOW:
                    mapping = {
                        "MA": "metric_accuracy_loss",
                        "TF": "terminology_incomplete",
                        "RC": "reasoning_incoherence",
                        "RS": "instability",
                    }
                    for dim in lowest_dims:
                        if mapping[dim] not in labels:
                            labels.append(mapping[dim])
    coord_len = parse_len(row.get("agent_response_len"))
    if coord_len is not None and single_len and coord_len >= BLOAT_RATIO * single_len:
        labels.append("verbosity_bloat")
        facts["len_ratio_vs_single"] = round(coord_len / single_len, 3)
    return {"schema": schema, "labels": labels, "facts": facts}


def analyze(rows: list[dict[str, Any]]) -> dict[str, Any]:
    single_score: dict[tuple[str, str, str], float] = {}
    single_len: dict[tuple[str, str, str], int | None] = {}
    for row in rows:
        if row["condition"] == "single_agent":
            key = (row["model_arm"], row["task_id"], row["rep"])
            single_score[key] = row["quality_score"]
            single_len[key] = parse_len(row.get("agent_response_len"))

    coded: dict[str, list[dict[str, Any]]] = {"PC2": [], "PC4": []}
    for row in rows:
        pc = row["problem_class"]
        if pc not in ("PC2", "PC4") or row["condition"] not in COORD_CONDITIONS:
            continue
        key = (row["model_arm"], row["task_id"], row["rep"])
        base = single_score.get(key)
        if base is None:
            continue
        delta = row["quality_score"] - base
        if delta >= 0:
            continue
        coding = code_row(row, single_len.get(key))
        coded[pc].append(
            {
                "model_arm": row["model_arm"],
                "role": "pre-registered" if row["model_arm"] in PRE_REGISTERED_ARMS else "auxiliary",
                "task_id": row["task_id"],
                "industry": row["industry"],
                "condition": row["condition"],
                "rep": row["rep"],
                "quality_score": round(row["quality_score"], 4),
                "single_agent_score": round(base, 4),
                "delta": round(delta, 4),
                "material": delta <= MATERIAL_CUT,
                "schema": coding["schema"],
                "labels": coding["labels"],
                "facts": coding["facts"],
            }
        )

    def summarize(items: list[dict[str, Any]], material_only: bool) -> dict[str, Any]:
        subset = [x for x in items if x["material"]] if material_only else items
        label_counts: dict[str, int] = defaultdict(int)
        condition_counts: dict[str, int] = defaultdict(int)
        lowest_dim_counts: dict[str, int] = defaultdict(int)
        submetric_values: dict[str, list[float]] = defaultdict(list)
        n_four_metric = 0
        rows_with_any_label = 0
        for x in subset:
            if x["labels"]:
                rows_with_any_label += 1
            for label in set(x["labels"]):
                label_counts[label] += 1
            condition_counts[x["condition"]] += 1
            facts = x.get("facts", {})
            if x["schema"] == "four_metric":
                n_four_metric += 1
                for dim in facts.get("lowest_dim", []):
                    lowest_dim_counts[dim] += 1
                for dim, value in facts.get("submetrics", {}).items():
                    submetric_values[dim].append(value)
        mean_submetrics = {
            dim: round(sum(values) / len(values), 4)
            for dim, values in submetric_values.items()
            if values
        }
        return {
            "n_rows": len(subset),
            "n_rows_with_label": rows_with_any_label,
            "label_counts": dict(sorted(label_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
            "condition_counts": dict(sorted(condition_counts.items())),
            "n_four_metric_rows": n_four_metric,
            "weakest_dimension_counts": dict(sorted(lowest_dim_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
            "mean_submetrics_four_metric": mean_submetrics,
        }

    summary = {}
    for pc in ("PC2", "PC4"):
        summary[pc] = {
            "all_negative": summarize(coded[pc], material_only=False),
            "material_only": summarize(coded[pc], material_only=True),
        }
    return {"coded_rows": coded, "summary": summary, "label_definitions": LABEL_DEFINITIONS}


def pct(part: int, whole: int) -> str:
    return f"{(100.0 * part / whole):.1f}%" if whole else "n/a"


def write_markdown(result: dict[str, Any], load_report: dict[str, Any], path: Path) -> None:
    lines = [
        "# RA-1 PC2/PC4 Systematic Failure-Mode Coding",
        "",
        "Status date: 2026-05-29",
        "",
        "Every coordination-condition row (consensus, debate, synthesis) in PC2 and PC4 that",
        "under-performs its paired single-agent baseline is coded here, using the judge's own",
        "structured rationale fields. This replaces the earlier sampled worst-gap annotation with a",
        "full enumeration. Material harm is a delta of at most -0.05 quality-score points.",
        "",
        f"- Valid unique judged rows loaded: {load_report['valid_unique_rows']}",
        "",
        "## Codebook",
        "",
        "| Label | Schema | Definition |",
        "| --- | --- | --- |",
    ]
    schema_of = {
        "citation_overreach": "compliance",
        "requirement_miss": "compliance",
        "metric_accuracy_loss": "four-metric",
        "terminology_incomplete": "four-metric",
        "reasoning_incoherence": "four-metric",
        "instability": "four-metric",
        "verbosity_bloat": "cross-schema",
    }
    for label, definition in result["label_definitions"].items():
        lines.append(f"| `{label}` | {schema_of.get(label, '')} | {definition} |")

    for pc in ("PC2", "PC4"):
        for cut, cut_label in (("material_only", "material harm, delta <= -0.05"), ("all_negative", "any negative delta")):
            block = result["summary"][pc][cut]
            n = block["n_rows"]
            lines.extend(
                [
                    "",
                    f"## {pc} failure coding ({cut_label})",
                    "",
                    f"- Coordination-harm rows: {n}",
                    f"- Rows with at least one assigned label: {block['n_rows_with_label']} ({pct(block['n_rows_with_label'], n)})",
                    f"- By condition: "
                    + ", ".join(f"{c}={k}" for c, k in block["condition_counts"].items()),
                    "",
                    "| Failure label | Rows | Share of harm rows |",
                    "| --- | ---: | ---: |",
                ]
            )
            for label, count in block["label_counts"].items():
                lines.append(f"| `{label}` | {count} | {pct(count, n)} |")
            if block.get("n_four_metric_rows"):
                nfm = block["n_four_metric_rows"]
                weakest = ", ".join(
                    f"{dim}={cnt} ({pct(cnt, nfm)})" for dim, cnt in block["weakest_dimension_counts"].items()
                )
                means = ", ".join(f"{dim}={val:.3f}" for dim, val in block["mean_submetrics_four_metric"].items())
                lines.extend(
                    [
                        "",
                        f"Four-metric rubric rows: {nfm}. Weakest rubric dimension (lowest sub-metric per row): "
                        + (weakest or "n/a"),
                        f"Mean sub-metric scores across these rows: {means or 'n/a'}.",
                    ]
                )

    # Full coded enumeration (material rows) for the appendix.
    for pc in ("PC2", "PC4"):
        material_rows = [x for x in result["coded_rows"][pc] if x["material"]]
        material_rows.sort(key=lambda x: (x["delta"], x["model_arm"], x["task_id"]))
        lines.extend(
            [
                "",
                f"## {pc} coded rows (material harm, full enumeration)",
                "",
                "| Model | Role | Task | Condition | Rep | Score | Single | Delta | Labels |",
                "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for x in material_rows:
            labels = ", ".join(f"`{l}`" for l in x["labels"]) if x["labels"] else "(none)"
            lines.append(
                "| "
                + " | ".join(
                    [
                        x["model_arm"],
                        x["role"],
                        x["task_id"],
                        x["condition"],
                        str(x["rep"]),
                        f"{x['quality_score']:.3f}",
                        f"{x['single_agent_score']:.3f}",
                        f"{x['delta']:.3f}",
                        labels,
                    ]
                )
                + " |"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", nargs="*", type=Path)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MARKDOWN)
    args = parser.parse_args()

    paths = args.results or default_result_paths()
    rows, load_report = load_rows(paths)
    result = analyze(rows)
    out = {
        "input_files": [str(path) for path in paths],
        "load_report": load_report,
        **result,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(result, load_report, args.output_md)
    digest = {
        pc: {
            "material_rows": result["summary"][pc]["material_only"]["n_rows"],
            "top_labels": list(result["summary"][pc]["material_only"]["label_counts"].items())[:3],
        }
        for pc in ("PC2", "PC4")
    }
    print(json.dumps({"valid_unique_rows": load_report["valid_unique_rows"], "digest": digest, "output_md": str(args.output_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
