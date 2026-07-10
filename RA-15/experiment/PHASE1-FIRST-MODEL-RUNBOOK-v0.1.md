# RA-15 Phase 1 First-Model Pilot Runbook v0.1

**Date:** 2026-05-09
**Status:** Smoke slice passed; full 576-call run ready for deliberate launch
**Model:** `qwen3.6:27b-coding-nvfp4`
**Renderer:** [`render_phase1_prompts.py`](render_phase1_prompts.py)
**Runner:** [`run_phase1_ollama.py`](run_phase1_ollama.py)

---

## 1. Purpose

Phase 1 is the first empirical gate for the RA-15 thesis. Phase 0 only
proved that the measurement instrument can produce parseable and
semantically interpretable binary observations. Phase 1 asks whether the
pilot design produces any residual-contextuality signal worth scaling.

Do not promote RA-15 to a full paper scaffold unless Phase 1 shows that
`CNTX` adds signal beyond direct influence, output entropy, and simple
task instability.

---

## 2. Call Matrix

| Arm | Tasks | Contexts | Reps | Calls |
|---|---:|---:|---:|---:|
| Canonical block | 8 | 4 | 12 | 384 |
| Conflict block | 4 high-conflict tasks | 4 | 12 | 192 |
| **Total** | 8 | - | 12 | **576** |

High-conflict tasks with conflict block:

- `fintech_T9`
- `insurance_T9`
- `insurance_vn_T8`
- `software_T3`

Low-conflict tasks run canonical only:

- `fintech_T6`
- `insurance_T6`
- `healthcare_T6`
- `banking_vn_T6`

At the Phase 1 smoke-slice observed local-Qwen speed, a full 576-call
run is estimated at about 16 hours. Prefer a manifest/dry-run check and
an overnight execution window before starting the full runner.

---

## 3. Dry-Run Manifest

Render the full Phase 1 prompt manifest:

```bash
python3 research-academic/experiments/RA-15-contextuality-pilot/render_phase1_prompts.py \
  --output research-academic/experiments/RA-15-contextuality-pilot/phase1_prompts_qwen3_6_27b_nvfp4_v01_20260509.jsonl
```

Expected:

```json
{
  "records": 576
}
```

For a quick smoke slice:

```bash
python3 research-academic/experiments/RA-15-contextuality-pilot/run_phase1_ollama.py \
  --model qwen3.6:27b-coding-nvfp4 \
  --output research-academic/experiments/RA-15-contextuality-pilot/phase1_outputs_qwen3_6_27b_nvfp4_representative_smoke_20260509.jsonl \
  --temperature 0.2 \
  --timeout 240 \
  --no-json-format \
  --smoke-representative
```

Observed smoke-slice result on 2026-05-09:

- Runner completed 8/8 records with no errors.
- Validator returned 8 valid / 0 invalid.
- Mean latency was 101.653 seconds per call.
- Full-run estimate at that speed is 16.26 hours.

The first smoke slice covered only the first 8 manifest records
(`fintech_T9`, canonical `C1`). Before the full run, use
`--smoke-representative` to cover one canonical and conflict record for
each context shape (`C1`--`C4`, `C1X`--`C4X`).

---

## 4. Full Run

```bash
python3 research-academic/experiments/RA-15-contextuality-pilot/run_phase1_ollama.py \
  --model qwen3.6:27b-coding-nvfp4 \
  --output research-academic/experiments/RA-15-contextuality-pilot/phase1_outputs_qwen3_6_27b_nvfp4_v01_20260509.jsonl \
  --temperature 0.2 \
  --timeout 240 \
  --no-json-format \
  --resume
```

Validate:

```bash
python3 research-academic/experiments/RA-15-contextuality-pilot/validate_outputs.py \
  --input research-academic/experiments/RA-15-contextuality-pilot/phase1_outputs_qwen3_6_27b_nvfp4_v01_20260509.jsonl
```

Analyze:

```bash
python3 research-academic/experiments/RA-15-contextuality-pilot/analyze_cbd.py \
  --input research-academic/experiments/RA-15-contextuality-pilot/phase1_outputs_qwen3_6_27b_nvfp4_v01_20260509.jsonl \
  --output research-academic/experiments/RA-15-contextuality-pilot/phase1_cbd_summary_qwen3_6_27b_nvfp4_v01_20260509.json
```

---

## 5. Phase 1 Decision Rules

| Result | Decision |
|---|---|
| `CNTX` higher in high-conflict tasks and/or conflict blocks, beyond direct influence | Promote to full RA-15 scaffold design |
| Direct influence high but `CNTX` null | Pivot toward prompt/role/context invariance audit |
| Low-conflict canonical tasks show high `CNTX` | Treat as measurement artifact; inspect labels/snippets before scale-up |
| Parser/schema failures exceed Phase 0 tolerance | Repair prompt/validator before interpreting metrics |
| Uniform `CNTX = 0` across all groups | Do not launch full contextuality paper; archive or pivot |

Phase 1 is still descriptive at 8 tasks. It can justify a full scaffold
only as a signal gate, not as a publishable inferential result by itself.
