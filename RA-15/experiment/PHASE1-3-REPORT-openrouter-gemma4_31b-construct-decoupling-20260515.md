# RA-15 Phase 1.3 Report - OpenRouter Gemma 4 Construct Decoupling

**Date:** 2026-05-15  
**Model:** `google/gemma-4-31b-it` via OpenRouter  
**Runner:** `run_phase13_openrouter.py`  
**Status:** Complete; 384 / 384 repaired rows valid  
**Formalism audit:** Corrected on 2026-05-15 for canonical CbD claims

> 2026-05-15 correction: The nonzero values originally labeled `CNTX` are now
> treated as `legacy_probability_drift` residuals. After expectation-scale
> direct-influence correction, `cntx_canonical = 0.000` for all OpenRouter
> Gemma 4 Phase 1.3 groups. See
> `../../papers/RA-15-Contextuality-Auditor/FORMALISM-AUDIT-20260515.md`.

---

## 1. Purpose

This run is an explicitly labeled second-model replication check for the Phase 1.3 q1/q4 construct-decoupling gate. After the formalism audit, it should be read as a robustness check for direct influence, a pattern consistent with construct coupling, and stable controls, not as a residual-contextuality replication.

It tests whether the primary-local-model findings from `qwen3.6:27b-coding-nvfp4` persist under OpenRouter-hosted Gemma 4:

- `healthcare_T6` should remain zero or near-zero after q1/q4 construct decoupling.
- `insurance_T9` should be checked for either canonical residual contextuality or direct-influence signal.
- `insurance_T6` and `software_T3` should remain stable or near-stable controls.

This is not a broad model-generalization claim. It is a targeted replication check on the frozen Phase 1.3 matrix.

---

## 2. Execution

Prompt freeze:

- `phase13_prompts_construct_decoupling_20260512.jsonl`
- 384 prompts
- 4 task/block groups x 2 conditions x 4 contexts x 12 repetitions

Output artifacts:

- Smoke output: `phase13_outputs_openrouter_gemma4_31b_construct_decoupling_smoke_20260515.jsonl`
- Raw runner output: `phase13_outputs_openrouter_gemma4_31b_construct_decoupling_20260515.jsonl`
- Repaired analysis output: `phase13_outputs_openrouter_gemma4_31b_construct_decoupling_repaired_20260515.jsonl`
- CbD summary: `phase13_cbd_summary_openrouter_gemma4_31b_construct_decoupling_20260515.json`

Run command:

```bash
python3 run_phase13_openrouter.py \
  --model google/gemma-4-31b-it \
  --output phase13_outputs_openrouter_gemma4_31b_construct_decoupling_20260515.jsonl \
  --restart \
  --timeout 240 \
  --max-tokens 500
```

Repair command:

```bash
python3 run_phase13_openrouter.py \
  --model google/gemma-4-31b-it \
  --output phase13_outputs_openrouter_gemma4_31b_construct_decoupling_20260515.jsonl \
  --timeout 240 \
  --max-tokens 500
```

Run notes:

- Smoke test passed: 1 / 1 valid.
- Main pass wrote 384 rows.
- One timeout occurred at `healthcare_T6 canonical_role_fixed C3 rep 8`.
- Resumable repair appended a successful replacement row.
- The repaired analysis file drops the timeout row and preserves one successful row for each `(condition, task_id, block, context_id, rep)` coordinate.
- Generation settings: temperature `0.2`, maximum `500` generated tokens, prompt-only JSON instruction, and timeout `240` seconds.
- The stored alias is `google/gemma-4-31b-it`; served provider/backend, immutable revision, seed, cache state, and randomized call-order metadata were not retained.
- The 12 repetitions per context are repeated stochastic draws from one routed endpoint, not independent task or subject units.

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
| `healthcare_T6` | `canonical_role_fixed` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | Construct-coupling signal remains collapsed |
| `healthcare_T6` | `canonical_order_neutral` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | Construct-coupling signal remains collapsed |
| `insurance_T6` | `canonical_role_fixed` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | Stable negative control |
| `insurance_T6` | `canonical_order_neutral` | 0.000 | 0.167 | 0.167 | 0.333 | 0.083 | Small-to-moderate direct influence in a control |
| `insurance_T9` | `conflict_role_fixed` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | No canonical or direct-influence signal |
| `insurance_T9` | `conflict_order_neutral` | 0.000 | 0.917 | 0.917 | 1.833 | 0.458 | Large direct-influence signal |
| `software_T3` | `conflict_role_fixed` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | Stable negative control |
| `software_T3` | `conflict_order_neutral` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | Stable negative control |

---

## 4. Comparison to First Model

| Task | Block | Qwen canonical CNTX | Gemma 4 canonical CNTX | Qwen legacy residual | Gemma 4 legacy residual | Replication read |
|---|---:|---:|---:|---:|---:|---|
| `healthcare_T6` | `canonical_role_fixed` | 0.000 | 0.000 | 0.000 | 0.000 | Replicates collapse |
| `healthcare_T6` | `canonical_order_neutral` | 0.000 | 0.000 | 0.083 | 0.000 | Replicates canonical zero |
| `insurance_T6` | `canonical_role_fixed` | 0.000 | 0.000 | 0.000 | 0.000 | Replicates stability |
| `insurance_T6` | `canonical_order_neutral` | 0.000 | 0.000 | 0.083 | 0.167 | Direct influence in both |
| `insurance_T9` | `conflict_role_fixed` | 0.000 | 0.000 | 0.333 | 0.000 | Canonical zero in both |
| `insurance_T9` | `conflict_order_neutral` | 0.000 | 0.000 | 0.333 | 0.917 | Direct influence in both |
| `software_T3` | `conflict_role_fixed` | 0.000 | 0.000 | 0.000 | 0.000 | Replicates stability |
| `software_T3` | `conflict_order_neutral` | 0.000 | 0.000 | 0.000 | 0.000 | Replicates stability |

---

## 5. Gate Decision

The OpenRouter Gemma 4 run is a **direct-influence robustness check**, not a canonical contextuality replication:

1. The `healthcare_T6` coupling-consistent pattern remains absent under both controls.
2. `software_T3` stays stable under both controls.
3. `insurance_T9` shows a large `order_neutral` direct-influence signal (`legacy residual = 0.917`, `DI_expectation = 1.833`).
4. `insurance_T9` has canonical `CNTX = 0.000` in both Gemma 4 blocks.
5. `insurance_T6` shows bounded `order_neutral` direct influence (`legacy residual = 0.167`).

Recommended paper stance:

> Across two models, RA-15 distinguishes the healthcare pattern consistent with construct coupling from the stable software control. The insurance conflict signal appears as direct influence, not canonical residual contextuality; therefore the result should be reported as a formalism-corrected audit-method result, not as a contextuality-positive replication.

Disallowed upgraded claim:

> `insurance_T9` is robustly contextual across models and all role/order controls.

---

## 6. Next Actions

1. Update the paper draft to v0.5 formalism-corrected wording.
2. Keep the main claim bounded to an audit method / negative-results paper.
3. Add a redesigned experiment only if RA-15 needs a canonical residual-contextuality-positive result.
4. Treat `insurance_T6` and `insurance_T9` order-neutral drift as direct-influence cautions.
