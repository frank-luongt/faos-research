# RA-15 Phase 0 v0.2 Smoke-Test Report - Qwen 3.6 27B

**Date:** 2026-05-09
**Model:** `qwen3.6:27b-coding-nvfp4`
**Runner:** [`run_phase0_ollama.py`](run_phase0_ollama.py)
**Output:** [`phase0_outputs_qwen3_6_27b_nvfp4_v02_20260509.jsonl`](phase0_outputs_qwen3_6_27b_nvfp4_v02_20260509.jsonl)
**Validator:** [`validate_outputs.py`](validate_outputs.py)
**CbD summary:** [`phase0_cbd_summary_qwen3_6_27b_nvfp4_v02_20260509.json`](phase0_cbd_summary_qwen3_6_27b_nvfp4_v02_20260509.json)

---

## 1. Executive Result

Phase 0 v0.2 **passes both the parser/schema gate and the measurement-semantics gate**.

The v0.1 instrument produced valid JSON but exposed q1 ambiguity on `fintech_T6`: `proceed` could mean either normal transaction processing or compliance action. The v0.2 instrument replaces q1 with the business-continuity labels `clear_to_continue` / `hold_for_review`.

The rerun produced 24/24 valid records and removed the low-conflict false-contextuality pattern. Both smoke-test tasks have `CNTX = 0.0`, `DI_total = 0.0`, and `q1_instability = 0.0`.

**Decision:** Phase 0 is cleared. RA-15 may proceed to the Phase 1 first-model pilot, while preserving the boundary that Phase 0 is an instrument test, not evidence for residual contextuality.

---

## 2. Run Notes

The first sandboxed attempt could not reach local Ollama (`Operation not permitted`). The successful run used the same command with local-network permission and kept `--no-json-format`, matching the v0.1 finding that Ollama `format=json` was not viable for this local model.

Command shape:

```bash
python3 research-academic/experiments/RA-15-contextuality-pilot/run_phase0_ollama.py \
  --model qwen3.6:27b-coding-nvfp4 \
  --output research-academic/experiments/RA-15-contextuality-pilot/phase0_outputs_qwen3_6_27b_nvfp4_v02_20260509.jsonl \
  --temperature 0.2 \
  --timeout 240 \
  --no-json-format
```

The run completed all 24 calls with no runner-level errors. Local generation was slow, roughly one minute per call, but stable.

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

| Task | Field | Label | Count |
|---|---|---:|---:|
| `software_T3` | q1 | `hold_for_review` | 6 |
| `software_T3` | q2 | `high_risk` | 6 |
| `software_T3` | q3 | `escalate` | 6 |
| `software_T3` | q4 | `insufficient` | 6 |
| `fintech_T6` | q1 | `hold_for_review` | 6 |
| `fintech_T6` | q2 | `high_risk` | 6 |
| `fintech_T6` | q3 | `escalate` | 6 |
| `fintech_T6` | q4 | `sufficient` | 6 |

The revised q1 wording resolves the previous ambiguity. For `fintech_T6`, the model consistently treats the transaction as not clear for normal business continuation and routes it to review, while still distinguishing sufficient evidence for compliance action under q4.

---

## 5. CbD Smoke Summary

| Task | DI total | CNTX | q1 instability | Interpretation |
|---|---:|---:|---:|---|
| `software_T3` | 0.000 | 0.000 | 0.000 | Stable high-conflict release-posture task under canonical block |
| `fintech_T6` | 0.000 | 0.000 | 0.000 | Low-conflict regulatory task no longer shows q1-driven false contextuality |

The v0.2 result should not be treated as evidence that RA-15's main hypothesis is supported. It shows that the binary measurement instrument is now usable for a larger first-model pilot.

---

## 6. Gate Decision

| Gate | Result |
|---|---|
| Parser / schema gate | Pass |
| Local model viability | Pass with `--no-json-format` |
| Measurement semantics gate | Pass |
| Phase 1 readiness | Ready for first-model pilot design/run |

**Final Phase 0 v0.2 decision:** Proceed to Phase 1 first-model pilot with the revised q1 labels.
