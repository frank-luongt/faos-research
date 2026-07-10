# RA-15 Phase 1 Smoke-Slice Report - Qwen 3.6 27B

**Date:** 2026-05-09
**Model:** `qwen3.6:27b-coding-nvfp4`
**Runner:** [`run_phase1_ollama.py`](run_phase1_ollama.py)
**Output:** [`phase1_outputs_qwen3_6_27b_nvfp4_smoke_20260509.jsonl`](phase1_outputs_qwen3_6_27b_nvfp4_smoke_20260509.jsonl)

---

## 1. Purpose

This smoke slice validates the Phase 1 execution path before launching
the full 576-call first-model pilot. It is not an empirical result for
RA-15, because it covers only the first 8 records from the Phase 1
manifest.

---

## 2. Manifest Check

The Phase 1 renderer produced the expected full prompt manifest:

| Split | Records |
|---|---:|
| Canonical block | 384 |
| Conflict block | 192 |
| **Total** | **576** |

Context counts:

| Context | Records |
|---|---:|
| C1 | 96 |
| C2 | 96 |
| C3 | 96 |
| C4 | 96 |
| C1X | 48 |
| C2X | 48 |
| C3X | 48 |
| C4X | 48 |

---

## 3. Smoke Run

Command shape:

```bash
python3 research-academic/experiments/RA-15-contextuality-pilot/run_phase1_ollama.py \
  --model qwen3.6:27b-coding-nvfp4 \
  --output research-academic/experiments/RA-15-contextuality-pilot/phase1_outputs_qwen3_6_27b_nvfp4_smoke_20260509.jsonl \
  --temperature 0.2 \
  --timeout 240 \
  --no-json-format \
  --limit 8
```

Result:

```json
{
  "total": 8,
  "valid": 8,
  "invalid": 0
}
```

All 8 runner records completed with no runner-level errors.

---

## 4. Runtime Estimate

Observed latency over the 8-record smoke slice:

| Metric | Seconds |
|---|---:|
| Minimum | 69.499 |
| Maximum | 145.617 |
| Mean | 101.653 |

At the observed mean latency, the full 576-call Phase 1 run is estimated
at approximately 16.26 hours.

---

## 5. Decision

Phase 1 tooling is ready. The full run should be launched only in an
overnight / long-running window, because local Qwen throughput is too
slow for an interactive session.
