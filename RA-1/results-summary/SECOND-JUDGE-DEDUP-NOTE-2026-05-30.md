# RA-1 Second-Judge CSV — Deduplication Note (2026-05-30)

**Scope:** reproducibility guard for `results_secondjudge_gpt51_2026_05_29.csv` and manuscript §7
(GPT-5.1 second-judge sensitivity study).

## Finding

The second-judge file contains **539 rep-1 rows**, of which **59 are duplicate
`(model_arm, task_id, condition)` cells** produced by the resumable re-scoring runner
(`second_judge_openai.py --resume`). Per-arm raw counts are uneven (gemma 120, openai 131,
qwen 144, sonnet 144) for this reason.

The official §7 analysis **deduplicates to 480 unique cells** (30 tasks × 4 conditions × 4 arms,
120 per arm). All 539 rows belong to the frozen 30-task set; none are out-of-frame.

## Verified numbers (dedup by `(model_arm, task_id, condition)`)

| Quantity | Deduplicated (n=480) | Manuscript §7 | Match |
| --- | ---: | ---: | :---: |
| Pearson r (Sonnet vs GPT) | 0.399 (keep-first) / 0.400 (cell-mean) | 0.40 | ✓ |
| n | 480 | 480 | ✓ |
| Sonnet mean | 0.893 | 0.893 | ✓ |
| GPT mean | 0.953 | 0.953 | ✓ |
| GPT best condition | Gemma/Qwen/Sonnet → single_agent; OpenAI → consensus | same | ✓ |

## Guard

A **naive Pearson on the raw 539 rows yields r = 0.385** (rounds to 0.39), which would
*understate* the agreement and contradict §7. Any recomputation must dedupe first:

```python
seen=set(); dd=[]
for row in rows:
    k=(row["model_arm"], row["task_id"], row["condition"])
    if k in seen: continue
    seen.add(k); dd.append(row)            # -> 480 cells, r ≈ 0.40
```

Verified 2026-05-30 (Builder-Researcher, pre-arXiv integrity sweep). §7 stands as written.
