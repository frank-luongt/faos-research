"""Offline corpus checks and explicit missingness; no model or judge execution."""
import hashlib
import json
import math
from pathlib import Path

METRICS = ("TF", "MA", "RC", "RS")
DOMAINS = {"banking", "insurance", "healthcare", "securities", "payments", "accounting"}
JURISDICTIONS = {"US", "VN", "SG"}
MISSING_REASONS = {"judge_missing", "generation_failed", "undefined_denominator"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def keyed(rows, key):
    result = {row[key]: row for row in rows}
    require(len(result) == len(rows), f"Duplicate {key}")
    return result


def validate_corpus(corpus, root):
    """Validate this preparation package, not legal correctness or launch readiness."""
    require(corpus["status"] == "DRAFT_CONTENT_PILOT", "Unsupported corpus status")
    cells = keyed(corpus["cells"], "cell_id")
    expected = {(d, j) for d in DOMAINS for j in JURISDICTIONS}
    actual = {(c["domain"], c["jurisdiction"]) for c in cells.values()}
    require(len(cells) == 18 and actual == expected, "Expected six domains by three jurisdictions")
    for cell in cells.values():
        require(cell["scope"] and cell["exclusions"] and cell["subjurisdiction"], "Incomplete cell scope")
    sources = keyed(corpus["sources"], "source_id")
    root = Path(root).resolve()
    for source in sources.values():
        note = (root / source["evidence_note_path"]).resolve()
        require(note.is_relative_to(root), "Evidence path escapes package")
        require(hashlib.sha256(note.read_bytes()).hexdigest() == source["evidence_note_sha256"], "Evidence note hash mismatch")
        require(source["archive_sha256"] is None, "This package does not contain source archives")
        require(source["retrieval_status"] == "WEB_TEXT_RETRIEVED", "Unsupported evidence status")
        require(source["url"].startswith("https://") and source["retrieved_on"], "Source provenance missing")
    facts = keyed(corpus["facts"], "fact_id")
    for fact in facts.values():
        require(fact["cell_id"] in cells, "Unknown fact cell")
        require(fact["source_ids"] and set(fact["source_ids"]) <= sources.keys(), "Unknown fact source")
        require(fact["shared_fact_family"] and fact["reference_fact"] and fact["version_scope"], "Incomplete fact")
        require(fact["allowed_use"] in {"task", "probe"}, "Fact must have one assigned use")
        require(fact["review_disposition"] == "DRAFT_PENDING_INDEPENDENT_REVIEW", "No reviewed facts in this draft")
    items = corpus["tasks"] + corpus["probes"]
    keyed(items, "item_id")
    families = {"task": set(), "probe": set()}
    for kind, group in (("task", corpus["tasks"]), ("probe", corpus["probes"])):
        for item in group:
            require(item["cell_id"] in cells and item["prompt"], "Incomplete item")
            require(item["fact_ids"] and set(item["fact_ids"]) <= facts.keys(), "Unknown item fact")
            for fact_id in item["fact_ids"]:
                fact = facts[fact_id]
                require(fact["cell_id"] == item["cell_id"], "Fact and item cells differ")
                require(fact["allowed_use"] == kind, "Fact reused across task/probe split")
                families[kind].add(fact["shared_fact_family"])
            require(item["status"] == "DRAFT_PENDING_INDEPENDENT_REVIEW", "No launch-ready items in this draft")
            require(set(item["metric_eligibility"]) == set(METRICS), "Every metric needs eligibility")
            for metric, spec in item["metric_eligibility"].items():
                require(type(spec["eligible"]) is bool and spec["reason"], "Invalid eligibility")
                if spec["eligible"]:
                    require(item["reference_keys"].get(metric) and spec["rubric_id"], "Eligible metric needs reference and rubric")
                else:
                    require(spec["rubric_id"] is None and metric not in item["reference_keys"], "Ineligible metric has a scoring key")
    require(not families["task"] & families["probe"], "Task/probe conceptual family overlap")
    return {
        "status": "STRUCTURAL_CHECKS_PASS_NOT_CONTENT_QUALIFICATION",
        "cells_scoped": len(cells), "source_records": len(sources),
        "draft_facts": len(facts), "draft_tasks": len(corpus["tasks"]),
        "draft_probes": len(corpus["probes"]),
        "ma_rs_candidate_tasks": sum(all(t["metric_eligibility"][m]["eligible"] for m in ("MA", "RS")) for t in corpus["tasks"]),
        "launch_ready_cells": 0,
        "overlap_check": "NO_PROBES_YET" if not corpus["probes"] else "DECLARED_FAMILIES_DISJOINT",
    }


def normalize_scores(item, scores, missing_reason=None):
    """Preserve actual zero; represent unscored and failed metrics with null.

    Only validates already-assigned scores. It does not judge responses, resolve
    zero denominators, impute missing values, or authorize complete-case means.
    """
    require(set(scores) <= set(METRICS), "Unknown metric")
    require(set(item["metric_eligibility"]) == set(METRICS), "Incomplete eligibility")
    require(missing_reason is None or missing_reason in MISSING_REASONS, "Unknown missingness reason")
    result = {}
    for metric in METRICS:
        eligible = item["metric_eligibility"][metric]["eligible"]
        require(type(eligible) is bool, "Eligibility must be boolean")
        score = scores.get(metric)
        if not eligible:
            require(score is None, f"{metric}: score supplied for ineligible metric")
            status = "not_eligible"
        elif score is None:
            require(missing_reason is not None, f"{metric}: missing score needs a reason")
            status = missing_reason
        else:
            require(type(score) in (int, float) and math.isfinite(score) and 0 <= score <= 1, f"{metric}: invalid score")
            status = "observed"
        result[metric] = {"eligible": eligible, "score": score, "status": status}
    return result


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    print(json.dumps(validate_corpus(json.loads((root / "corpus.json").read_text()), root), indent=2))
