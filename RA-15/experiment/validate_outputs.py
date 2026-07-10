#!/usr/bin/env python3
"""Validate RA-15 pilot JSONL outputs against context-specific binary schemas."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ALLOWED_LABELS: dict[str, set[str]] = {
    "q1": {
        "clear_to_continue",
        "hold_for_review",
        "action_permitted_in_principle",
        "action_not_permitted_in_principle",
    },
    "q2": {"high_risk", "not_high_risk"},
    "q3": {"escalate", "no_escalate"},
    "q4": {
        "sufficient",
        "insufficient",
        "evidence_ready_for_action",
        "evidence_not_ready_for_action",
        "evidence_packet_ready",
        "evidence_packet_not_ready",
    },
}

CONTEXT_FIELDS: dict[str, list[str]] = {
    "C1": ["q1", "q2"],
    "C2": ["q2", "q3"],
    "C3": ["q3", "q4"],
    "C4": ["q4", "q1"],
    "C1X": ["q1", "q2"],
    "C2X": ["q2", "q3"],
    "C3X": ["q3", "q4"],
    "C4X": ["q4", "q1"],
}

Q_FIELDS = {"q1", "q2", "q3", "q4"}
REQUIRED_META = {"task_id", "block", "context_id", "rep", "model", "response"}


def extract_json_object(value: Any) -> tuple[dict[str, Any] | None, str | None]:
    if isinstance(value, dict):
        return value, None
    if not isinstance(value, str):
        return None, "response must be a JSON object or a string containing one"

    text = value.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return None, "response string does not contain a JSON object"
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            return None, f"response JSON parse error: {exc}"

    if not isinstance(parsed, dict):
        return None, "parsed response is not a JSON object"
    return parsed, None


def validate_record(record: dict[str, Any], line_no: int) -> list[str]:
    errors: list[str] = []

    missing_meta = sorted(REQUIRED_META - set(record))
    if missing_meta:
        errors.append(f"line {line_no}: missing metadata fields {missing_meta}")
        return errors

    context_id = str(record["context_id"])
    expected_fields = CONTEXT_FIELDS.get(context_id)
    if expected_fields is None:
        errors.append(f"line {line_no}: unknown context_id {context_id!r}")
        return errors

    response, parse_error = extract_json_object(record["response"])
    if parse_error:
        errors.append(f"line {line_no}: {parse_error}")
        return errors
    assert response is not None

    expected_key_set = set(expected_fields) | {"rationale"}
    actual_key_set = set(response)
    extra_keys = sorted(actual_key_set - expected_key_set)
    missing_keys = sorted(expected_key_set - actual_key_set)

    if extra_keys:
        errors.append(f"line {line_no}: unexpected response keys {extra_keys}")
    if missing_keys:
        errors.append(f"line {line_no}: missing response keys {missing_keys}")

    unmeasured_q = sorted((actual_key_set & Q_FIELDS) - set(expected_fields))
    if unmeasured_q:
        errors.append(f"line {line_no}: includes unmeasured q fields {unmeasured_q}")

    for field in expected_fields:
        value = response.get(field)
        if value not in ALLOWED_LABELS[field]:
            errors.append(
                f"line {line_no}: {field} has invalid label {value!r}; "
                f"allowed={sorted(ALLOWED_LABELS[field])}"
            )

    rationale = response.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        errors.append(f"line {line_no}: rationale must be a non-empty string")
    elif len(rationale.split()) > 80:
        errors.append(f"line {line_no}: rationale exceeds 80 words")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="JSONL file of model outputs")
    args = parser.parse_args()

    total = 0
    invalid = 0
    all_errors: list[str] = []

    with args.input.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            total += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                invalid += 1
                all_errors.append(f"line {line_no}: record JSON parse error: {exc}")
                continue
            if not isinstance(record, dict):
                invalid += 1
                all_errors.append(f"line {line_no}: record must be a JSON object")
                continue

            errors = validate_record(record, line_no)
            if errors:
                invalid += 1
                all_errors.extend(errors)

    valid = total - invalid
    print(json.dumps({"total": total, "valid": valid, "invalid": invalid}, indent=2))

    if all_errors:
        print("\nValidation errors:", file=sys.stderr)
        for error in all_errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
