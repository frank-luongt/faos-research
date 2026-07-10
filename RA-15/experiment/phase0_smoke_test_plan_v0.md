# RA-15 Phase 0 Smoke-Test Plan v0

**Date:** 2026-05-05; revised 2026-05-09
**Status:** Phase 0 v0.2 cleared; retained as rerun record
**Validator:** [`validate_outputs.py`](validate_outputs.py)

---

## 1. Purpose

Phase 0 checks the measurement instrument before any full RA-15 pilot run.
The first Phase 0 pass on 2026-05-05 produced 24/24 valid JSON records
but exposed q1 ambiguity on `fintech_T6`. This revised plan reruns the
same scope with q1 changed from `proceed` / `defer` to
`clear_to_continue` / `hold_for_review`.

**Rerun result:** Phase 0 v0.2 on 2026-05-09 produced 24/24 valid JSON
records and removed the q1-driven false-contextuality pattern
(`fintech_T6`: `CNTX = 0.0`, `DI_total = 0.0`, `q1_instability = 0.0`).
See [`PHASE0-REPORT-qwen3_6_27b_nvfp4-v02-20260509.md`](PHASE0-REPORT-qwen3_6_27b_nvfp4-v02-20260509.md).

The question is not whether contextuality exists. The question is simpler:

> Can the prompt reliably produce parseable binary measurements with exactly the requested q fields?

If no, do not run Phase 1.

---

## 2. Scope

Use:

- tasks: `software_T3`, `fintech_T6`
- ontology block: canonical only
- contexts: `C1`, `C2`, `C3`, `C4`
- repetitions: 3 per task/context
- model: primary RA-1 model

Expected calls:

```
2 tasks x 4 contexts x 3 reps = 24 calls
```

---

## 3. Required Input Columns

Store model outputs as JSONL. Each line must have:

```json
{
  "task_id": "software_T3",
  "block": "canonical",
  "context_id": "C1",
  "rep": 1,
  "model": "model-name",
  "response": "{\"q1\":\"hold_for_review\",\"q2\":\"high_risk\",\"rationale\":\"...\"}"
}
```

The `response` field may be either:

1. a JSON object; or
2. a string containing a JSON object.

---

## 4. Pass Criteria

Phase 0 passes only if:

- parseable rate is >= 95%;
- measured-field correctness is 100%;
- allowed-label correctness is 100%;
- rationale is present in 100%;
- no response includes unmeasured q fields.
- low-conflict `fintech_T6` does not show q1-driven false contextuality
  in the CbD smoke summary.

With 24 calls, one parse failure is tolerable for parseable rate, but any field/label schema failure blocks Phase 1.

---

## 5. Stop Conditions

Stop and revise prompt templates if any of these occur:

- model returns markdown fences around JSON more than once;
- model includes unmeasured q fields;
- model emits labels outside the allowed set;
- rationale includes chain-of-thought style hidden reasoning;
- response cannot be parsed after one simple JSON extraction attempt.

---

## 6. Validation Command

Render the 24 Phase 0 prompts:

```bash
python3 research-academic/experiments/RA-15-contextuality-pilot/render_phase0_prompts.py \
  --output research-academic/experiments/RA-15-contextuality-pilot/phase0_prompts.jsonl
```

After collecting outputs:

```bash
python3 research-academic/experiments/RA-15-contextuality-pilot/validate_outputs.py \
  --input research-academic/experiments/RA-15-contextuality-pilot/phase0_outputs.jsonl
```

For local fixture validation:

```bash
python3 research-academic/experiments/RA-15-contextuality-pilot/validate_outputs.py \
  --input research-academic/experiments/RA-15-contextuality-pilot/sample_phase0_outputs_valid.jsonl
```

---

## 7. Phase 0 Decision

| Result | Decision |
|---|---|
| Pass all criteria and remove q1-driven false contextuality | Move to Phase 1 first-model pilot |
| Parse failures only | Tighten JSON-only prompt and rerun Phase 0 |
| Field/label failures | Revise template and validator; rerun Phase 0 |
| Rationale quality problem | Tighten rationale instruction; rerun Phase 0 |
| Parser passes but `fintech_T6` still shows q1-driven contextuality | Revise q1 again or make q1 task-specific before Phase 1 |
