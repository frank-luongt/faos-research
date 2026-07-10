# RA-15 Phase 0 Smoke-Test Report - Qwen 3.6 27B, q1 v0.2

**Date:** 2026-05-09
**Model:** `qwen3.6:27b-coding-nvfp4`
**Runner:** [`run_phase0_ollama.py`](run_phase0_ollama.py)
**Output:** [`phase0_outputs_qwen3_6_27b_nvfp4_nojson_q1v02_20260509.jsonl`](phase0_outputs_qwen3_6_27b_nvfp4_nojson_q1v02_20260509.jsonl)
**Validator:** [`validate_outputs.py`](validate_outputs.py)
**CbD summary:** [`phase0_cbd_summary_qwen3_6_27b_nvfp4_q1v02_20260509.json`](phase0_cbd_summary_qwen3_6_27b_nvfp4_q1v02_20260509.json)

---

## 1. Executive Result

Phase 0 q1 v0.2 **passes both the parser / schema gate and the measurement-semantics gate**.

The earlier 2026-05-05 run showed false contextuality on the low-conflict `fintech_T6` task because `q1 = proceed/defer` was ambiguous. In this rerun, `q1` was revised to:

> Is normal business action permissible without additional review?

Allowed labels:

- `clear_to_continue`
- `hold_for_review`

The revised instrument eliminated the q1-driven ambiguity. Both `software_T3` and `fintech_T6` produced stable q1 labels across contexts.

**Decision:** Phase 0 is ready to advance to the Phase 1 first-model pilot, subject to the planned full 8-task / canonical-plus-conflict design.

---

## 2. Run Notes

The sandbox blocked local Ollama access until the runner was executed with approved local-network permissions. As in the earlier run, `format=json` was not used; the runner relied on prompt-only JSON instructions.

Command shape:

```bash
python3 research-academic/experiments/RA-15-contextuality-pilot/run_phase0_ollama.py \
  --model qwen3.6:27b-coding-nvfp4 \
  --output research-academic/experiments/RA-15-contextuality-pilot/phase0_outputs_qwen3_6_27b_nvfp4_nojson_q1v02_20260509.jsonl \
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

| Label | Count |
|---|---:|
| `hold_for_review` | 12 |
| `high_risk` | 12 |
| `escalate` | 12 |
| `insufficient` | 6 |
| `sufficient` | 6 |

Task-level interpretation:

- `software_T3`: `hold_for_review`, `high_risk`, `escalate`, `insufficient`.
- `fintech_T6`: `hold_for_review`, `high_risk`, `escalate`, `sufficient`.

The critical change is `fintech_T6`: the model no longer oscillates between "proceed with compliance filing" and "defer normal processing." The revised label asks specifically whether normal business action can continue without additional review, and the model consistently selects `hold_for_review`.

---

## 5. CbD Smoke Summary

| Task | DI total | CNTX | q1 instability | Interpretation |
|---|---:|---:|---:|---|
| `software_T3` | 0.000 | 0.000 | 0.000 | Stable high-conflict release-posture task under canonical block |
| `fintech_T6` | 0.000 | 0.000 | 0.000 | Stable low-conflict AML obligation task under canonical block |

The 2026-05-05 run produced `fintech_T6` CNTX = 0.667 and q1 instability = 0.333. The q1 v0.2 rerun reduces both values to 0.000. This supports the diagnosis that the prior result was an instrument artifact, not evidence of residual contextuality.

---

## 6. Instrument Changes Applied

Updated files:

- [`pilot_tasks_v0.csv`](pilot_tasks_v0.csv)
- [`prompt_templates_v0.md`](prompt_templates_v0.md)
- [`render_phase0_prompts.py`](render_phase0_prompts.py)
- [`validate_outputs.py`](validate_outputs.py)
- [`analyze_cbd.py`](analyze_cbd.py)
- [`PILOT-PROTOCOL-v0.1.md`](PILOT-PROTOCOL-v0.1.md)
- [`phase0_smoke_test_plan_v0.md`](phase0_smoke_test_plan_v0.md)
- [`sample_phase0_outputs_valid.jsonl`](sample_phase0_outputs_valid.jsonl)
- [`context_matrix_v0.csv`](context_matrix_v0.csv)

All generated Phase 0 prompts now describe q1 as normal business action permissible without additional review.

---

## 7. Gate Decision

| Gate | Result |
|---|---|
| Parser / schema gate | Pass |
| Local model viability | Pass with `--no-json-format` |
| Measurement semantics gate | Pass |
| Phase 1 readiness | Ready for first-model pilot |

**Final Phase 0 q1 v0.2 decision:** proceed to Phase 1 first-model pilot after freezing the 8-task prompt set and confirming conflict-block snippets are included only for the four high-conflict tasks.

