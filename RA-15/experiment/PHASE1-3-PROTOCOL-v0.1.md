# RA-15 Phase 1.3 Protocol - q1/q4 Construct Decoupling

**Date:** 2026-05-12  
**Owner:** Builder-Researcher  
**Status:** Complete; exploratory protocol and canonical-formalism correction recorded
**Prerequisite:** Phase 1.2 role/order disentanglement complete  
**Primary report:** `PHASE1-2-REPORT-qwen3_6_27b_nvfp4-role-order-20260510.md`

---

## 1. Purpose

Phase 1.2 produced a nonzero legacy probability-scale residual for `healthcare_T6` under both controls:

- `CNTX = 1.000`
- `DI_total = 1.000`
- `q1_instability = 0.500`
- `H_mean = 0.000`

The pattern was deterministic in those draws. One hypothesis was q1/q4 construct coupling:

- q1 asks whether normal business action is permissible without additional review.
- q4 asks whether evidence is ready for action.

For HIPAA access, those constructs can collapse into one another. A request may be legally routine in one context while procedurally blocked in another because the available evidence packet is incomplete. Phase 1.3 tests whether the signal disappears when q1 and q4 are deliberately decoupled.

---

## 2. Research Question

> Does the `healthcare_T6` contextuality signal collapse when operational permission and procedural evidence readiness are measured as distinct constructs?

Secondary question:

> Does `insurance_T9` conflict remain nonzero under the same decoupled instrument?

---

## 3. Design

### 3.1 Retest Groups

Minimum decisive set:

| Task | Block | Role in Phase 1.3 |
|---|---|---|
| `healthcare_T6` | canonical | construct-coupling retest |
| `insurance_T9` | conflict | direct-influence challenge case |
| `insurance_T6` | canonical | stable negative control |
| `software_T3` | conflict | stable negative control |

Optional extension:

| Candidate | Reason |
|---|---|
| one additional regulated-access task | Tests whether q1/q4 coupling is healthcare-specific or access-control-general |

**Decision as of 2026-05-12:** defer the optional fifth task. The frozen `pilot_tasks_v0.csv` list does not contain a clean second regulated-access task; the closest low-conflict tasks are AML/CFT, suitability, and compliance-obligation checks rather than access-rights decisions. Phase 1.3 should therefore run the minimum 384-call decisive set first.

### 3.2 Conditions

Use the two Phase 1.2 control conditions:

1. `role_fixed`
2. `order_neutral`

Do not add new role/order variants in Phase 1.3. The point is construct decoupling, not another prompt-frame search.

### 3.3 Repetitions

Use the Phase 1.2 repetition count:

```
4 task/block groups x 2 conditions x 4 contexts x 12 reps = 384 calls
```

If the optional regulated-access task is added:

```
5 task/block groups x 2 conditions x 4 contexts x 12 reps = 480 calls
```

---

## 4. Revised Measurement Constructs

### 4.1 q1 - Operational Permission

New generic question:

> Is the underlying business action permitted in principle under the applicable policy, assuming normal procedural evidence can still be checked separately?

Allowed labels:

- `action_permitted_in_principle`
- `action_not_permitted_in_principle`

Meaning:

- q1 should answer the policy/legal/operational permissibility of the action itself.
- q1 should not decide whether the current evidence packet is complete.
- q1 should not use missing documentation alone as a reason to mark the action impermissible unless the policy makes documentation a condition of permissibility.

### 4.2 q4 - Procedural Evidence Readiness

New generic question:

> Is the currently available evidence packet sufficient to finalize the action without collecting additional documentation, approval, or audit evidence?

Allowed labels:

- `evidence_packet_ready`
- `evidence_packet_not_ready`

Meaning:

- q4 should answer procedural readiness.
- q4 should not decide whether the underlying action is substantively permissible.
- q4 may be negative even when q1 is positive.

### 4.3 q2 and q3

Keep q2 and q3 unchanged:

- q2: `high_risk` / `not_high_risk`
- q3: `escalate` / `no_escalate`

---

## 5. Historical Diagnostic Targets and Final Interpretation

The thresholds below were specified before the 2026-05-15 normalization audit and apply only to the superseded probability-scale residual. They are retained as instrument-development history, not as canonical CbD decision rules.

| Pattern | Interpretation |
|---|---|
| `healthcare_T6` legacy score collapses to near zero | Pattern is consistent with q1/q4 construct coupling; causal diagnosis remains unvalidated |
| `healthcare_T6` DI remains high but CNTX collapses | Direct influence remains, residual contextuality does not |
| `healthcare_T6` CNTX remains 1.000 | Constructs are still coupled or task has deeper context dependence |
| `insurance_T9` conflict legacy score remains >= 0.300 | Direct-influence challenge case remains informative |
| Negative controls remain 0.000 | Instrument stability preserved |
| Negative controls become nonzero | Phase 1.3 instrument is too disruptive; stop and redesign |

Near-zero threshold for Phase 1.3:

```
CNTX <= 0.100
```

Historical challenge-case threshold:

```
CNTX >= 0.300 in at least one Phase 1.3 control condition
```

---

## 6. Paper-Gate Decision Matrix

Observed final landing after canonical correction: all Qwen and Gemma 4 Phase 1.3 groups have `CNTX_canonical = 0.000`; RA-15 proceeds as a bounded method / negative-results paper, not a contextuality-positive study.

| Phase 1.3 result | RA-15 paper decision |
|---|---|
| Healthcare collapses; insurance conflict survives; negatives stable | Proceed with bounded audit-method paper |
| Healthcare remains but negatives stable and insurance survives | Proceed, but frame healthcare as construct-validity warning |
| Insurance conflict collapses; healthcare collapses; negatives stable | Pivot to measurement-artifact / prompt-audit note |
| Negative controls become unstable | Do not broaden; repair instrument |

---

## 7. Implementation Notes

1. Create a new renderer rather than mutating Phase 1.2 prompt artifacts. **Done:** `render_phase13_prompts.py`.
2. Preserve Phase 1.2 outputs exactly. **Done:** Phase 1.3 has separate prompt-freeze and output names.
3. Name all Phase 1.3 artifacts with `phase13_construct_decoupling_20260512`. **Done for prompt artifacts.**
4. Validate JSON first, then compute CbD metrics. **Done:** repaired output validates 384 / 384.
5. Report probability-scale direct influence, the auxiliary legacy residual, and canonical CbD separately. Do not treat high direct influence as contextuality.
6. Update `RA-15-CONTEXTUALITY-CONCEPT-NOTE.md` only after Phase 1.3 completes.

Generated prompt artifacts:

- `phase13_prompts_construct_decoupling_20260512.jsonl` — 384 records.
- `phase13_prompt_freeze_construct_decoupling_20260512.json` — prompt-freeze summary with 8 groups x 48 prompts.

Generated result artifacts:

- `phase13_outputs_qwen3_6_27b_nvfp4_construct_decoupling_20260512.jsonl` — raw local-Qwen output with one timeout row and one appended repair row.
- `phase13_outputs_qwen3_6_27b_nvfp4_construct_decoupling_repaired_20260512.jsonl` — analysis-ready repaired output, 384 rows.
- `phase13_cbd_summary_qwen3_6_27b_nvfp4_construct_decoupling_20260512.json` — final CbD summary.
- `PHASE1-3-REPORT-qwen3_6_27b_nvfp4-construct-decoupling-20260512.md` — narrative report.

Implemented run/analysis support:

- `run_phase13_ollama.py` — resumable local-Ollama runner.
- `run_phase13_openrouter.py` — resumable OpenRouter runner for long cloud-backed jobs.
- `validate_outputs.py` — updated to accept Phase 1.3 q1/q4 labels.
- `analyze_cbd.py` — updated to map Phase 1.3 q1/q4 labels to binary values.

Resume guardrail: Phase 1.3 runners key completed rows by `(condition, task_id, block, context_id, rep)`. The `condition` field is required because `role_fixed` and `order_neutral` share task/block/context/rep coordinates.

OpenRouter execution option:

```bash
OPENROUTER_API_KEY=... \
RA15_OPENROUTER_MODEL=qwen/qwen-2.5-72b-instruct \
python3 run_phase13_openrouter.py \
  --output phase13_outputs_openrouter_qwen_2_5_72b_construct_decoupling_20260512.jsonl \
  --restart
```

Interpretation guardrail: an OpenRouter run is a provider/model-lineage run, not a silent substitute for the local Ollama/Qwen run. If the selected OpenRouter model differs from `qwen3.6:27b-coding-nvfp4`, report it as a cloud-backed replication or acceleration run with `provider=openrouter` and the exact model identifier.

Environment compatibility: the RA-15 runner reads `OPENROUTER_API_KEY` and prefers `RA15_OPENROUTER_MODEL`, but also accepts the existing RA-6 / RA-3 model aliases (`RA6_OPENROUTER_MODEL`, `RA3_OPENROUTER_MODEL`) for continuity with prior OpenRouter experiments.

---

## 8. Pre-Run Checklist

- [x] q1/q4 labels updated in renderer and validator.
- [x] Phase 1.2 artifacts are copied only by reference, not overwritten.
- [x] Four minimum task/block groups selected.
- [x] Optional regulated-access task explicitly deferred; run 384-call minimum set first.
- [x] Expected row count computed before run: 384 calls.
- [x] Validator accepts the new q1/q4 labels.
- [x] Analysis script can read the Phase 1.3 labels without mapping them back to the older labels ambiguously.
- [x] Long-run OpenRouter option exists without mutating the frozen prompt set.
- [x] Local-Qwen Phase 1.3 run completed and repaired: 384 valid rows, 0 invalid rows.
