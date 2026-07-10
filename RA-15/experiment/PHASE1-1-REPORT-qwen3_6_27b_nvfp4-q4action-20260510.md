# RA-15 Phase 1.1 Report - q4 Action-Readiness Robustness

**Date:** 2026-05-10  
**Owner:** Builder-Researcher  
**Model:** `qwen3.6:27b-coding-nvfp4`  
**Prompt instrument:** q1 v0.2 plus q4 action-readiness labels  
**Status:** Phase 1.1 robustness pass complete

## 1. Run Summary

Phase 1.1 reran the targeted q4-robustness subset from Phase 1:

- Records rendered: 336.
- Groups: 7 task/block groups x 4 contexts x 12 reps.
- Valid JSON outputs: 336 / 336.
- Invalid / timeout after repair: 0 / 336.

The first pass produced one timeout at `insurance_T9`, conflict, `C3X`, rep 4. A resumable retry produced the missing valid response, and the stale timeout row was removed. The current output artifact is a clean 336-row dataset.

Prompt-freeze artifact:

- `phase11_prompt_freeze_q4action_20260510.json`

Output artifacts:

- `phase11_prompts_q4action_qwen3_6_27b_nvfp4_20260510.jsonl`
- `phase11_outputs_qwen3_6_27b_nvfp4_nojson_q4action_20260510.jsonl`
- `phase11_cbd_summary_qwen3_6_27b_nvfp4_q4action_20260510.json`

## 2. Instrument Change

Phase 1 used q4 labels:

- `sufficient`
- `insufficient`

Phase 1.1 changed q4 to action-readiness:

- `evidence_ready_for_action`
- `evidence_not_ready_for_action`

The q4 prompt instruction also narrowed the construct: judge whether the current evidence supports the requested action now, not broad evidence sufficiency.

## 3. Metrics

| Task | Block | Phase 1 CNTX | Phase 1.1 CNTX | Phase 1 DI | Phase 1.1 DI | Phase 1 H_mean | Phase 1.1 H_mean | Phase 1.1 q1 instability |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `banking_vn_T6` | canonical | 0.000 | 0.083 | 0.000 | 0.083 | 0.103 | 0.052 | 0.000 |
| `fintech_T6` | canonical | 0.167 | 0.167 | 0.167 | 0.167 | 0.081 | 0.224 | 0.000 |
| `healthcare_T6` | canonical | 0.417 | 1.000 | 1.083 | 1.000 | 0.205 | 0.000 | 0.500 |
| `insurance_T9` | canonical | 0.500 | 0.000 | 0.500 | 0.000 | 0.125 | 0.000 | 0.000 |
| `insurance_T9` | conflict | 0.833 | 0.500 | 0.833 | 0.500 | 0.081 | 0.125 | 0.000 |
| `insurance_vn_T8` | conflict | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `software_T3` | conflict | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## 4. Findings

1. q4 action-readiness removed the `insurance_T9` canonical signal. `insurance_T9` canonical dropped from `CNTX=0.500` to `CNTX=0.000`, which means the original canonical insurance signal was likely measurement-induced by broad q4 evidence-sufficiency wording.

2. The `insurance_T9` conflict signal survived, but attenuated. Conflict `CNTX` dropped from `0.833` to `0.500`, with `DI_total=0.500` and `H_mean=0.125`. This remains the best positive-control evidence for orchestration-relevant contextuality, but the effect size is smaller after q4 tightening.

3. `healthcare_T6` did not improve; it intensified. `CNTX` increased from `0.417` to `1.000`, with `q1_instability=0.500` and zero entropy. This is a deterministic context-frame flip: business-action C1 permits routine continuation, while evidence-first C4 forces hold-for-review. The issue is therefore not only q4 labels; it is the coupling between role/frame/order and q1.

4. Low-control tasks remain mixed. `fintech_T6` stayed at `CNTX=0.167`, while `banking_vn_T6` rose slightly from `0.000` to `0.083`. Both retain q1 stability, so the signal is not driven by q1 label ambiguity.

5. Stable negative controls stayed stable. `insurance_vn_T8` conflict and `software_T3` conflict both remained `CNTX=0.000`, `DI_total=0.000`, `H_mean=0.000`, and `q1_instability=0.000`.

## 5. Gate Decision

**Decision: continue RA-15, but do not promote to full paper scaffold yet.**

Phase 1.1 strengthens the methodological story but weakens the immediate paper claim. The simple interpretation "high-conflict tasks produce contextuality" is not supported. The better claim is narrower: CbD can diagnose when enterprise-agent decisions are sensitive to context-frame coupling, and this diagnostic can separate stable negative controls, measurement artifacts, and surviving conflict effects.

The next gate should be Phase 1.2 measurement redesign, not paper writing.

Recommended Phase 1.2 actions:

1. Decouple role frame from measured-content context. Keep the cyclic CbD pairing but hold role constant across C1-C4 in one condition.
2. Add a second condition where role varies but measured-content order is held constant, to estimate role-vs-order contribution.
3. Replace q4 with an action-readiness construct, but avoid pairing evidence-first framing directly with q1 until the role/order confound is measured.
4. Rerun the smallest decisive set: `healthcare_T6`, `insurance_T9` canonical/conflict, `software_T3` conflict, and one stable low-control task.
5. Promote only if `insurance_T9` conflict remains nonzero after role/order disentanglement while healthcare drops or can be explained as controlled direct influence.

## 6. Interpretation

RA-15 remains promising as an audit method, not yet as a conflict-band prediction paper. The Phase 1.1 result says the instrument is sensitive enough to detect both real conflict effects and its own measurement coupling. That is useful, but the next step must isolate the source of contextuality before making a publishable claim.
