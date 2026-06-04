# RA-1 — Dynamic Coordination Strategy Selection for Enterprise Multi-Agent Systems

**Authors:** Thanh Luong Tuan
**Status:** arXiv-live — [`arXiv:2606.00804`](https://arxiv.org/abs/2606.00804) (cs.MA)
**Last revised:** 2026-06-04

Enterprise multi-agent systems increasingly expose multiple coordination patterns, but deployments often lack evidence for when to use consensus, debate, synthesis, or a simpler single-agent workflow. This paper evaluates whether coordination strategy should be selected dynamically by problem class rather than fixed globally. We run a frozen matrix of 30 enterprise tasks spanning six industries, five problem classes, four execution conditions, three replications per cell, and four model arms: qwen_local, sonnet, gemma_openrouter, and an auxiliary openai cloud-validation arm. All 1,440 generated outputs are judged by a fixed Sonnet rubric.

The main finding is bounded and operationally useful, but it is not the original strict H1. The pre-registered exact-winner/CI criterion is not supported: exact winner identity is unstable across model arms, and several predicted strategies are close to, but not above, the best observed alternative. A weaker near-best routing claim is strongly supported. In every pre-registered model arm and problem class, and again in the auxiliary OpenAI validation arm, the predicted strategy is within 0.10 quality-score points of the best observed condition. Structured compliance verification is the clearest exception to the original mapping: all arms favor single_agent rather than consensus. A pre-registered Kendall's W test finds no reliable difference between Vietnamese-domain and English-domain tasks in how consistently the four coordination conditions are ranked (mean W of 0.20 in both strata; signed-rank p = .85), so H2 is not supported. We conclude that enterprise coordination policy should use dynamic routing as a calibrated default, not as a deterministic winner-selection law.

## Paper

The canonical version of this paper lives on arXiv: **[arXiv:2606.00804](https://arxiv.org/abs/2606.00804)**. Per the FAOS Research Programme policy, this directory carries reproducibility scaffolding; paper artifacts (PDF, LaTeX, bibliography, submission tarball, figures) are mirrored here only after the canonical version is live on arXiv or accepted by a journal.

## Key results

- **Strict H1 (exact-winner per problem class): not supported.** Winner identity is unstable across model arms; several predicted strategies land close to, but not above, the best observed alternative.
- **Near-best routing: strongly supported.** In every pre-registered model arm and problem class — and in the auxiliary OpenAI arm — the predicted strategy is within **0.10** quality-score points of the best observed condition.
- **PC4 (structured compliance verification) is the clear exception:** all arms favor `single_agent` over `consensus`.
- **H2 (Vietnamese- vs English-domain rank concordance): not supported.** Pre-registered Kendall's *W* = 0.20 in both strata; signed-rank *p* = .85.
- **Conclusion:** treat dynamic coordination routing as a calibrated default, not a deterministic winner-selection law.

Formal statistics use seed `20260527` with 5,000 permutation and 5,000 bootstrap replications over the frozen 1,440-row matrix.

## Contents (reproducibility scaffolding)

- `code/` — analysis and methodology scripts:
  - `formal_analysis.py` — pre-registered omnibus + H1 near-best analysis (permutation/bootstrap)
  - `h2_kendall_w.py` — H2 Kendall's *W* concordance test (VI vs EN strata)
  - `pc2_pc4_failure_coding.py` — systematic coordination-harm coding for PC2/PC4
  - `analyze_results.py` — descriptive aggregation across arms and conditions
  - `build_task_corpus.py` — corpus assembly provenance (RA-3 task pool + RA-1 supplements)
  - `judge_deferred_results.py` — fixed-Sonnet-rubric judging harness
  - `pilot_coder_bias.py` — pilot coder-bias assessment
- `results-summary/` — aggregated analysis JSONs (paths repo-relative):
  - `formal_analysis_summary.json`, `h2_kendall_w_summary.json`, `pc2_pc4_failure_coding.json`, `analysis_summary.json`
  - `SECOND-JUDGE-DEDUP-NOTE-2026-05-30.md` — second-judge dedup discipline (de-duplicate by `(arm, task, condition)` before recomputing)
- `tasks/` — task-corpus inputs:
  - `balanced_supplement_tasks.json` — RA-1 supplement task set
  - `problem_class_map.csv` — task → problem-class (PC1–PC5) mapping
  - `problem_class_rater_protocol_v1.md` — independent problem-class rater protocol
- `CROSS-MODEL-PROTOCOL.md` — four-arm cross-model evaluation protocol
- `citation-audit.md` — WebSearch-verified citation integrity audit (0 fabrications)
- `references.bib` — bibliography
- `requirements.txt` — Python dependencies

## Reproduction notes

The analysis scripts recompute the paper's reported statistics from the per-row judged matrix. The **raw model outputs and judged transcripts** (the `results_judged_*` / `results_raw_*` CSVs) are released alongside the frozen-version Zenodo DOI **at journal acceptance**, per the programme's post-acceptance raw-data policy; until then this directory provides the scripts, task corpus, aggregated summaries, and protocols. Corpus assembly (`build_task_corpus.py`) draws on the RA-3 task pool (see [`../RA-3/`](../RA-3/) and [`arXiv:2604.00555`](https://arxiv.org/abs/2604.00555)) plus the RA-1 supplements in `tasks/`.

## Citation

```bibtex
@misc{luong2026coordination,
  author       = {Luong, Thanh Tuan},
  title        = {Dynamic Coordination Strategy Selection for Enterprise Multi-Agent Systems},
  year         = {2026},
  eprint       = {2606.00804},
  archivePrefix= {arXiv},
  primaryClass = {cs.MA},
  howpublished = {\url{https://arxiv.org/abs/2606.00804}}
}
```

## License

Code, task corpus, protocols, and aggregated results released under the MIT licence (see repository root [`LICENSE`](../LICENSE)).
