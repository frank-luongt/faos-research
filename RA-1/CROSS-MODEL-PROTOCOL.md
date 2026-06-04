# RA-1 — Cross-Model Evaluation Protocol

This protocol documents the four-arm, cross-model design used to test whether the dynamic
coordination-routing finding holds across heterogeneous LLM families rather than a single model.

## Model arms (4)

| Arm | Role | Pre-registered? |
|---|---|---|
| `sonnet` | Claude Sonnet (primary; cross-study compatibility with the rest of the programme) | Yes |
| `qwen_local` | Local open-weight model (Ollama) | Yes |
| `gemma_openrouter` | Open-weight model served via OpenRouter | Yes |
| `openai` | Cloud model, **auxiliary validation arm** added during execution | No (auxiliary) |

The headline claims are based on the three pre-registered arms; the auxiliary `openai` arm is reported
separately as out-of-sample validation and is not used to define the primary result.

## Execution conditions (4)

| Condition | Definition |
|---|---|
| `single_agent` | Solo execution, no coordination strategy (control / baseline reference) |
| `consensus` | N agents propose independently → aggregator selects the majority / weighted-mean answer |
| `debate` | Two agents argue opposing positions → an arbiter selects the winner |
| `synthesis` | N agents propose independently → an aggregator integrates dimensions of all proposals into a novel answer |

Coordination strategies are operationalized from production multi-agent practice; they are evaluated here
as a within-subjects factor with `single_agent` as the baseline reference point.

## Design factors

- **Industry (6):** FinTech (EN), Insurance (EN), Healthcare (EN), Banking VN (VI), Insurance VN (VI), Software (EN) — balanced across language (EN/VI) and coding-adjacency.
- **Problem class (5), with pre-registered predicted winner:**
  - **PC1** High-uncertainty risk decision → `consensus`
  - **PC2** Conflicting-objective tradeoff → `debate`
  - **PC3** Novel design synthesis → `synthesis`
  - **PC4** Structured compliance verification → `consensus` (or `single_agent` ceiling)
  - **PC5** Ambiguous-requirement clarification → `synthesis` (or `debate`)
- **Replications:** 3 per cell.

**Matrix size:** 6 industries × 5 problem classes = 30 tasks; 30 × 4 conditions × 3 reps × 4 arms = **1,440 judged outputs** (frozen).

## Judging

- A **single fixed Sonnet rubric** scores every row, so each output carries a comparable quality score; the design is paired across conditions within a (task, arm).
- **Second-judge sensitivity:** an external GPT-5.1 judge was run as a robustness check (Pearson *r* = 0.40, *n* = 480 after de-duplication). The PC4 `single_agent` dominance and the near-best routing pattern both replicate. See the paper §7.
- **Dedup discipline:** second-judge rows must be de-duplicated by `(arm, task, condition)` before any statistic is recomputed — the resumable runner can emit duplicate cells. See [`results-summary/SECOND-JUDGE-DEDUP-NOTE-2026-05-30.md`](results-summary/SECOND-JUDGE-DEDUP-NOTE-2026-05-30.md).

## Determinism and statistics

- Generation and judging at temperature `T = 0.0`.
- Formal analysis seed: `20260527`; 5,000 permutation replications and 5,000 bootstrap replications.
- Pre-registered hypotheses: **H1** (exact-winner per problem class) and **H2** (Kendall's *W* rank-concordance, VI vs EN strata). The supported result is the weaker **near-best** claim: the predicted strategy lands within 0.10 quality-score points of the best observed condition in every pre-registered arm and problem class.

## Corpus provenance

The full task corpus is assembled by `code/build_task_corpus.py` from the RA-3 task pool
(see [`../RA-3/`](../RA-3/), [`arXiv:2604.00555`](https://arxiv.org/abs/2604.00555)) plus the RA-1 supplement
tasks in [`tasks/balanced_supplement_tasks.json`](tasks/balanced_supplement_tasks.json), with the
problem-class mapping in [`tasks/problem_class_map.csv`](tasks/problem_class_map.csv).
