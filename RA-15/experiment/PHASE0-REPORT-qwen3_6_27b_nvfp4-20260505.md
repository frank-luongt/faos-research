# RA-15 Phase 0 Smoke-Test Report - Qwen 3.6 27B

**Date:** 2026-05-05
**Model:** `qwen3.6:27b-coding-nvfp4`
**Runner:** [`run_phase0_ollama.py`](run_phase0_ollama.py)
**Output:** [`phase0_outputs_qwen3_6_27b_nvfp4_nojson_20260505.jsonl`](phase0_outputs_qwen3_6_27b_nvfp4_nojson_20260505.jsonl)
**Validator:** [`validate_outputs.py`](validate_outputs.py)
**CbD summary:** [`phase0_cbd_summary_qwen3_6_27b_nvfp4_20260505.json`](phase0_cbd_summary_qwen3_6_27b_nvfp4_20260505.json)

---

## 1. Executive Result

Phase 0 **passes the parser / schema gate** but **does not yet clear the measurement-semantics gate**.

The prompt instrument produced 24/24 valid JSON records with exactly the requested q fields and allowed labels. However, the low-conflict `fintech_T6` task produced a nontrivial contextuality score driven by `q1` label ambiguity. This is useful: Phase 0 caught an instrument-design issue before Phase 1.

**Decision:** Do not run Phase 1 yet. Revise `q1` from the generic `proceed/defer` action posture into a less ambiguous "business posture" or task-specific decision variable, then rerun Phase 0.

---

## 2. Run Notes

An initial attempt using Ollama `format=json` returned HTTP 500 errors for the local Qwen model. The successful run disabled `format=json` and relied on prompt-only JSON instructions.

Command shape:

```bash
python3 research-academic/experiments/RA-15-contextuality-pilot/run_phase0_ollama.py \
  --model qwen3.6:27b-coding-nvfp4 \
  --output research-academic/experiments/RA-15-contextuality-pilot/phase0_outputs_qwen3_6_27b_nvfp4_nojson_20260505.jsonl \
  --temperature 0.2 \
  --timeout 240 \
  --no-json-format
```

The run completed all 24 calls with no runner-level errors.

---

## 3. Validation Result

Validator output:

```json
{
  "total": 24,
  "valid": 24,
  "invalid": 0
}
```

Interpretation:

- Parseability: pass.
- Required measured fields: pass.
- Unmeasured q-field exclusion: pass.
- Allowed labels: pass.
- Rationale presence: pass.

---

## 4. Label Distribution

Across all 24 records:

| Field | Label | Count |
|---|---:|---:|
| q1 | `defer` | 8 |
| q1 | `proceed` | 4 |
| q2 | `high_risk` | 12 |
| q3 | `escalate` | 12 |
| q4 | `insufficient` | 6 |
| q4 | `sufficient` | 6 |

The distribution is sensible for the two tasks:

- `software_T3`: defer, high risk, escalate, insufficient evidence.
- `fintech_T6`: high risk, escalate, sufficient evidence.

The issue is `fintech_T6` q1: the model sometimes treats `defer` as "hold normal processing due to suspicious activity" and sometimes treats `proceed` as "proceed with CTR/SAR compliance action." Both are defensible interpretations under the current label wording.

---

## 5. CbD Smoke Summary

| Task | DI total | CNTX | q1 instability | Interpretation |
|---|---:|---:|---:|---|
| `software_T3` | 0.000 | 0.000 | 0.000 | Stable high-conflict release-posture task under canonical block |
| `fintech_T6` | 0.667 | 0.667 | 0.333 | Apparent contextuality driven by q1 semantic ambiguity, not yet interpretable as true residual contextuality |

The `fintech_T6` result should **not** be treated as evidence that a low-conflict regulatory task is contextual. It is evidence that `q1 = proceed/defer` is underspecified.

---

## 6. Instrument Revision Required

### Problem

`q1` currently means:

> Is the action posture aggressive / proceed?

Labels:

- `proceed`
- `defer`

This works for `software_T3`, where the decision is whether to proceed with release. It fails for `fintech_T6`, where "proceed" can mean either:

- proceed with the customer transaction / normal processing; or
- proceed with compliance filing / escalation.

### Recommended Fix

Replace q1 with a clearer business-posture variable:

> Is normal business action permissible without additional review?

Candidate labels:

- `clear_to_continue`
- `hold_for_review`

This should reduce ambiguity across both high-conflict and low-conflict tasks.

### Required Follow-Up

1. Update `pilot_tasks_v0.csv` or create `pilot_tasks_v0.2.csv` with revised q1 labels.
2. Update `prompt_templates_v0.md`, `render_phase0_prompts.py`, `validate_outputs.py`, and `analyze_cbd.py`.
3. Rerun Phase 0 with the same two tasks.
4. Proceed to Phase 1 only if parser pass remains 24/24 and `fintech_T6` no longer shows q1-driven false contextuality.

---

## 7. Gate Decision

| Gate | Result |
|---|---|
| Parser / schema gate | Pass |
| Local model viability | Pass with `--no-json-format` |
| Measurement semantics gate | Blocked on q1 revision |
| Phase 1 readiness | Not ready |

**Final Phase 0 decision:** Revise q1 and rerun Phase 0 before any Phase 1 pilot.
