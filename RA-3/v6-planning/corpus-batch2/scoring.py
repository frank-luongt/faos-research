"""Offline arithmetic on adjudicated annotations, not an automated text judge."""
import math

REFERENCE_LABELS = {"correct", "incorrect", "pending"}
COVERAGE_LABELS = REFERENCE_LABELS | {"omitted"}
RS_DIMENSIONS = {"decision_pattern", "metric_alignment", "communication_style"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def score_annotations(references, coverage, required_ids, response_status="answered"):
    """Preserve legacy reference precision; report completeness separately.

    Each reference is an adjudicated distinct semantic claim, with a stable ID,
    a verdict and evidence. Coverage is independently adjudicated against the
    frozen requested-answer IDs. This function does not extract either from text.
    """
    require(response_status in {"answered", "abstained", "generation_failed"}, "Unknown response status")
    require(required_ids and len(set(required_ids)) == len(required_ids), "Required-answer IDs must be nonempty and unique")
    require(set(coverage) == set(required_ids), "Coverage must retain the full requested denominator")
    require(all(v in COVERAGE_LABELS for v in coverage.values()), "Unknown coverage label")
    ids = [r["reference_id"] for r in references]
    require(all(ids) and len(set(ids)) == len(ids), "Duplicate or empty reference ID")
    for ref in references:
        require(ref["verdict"] in REFERENCE_LABELS and ref["evidence"].strip(), "Invalid reference annotation")
    if response_status == "generation_failed":
        require(not references and set(coverage.values()) == {"pending"}, "Transport failure cannot contain scored content")
        return {"precision": None, "precision_status": "generation_failed", "completeness": None,
                "completeness_status": "generation_failed", "reference_count": 0, "required_count": len(required_ids)}
    if response_status == "abstained":
        require(not references and set(coverage.values()) == {"omitted"}, "Abstention contains contradictory annotations")
    require(bool(references) or "correct" not in coverage.values(), "Correct coverage without any reference")
    if not references:
        precision, pstatus = None, "undefined_denominator"
    elif any(r["verdict"] == "pending" for r in references):
        precision, pstatus = None, "adjudication_pending"
    else:
        precision = sum(r["verdict"] == "correct" for r in references) / len(references)
        pstatus = "observed"
    if "pending" in coverage.values():
        completeness, cstatus = None, "adjudication_pending"
    else:
        completeness = sum(v == "correct" for v in coverage.values()) / len(required_ids)
        cstatus = "observed"
    return {"precision": precision, "precision_status": pstatus,
            "completeness": completeness, "completeness_status": cstatus,
            "reference_count": len(references), "required_count": len(required_ids)}


def score_role(dimensions):
    """Mean of the three candidate anchored RS ratings; null if any is pending."""
    require(set(dimensions) == RS_DIMENSIONS, "All three RS dimensions are required")
    for value in dimensions.values():
        require(value is None or (type(value) in (int, float) and value in (0, 0.5, 1)), "Invalid RS anchor")
    if any(v is None for v in dimensions.values()):
        return {"score": None, "status": "adjudication_pending"}
    return {"score": sum(dimensions.values()) / 3, "status": "observed"}


def paired_lift_bounds(c1, c3):
    """Support bounds for one eligible C3-C1 pair; not confidence intervals.

    Null represents an unavailable score on an eligible task. Ineligible tasks
    must be excluded by the prespecified eligibility contract before this call.
    """
    for score in (c1, c3):
        require(score is None or (type(score) in (int, float) and math.isfinite(score) and 0 <= score <= 1), "Invalid score")
    lo1, hi1 = (0, 1) if c1 is None else (c1, c1)
    lo3, hi3 = (0, 1) if c3 is None else (c3, c3)
    return {"lower": lo3 - hi1, "upper": hi3 - lo1,
            "status": "point" if c1 is not None and c3 is not None else "support_bound"}
