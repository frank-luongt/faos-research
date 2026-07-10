# RA-15 Phase 1.2 Report - Role/Order Disentanglement

**Date:** 2026-05-10  
**Owner:** Builder-Researcher  
**Model:** `qwen3.6:27b-coding-nvfp4`  
**Prompt instrument:** q1 v0.2 plus q4 action-readiness labels  
**Status:** Phase 1.2 role/order disentanglement complete

## 1. Run Summary

Phase 1.2 reran the smallest decisive role/order-disentanglement set:

- Records rendered: 480.
- Groups: 5 task/source-block groups x 2 conditions x 4 contexts x 12 reps.
- Conditions: `role_fixed`, `order_neutral`.
- Valid JSON outputs: 480 / 480.
- Invalid / timeout after repair: 0 / 480.

The first pass produced one timeout at `healthcare_T6`, `canonical_role_fixed`, `C2`, rep 10. A resumable retry produced the missing valid response, and the stale timeout row was removed. The current output artifact is a clean 480-row dataset.

Prompt-freeze artifact:

- `phase12_prompt_freeze_role_order_20260510.json`

Output artifacts:

- `phase12_prompts_role_order_qwen3_6_27b_nvfp4_20260510.jsonl`
- `phase12_outputs_qwen3_6_27b_nvfp4_nojson_role_order_20260510.jsonl`
- `phase12_cbd_summary_qwen3_6_27b_nvfp4_role_order_20260510.json`

## 2. Conditions

`role_fixed`:

- Keeps the cyclic CbD measured pairs.
- Holds the role frame constant as `neutral enterprise decision reviewer`.
- Removes business-action-first, risk-first, escalation-first, and evidence-first priority language.

`order_neutral`:

- Keeps the role frame variation from the original context matrix.
- Removes measured-content ordering priority and framing language.
- Instructs the model to treat measured q fields as unordered independent labels.

Both conditions retain q4 action-readiness labels:

- `evidence_ready_for_action`
- `evidence_not_ready_for_action`

## 3. Metrics

| Task | Block | Phase 1 CNTX | Phase 1.1 CNTX | Phase 1.2 condition | Phase 1.2 CNTX | Phase 1.2 DI | H_mean | q1 instability |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `healthcare_T6` | canonical | 0.417 | 1.000 | `canonical_role_fixed` | 1.000 | 1.000 | 0.000 | 0.500 |
| `healthcare_T6` | canonical | 0.417 | 1.000 | `canonical_order_neutral` | 1.000 | 1.000 | 0.000 | 0.500 |
| `insurance_T6` | canonical | 0.000 | n/a | `canonical_role_fixed` | 0.000 | 0.000 | 0.000 | 0.000 |
| `insurance_T6` | canonical | 0.000 | n/a | `canonical_order_neutral` | 0.000 | 0.000 | 0.000 | 0.000 |
| `insurance_T9` | canonical | 0.500 | 0.000 | `canonical_role_fixed` | 0.083 | 0.083 | 0.052 | 0.000 |
| `insurance_T9` | canonical | 0.500 | 0.000 | `canonical_order_neutral` | 0.167 | 0.167 | 0.081 | 0.000 |
| `insurance_T9` | conflict | 0.833 | 0.500 | `conflict_role_fixed` | 0.417 | 0.417 | 0.122 | 0.000 |
| `insurance_T9` | conflict | 0.833 | 0.500 | `conflict_order_neutral` | 0.583 | 0.583 | 0.122 | 0.000 |
| `software_T3` | conflict | 0.000 | 0.000 | `conflict_role_fixed` | 0.000 | 0.000 | 0.000 | 0.000 |
| `software_T3` | conflict | 0.000 | 0.000 | `conflict_order_neutral` | 0.000 | 0.000 | 0.000 | 0.000 |

## 4. Findings

1. `insurance_T9` conflict survives role/order disentanglement. `conflict_role_fixed` remains nonzero at `CNTX=0.417`; `conflict_order_neutral` remains nonzero at `CNTX=0.583`. This is the strongest evidence so far that at least one high-conflict enterprise decision carries residual contextuality beyond the original role/order framing.

2. `insurance_T9` canonical stays near zero after redesign. Canonical Phase 1.2 values are small (`0.083`, `0.167`) compared with Phase 1 canonical `0.500`, supporting the Phase 1.1 conclusion that the original canonical insurance signal was largely measurement-induced.

3. Negative controls remain stable. `insurance_T6` canonical and `software_T3` conflict both remain at `CNTX=0.000` under both Phase 1.2 conditions. This supports the redesigned instrument's ability to preserve stable cases.

4. `healthcare_T6` remains a deterministic q1/q4 construct-coupling artifact. Holding role fixed and removing ordering priority did not reduce the healthcare signal: both conditions are `CNTX=1.000`, `DI_total=1.000`, `H_mean=0.000`, and `q1_instability=0.500`. The issue is not role frame or prompt order. It is that q1 "normal business action permissible" and q4 "evidence ready for action" become semantically entangled for HIPAA access: C1 treats the legal right as routine, while C4 treats missing process evidence as a reason to hold.

5. The clean RA-15 claim is now narrower and stronger: contextuality auditing can distinguish stable controls, measurement-induced canonical effects, construct-coupling artifacts, and surviving conflict effects.

## 5. Gate Decision

**Decision: promote to a scoped RA-15 paper scaffold, but only with a bounded claim and one planned confirmatory extension.**

Phase 1.2 satisfies the core survival condition for `insurance_T9` conflict: nonzero contextuality remains after role/order disentanglement. It also preserves stable negative controls. However, `healthcare_T6` proves that the current instrument still detects construct coupling, not only operational conflict. The paper should not claim that high-conflict labels generally predict contextuality.

Allowed paper claim:

- CbD-style contextuality can audit enterprise-agent decisions by separating stable cases, measurement artifacts, construct-coupling artifacts, and residual conflict-sensitive effects.

Disallowed paper claim:

- High-conflict enterprise tasks generally produce contextuality.

Recommended next action:

1. Scaffold the RA-15 paper around the bounded audit-method claim.
2. Add a planned Phase 1.3 confirmatory extension focused on q1/q4 construct decoupling for healthcare and one additional regulated-access task.
3. Treat `insurance_T9` conflict as the primary positive-control result.
4. Treat `insurance_T6` and `software_T3` as stable negative controls.
5. Treat `healthcare_T6` as a documented construct-coupling failure mode, not a positive result.

## 6. Interpretation

RA-15 has crossed from "interesting pilot" to "scaffoldable research direction," but the paper must be honest about what survived. The surviving contribution is not a universal conflict-band predictor. It is an audit methodology for detecting when an agent decision cannot be explained by a single context-independent joint distribution, followed by diagnosis of whether the signal is conflict, measurement design, or construct coupling.
