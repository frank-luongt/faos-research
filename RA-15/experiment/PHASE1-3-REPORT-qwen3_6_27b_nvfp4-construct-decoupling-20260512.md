# RA-15 Phase 1.3 Report - q1/q4 Construct Decoupling

**Date:** 2026-05-12
**Model:** `qwen3.6:27b-coding-nvfp4` via local Ollama
**Runner:** `run_phase13_ollama.py --no-json-format`
**Status:** Complete; 384 / 384 repaired rows valid  
**Formalism audit:** Superseded on 2026-05-15 for canonical CbD claims

> 2026-05-15 correction: The original `CNTX` values in this report are now
> treated as `legacy_probability_drift` residuals, not canonical cyclic-binary
> CbD degree. After expectation-scale direct-influence correction,
> `cntx_canonical = 0.000` for all Phase 1.3 groups. See
> `../../papers/RA-15-Contextuality-Auditor/FORMALISM-AUDIT-20260515.md`.

---

## 1. Purpose

Phase 1.3 tested whether the Phase 1.2 `healthcare_T6` signal was residual contextuality or a measurement-design artifact caused by coupling q1 operational permission with q4 evidence readiness. The later formalism audit showed that all Phase 1.3 nonzero legacy residuals are direct-influence effects rather than canonical residual contextuality.

Phase 1.3 changed:

- q1 to operational permission: `action_permitted_in_principle` / `action_not_permitted_in_principle`
- q4 to procedural evidence readiness: `evidence_packet_ready` / `evidence_packet_not_ready`

The historical pre-audit criterion was:

- `healthcare_T6` should collapse to near-zero contextuality (`CNTX <= 0.100`)
- `insurance_T9` conflict should remain informative as a challenge case
- `insurance_T6` and `software_T3` should remain stable controls

---

## 2. Execution

Prompt freeze:

- `phase13_prompts_construct_decoupling_20260512.jsonl`
- 384 prompts
- 4 task/block groups x 2 conditions x 4 contexts x 12 repetitions

Output artifacts:

- Raw runner output: `phase13_outputs_qwen3_6_27b_nvfp4_construct_decoupling_20260512.jsonl`
- Repaired analysis output: `phase13_outputs_qwen3_6_27b_nvfp4_construct_decoupling_repaired_20260512.jsonl`
- CbD summary: `phase13_cbd_summary_qwen3_6_27b_nvfp4_construct_decoupling_20260512.json`

Run notes:

- Main pass wrote 384 rows.
- One timeout occurred at `insurance_T9 conflict_order_neutral C2X rep 8`.
- Resumable repair appended a successful replacement row.
- The repaired analysis file drops the timeout row and preserves the latest successful row for each `(condition, task_id, block, context_id, rep)` coordinate.
- Generation settings: temperature `0.2`, no JSON response-format constraint, timeout `420` seconds, and no explicit generation-token cap.
- Local artifact: Ollama `qwen3.6:27b-coding-nvfp4`, artifact ID `42a2d9de99b0`, architecture `qwen3_5`, 27.4B parameters, NVFP4 quantization.
- Seed, cache state, and randomized call-order metadata were not retained.
- The 12 repetitions per context are repeated stochastic draws from one fixed endpoint, not independent task or subject units.

Validation:

```json
{
  "total": 384,
  "valid": 384,
  "invalid": 0
}
```

---

## 3. Results

| Task | Block | Canonical CNTX | Legacy residual | DI_probability | DI_expectation | q1 instability | Interpretation |
|---|---:|---:|---:|---:|---:|---:|---|
| `healthcare_T6` | `canonical_role_fixed` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | Healthcare construct-coupling signal collapses |
| `healthcare_T6` | `canonical_order_neutral` | 0.000 | 0.083 | 0.083 | 0.167 | 0.000 | Direct influence only after decoupling |
| `insurance_T6` | `canonical_role_fixed` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | Stable negative control |
| `insurance_T6` | `canonical_order_neutral` | 0.000 | 0.083 | 0.083 | 0.167 | 0.042 | Direct influence only |
| `insurance_T9` | `conflict_role_fixed` | 0.000 | 0.333 | 0.333 | 0.667 | 0.417 | Direct influence only |
| `insurance_T9` | `conflict_order_neutral` | 0.000 | 0.333 | 0.333 | 0.667 | 0.417 | Direct influence only |
| `software_T3` | `conflict_role_fixed` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | Stable negative control |
| `software_T3` | `conflict_order_neutral` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | Stable negative control |

---

## 4. Gate Decision

After the 2026-05-15 formalism audit, Phase 1.3 satisfies a narrower RA-15 method / negative-results gate:

1. `healthcare_T6` collapses after q1/q4 construct decoupling.
2. `insurance_T9` conflict does not survive as canonical residual contextuality; its nonzero legacy residual is direct influence.
3. Negative controls remain stable or direct-influence-only.

The paper should proceed only as a bounded formalism-corrected audit-method / negative-results paper, not a broad conflict-band prediction paper.

Allowed post-Phase 1.3 claim:

> In this primary-local-model pilot, CbD-style analysis distinguished stable controls, a pattern consistent with q1/q4 construct coupling, and direct-influence-only insurance conflict sensitivity after role/order and construct-decoupling controls.

Disallowed claim:

> High-conflict enterprise tasks generally produce contextuality.

---

## 5. Interpretation Notes

The challenge-case result is direct influence. Both `insurance_T9` Phase 1.3 conditions have:

- `DI_total = 0.333`
- q1 instability `= 0.417`
- `H_mean = 0.224`

Therefore the result should be framed as a conflict-sensitive direct-influence diagnostic signal in a bounded primary-local-model pilot, not as proof that insurance conflict tasks are canonically contextual.

The healthcare result is cleaner: q1 instability falls to zero in both Phase 1.3 controls. This is consistent with the hypothesis that the prior signal arose from coupling operational permission and procedural evidence readiness, but it does not establish that latent cause because the intervention changed several prompt elements and no independent construct review was performed.

---

## 6. Next Actions

1. Update the RA-15 paper scaffold with formalism-corrected Phase 1.3 results.
2. Keep all claims bounded to direct influence, evidence consistent with construct coupling, and canonical CbD null results.
3. Decide whether to submit as a negative-results method paper or redesign the experiment.
