# RA-15 Phase 1 Report - First-Model Cyclic CbD Pilot

**Date:** 2026-05-09  
**Owner:** Builder-Researcher  
**Model:** `qwen3.6:27b-coding-nvfp4`  
**Prompt instrument:** q1 v0.2 (`clear_to_continue` / `hold_for_review`)  
**Status:** Phase 1 first-model run complete; timeout repaired on 2026-05-10

## 1. Run Summary

Phase 1 rendered the frozen 8-task prompt set with 12 repetitions per cyclic context:

- Canonical block: 8 tasks x 4 contexts x 12 reps = 384 prompts.
- Conflict block: 4 high-conflict tasks x 4 contexts x 12 reps = 192 prompts.
- Total attempted: 576 prompts.
- Valid JSON outputs: 576 / 576.
- Invalid / timeout: 0 / 576.

The original run had one timeout at `insurance_vn_T8`, conflict, `C3X`, rep 5. A resumable retry on 2026-05-10 produced the missing valid JSON response, and the stale timeout row was removed from the analysis file. The current output artifact is therefore a clean 576-row dataset.

## 2. Prompt Freeze Verification

The Phase 1 renderer produced the expected frozen prompt set:

- Records: 576.
- Conflict snippets routed only to high-conflict tasks: `fintech_T9`, `insurance_T9`, `insurance_vn_T8`, `software_T3`.
- Canonical prompts present for all 8 tasks.
- q1 labels restricted to `clear_to_continue` and `hold_for_review`.

Prompt-freeze artifact:

- `phase1_prompt_freeze_q1v02_20260509.json`

## 3. Metrics

| Task | Block | DI_total | CNTX | H_mean | q1 instability |
|---|---:|---:|---:|---:|---:|
| `banking_vn_T6` | canonical | 0.000 | 0.000 | 0.103 | 0.000 |
| `fintech_T6` | canonical | 0.167 | 0.167 | 0.081 | 0.000 |
| `fintech_T9` | canonical | 1.500 | 0.000 | 0.228 | 0.458 |
| `fintech_T9` | conflict | 0.167 | 0.167 | 0.081 | 0.000 |
| `healthcare_T6` | canonical | 1.083 | 0.417 | 0.205 | 0.458 |
| `insurance_T6` | canonical | 0.000 | 0.000 | 0.000 | 0.000 |
| `insurance_T9` | canonical | 0.500 | 0.500 | 0.125 | 0.000 |
| `insurance_T9` | conflict | 0.833 | 0.833 | 0.081 | 0.000 |
| `insurance_vn_T8` | canonical | 0.000 | 0.000 | 0.000 | 0.000 |
| `insurance_vn_T8` | conflict | 0.000 | 0.000 | 0.000 | 0.000 |
| `software_T3` | canonical | 0.000 | 0.000 | 0.000 | 0.000 |
| `software_T3` | conflict | 0.000 | 0.000 | 0.000 | 0.000 |

Skipped groups:

- None. All 12 task/block groups are balanced at 48 records each.

Metric artifact:

- `phase1_cbd_summary_qwen3_6_27b_nvfp4_q1v02_20260509.json`

## 4. Findings

1. The revised q1 instrument held up under Phase 1. `software_T3` canonical and conflict both produced `DI_total=0`, `CNTX=0`, `H_mean=0`, confirming that the Phase 0 q1 ambiguity was not reintroduced.

2. Residual contextuality exists in the pilot. Nonzero `CNTX` appears in `fintech_T6`, `fintech_T9` conflict, `healthcare_T6`, `insurance_T9` canonical, and `insurance_T9` conflict.

3. The signal is not explained by entropy alone. `insurance_T9` conflict has `CNTX=0.833` with low `H_mean=0.081`, while `fintech_T9` canonical has higher entropy (`H_mean=0.228`) but `CNTX=0`.

4. The signal is not cleanly predicted by the original high-conflict label. Two high-conflict tasks are perfectly stable across their conflict blocks (`software_T3`, `insurance_vn_T8`), while a low-conflict healthcare task shows high direct influence and nonzero contextuality (`DI_total=1.083`, `CNTX=0.417`).

5. Evidence sufficiency (`q4`) is the dominant measurement hazard. Several low-control tasks changed posture when q4 was paired with q1 in C4, especially `healthcare_T6`, where C1 treated the access request as routine while C4 held the request for review because missing operational evidence became salient.

## 5. Gate Decision

**Decision: continue RA-15, but do not promote directly to full paper scaffold yet.**

The pilot passes the basic empirical-interest gate because residual contextuality appears after direct-influence correction and is not reducible to output entropy. However, the Phase 1 result also shows that part of the signal is instrument-induced by the evidence-sufficiency variable. The next step should be a short Phase 1.1 robustness pass before paper promotion.

Recommended Phase 1.1 actions:

1. Split q4 into a less ambiguous construct, e.g. `evidence_ready_for_action` rather than broad `sufficient`.
2. Re-run only the affected low-control cases (`fintech_T6`, `healthcare_T6`, `banking_vn_T6`) plus `insurance_T9` as a positive-control high-CNTX case.
3. Compare current CNTX against revised-q4 CNTX to estimate measurement-artifact share.
4. Promote to full RA-15 scaffold only if residual contextuality remains after q4 tightening and continues to add signal beyond `DI_total` and `H_mean`.
5. Keep `insurance_vn_T8` and `software_T3` as stable high-conflict negative controls in the robustness report.

## 6. Interpretation

RA-15 remains alive. The right claim is narrower than the original conflict-band story: contextuality is a useful audit signal for context-sensitive enterprise decisions, but it currently detects both real policy conflict and measurement-design coupling. The next robustness pass should determine whether the surviving contextuality is orchestration-relevant or primarily an artifact of asking evidence sufficiency next to decision posture.
