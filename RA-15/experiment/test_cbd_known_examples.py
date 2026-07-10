#!/usr/bin/env python3
"""Known cyclic-system checks for the RA-15 CbD summary implementation."""

from __future__ import annotations

from analyze_cbd import CONTEXT_PAIRS, summarize_group


LABELS = {
    "q1": {1: "clear_to_continue", -1: "hold_for_review"},
    "q2": {1: "high_risk", -1: "not_high_risk"},
    "q3": {1: "escalate", -1: "no_escalate"},
    "q4": {1: "evidence_ready_for_action", -1: "evidence_not_ready_for_action"},
}


def _record(context_id: str, signs: dict[str, int]) -> dict[str, object]:
    return {
        "context_id": context_id,
        "_parsed_response": {
            q_field: LABELS[q_field][sign] for q_field, sign in signs.items()
        },
    }


def _balanced_pair_records(context_id: str, correlation: int, reps: int = 12) -> list[dict[str, object]]:
    q_a, q_b = CONTEXT_PAIRS[context_id]
    if correlation == 1:
        pairs = [(1, 1), (-1, -1)]
    elif correlation == -1:
        pairs = [(1, -1), (-1, 1)]
    else:
        raise ValueError("Only deterministic +/-1 correlation fixtures are supported.")

    records: list[dict[str, object]] = []
    for index in range(reps):
        sign_a, sign_b = pairs[index % 2]
        records.append(_record(context_id, {q_a: sign_a, q_b: sign_b}))
    return records


def balanced_group(correlations: dict[str, int], reps: int = 12) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for context_id in ("C1", "C2", "C3", "C4"):
        records.extend(_balanced_pair_records(context_id, correlations[context_id], reps))
    return records


def direct_influence_only_group(reps: int = 12) -> list[dict[str, object]]:
    fixed_signs = {
        "C1": {"q1": 1, "q2": 1},
        "C2": {"q2": 1, "q3": 1},
        "C3": {"q3": 1, "q4": 1},
        "C4": {"q4": -1, "q1": -1},
    }
    records: list[dict[str, object]] = []
    for context_id, signs in fixed_signs.items():
        records.extend(_record(context_id, signs) for _ in range(reps))
    return records


def legacy_positive_canonical_zero_group(reps: int = 12) -> list[dict[str, object]]:
    records = []
    records.extend(_balanced_pair_records("C1", 1, reps))
    records.extend(_record("C2", {"q2": 1, "q3": 1}) for _ in range(reps))
    records.extend(_record("C3", {"q3": 1, "q4": 1}) for _ in range(reps))
    records.extend(_record("C4", {"q4": 1, "q1": -1}) for _ in range(reps))
    return records


def stable_deterministic_group(reps: int = 12) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for context_id, (q_a, q_b) in CONTEXT_PAIRS.items():
        records.extend(_record(context_id, {q_a: 1, q_b: 1}) for _ in range(reps))
    return records


def assert_close(name: str, observed: float, expected: float) -> None:
    if abs(observed - expected) > 1e-9:
        raise AssertionError(f"{name}: expected {expected}, observed {observed}")


def check_example(
    name: str,
    records: list[dict[str, object]],
    expected_s_odd: float,
    expected_di_total: float,
    expected_legacy_cntx: float,
    expected_canonical_cntx: float,
) -> None:
    summary = summarize_group(records)
    assert_close(f"{name} S_odd", summary["s_odd"], expected_s_odd)
    assert_close(f"{name} DI_total", summary["di_total"], expected_di_total)
    assert_close(
        f"{name} legacy probability-drift CNTX",
        summary["cntx_legacy_probability_drift"],
        expected_legacy_cntx,
    )
    assert_close(f"{name} canonical CNTX", summary["cntx"], expected_canonical_cntx)
    print(
        f"{name}: S_odd={summary['s_odd']:.3f}, "
        f"DI_prob_total={summary['di_total']:.3f}, "
        f"CNTX_legacy={summary['cntx_legacy_probability_drift']:.3f}, "
        f"CNTX_canonical={summary['cntx']:.3f}"
    )


def main() -> int:
    check_example(
        "stable_deterministic",
        stable_deterministic_group(),
        expected_s_odd=2.0,
        expected_di_total=0.0,
        expected_legacy_cntx=0.0,
        expected_canonical_cntx=0.0,
    )
    check_example(
        "balanced_noncontextual",
        balanced_group({"C1": 1, "C2": 1, "C3": 1, "C4": 1}),
        expected_s_odd=2.0,
        expected_di_total=0.0,
        expected_legacy_cntx=0.0,
        expected_canonical_cntx=0.0,
    )
    check_example(
        "balanced_contextual_pr_box",
        balanced_group({"C1": 1, "C2": 1, "C3": 1, "C4": -1}),
        expected_s_odd=4.0,
        expected_di_total=0.0,
        expected_legacy_cntx=2.0,
        expected_canonical_cntx=1.0,
    )
    check_example(
        "legacy_positive_canonical_zero",
        legacy_positive_canonical_zero_group(),
        expected_s_odd=4.0,
        expected_di_total=1.0,
        expected_legacy_cntx=1.0,
        expected_canonical_cntx=0.0,
    )
    check_example(
        "direct_influence_only",
        direct_influence_only_group(),
        expected_s_odd=2.0,
        expected_di_total=2.0,
        expected_legacy_cntx=0.0,
        expected_canonical_cntx=0.0,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
