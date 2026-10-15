# RA-1 — Dynamic Coordination Strategy Selection for Enterprise Multi-Agent Systems

**Authors:** Thanh Luong Tuan
**Status:** arXiv-live — [`arXiv:2606.00804`](https://arxiv.org/abs/2606.00804) (cs.MA)
**Last revised:** October 15, 2026 (README correction; the paper on arXiv is unchanged)

> **Correction (October 15, 2026).** Versions 1 and 2 of arXiv:2606.00804 reported a near-best routing result as support for problem-class routing. That claim is retired, because the criterion behind it is met as well by fixed policies that ignore problem class (see Key results). The corrected record is **arXiv:2606.00804v3**, which is prepared but **not yet posted**. Until it posts, the live arXiv version is v2 (June 4, 2026), and its abstract still carries the retired claim. This README follows the corrections prepared for v3.

Enterprise multi-agent systems increasingly expose multiple coordination patterns, but deployments often lack evidence for when to use consensus, debate, synthesis, or a simpler single-agent workflow. This paper evaluates whether coordination strategy should be selected dynamically by problem class rather than fixed globally. We run a frozen matrix of 30 enterprise tasks spanning six industries, five problem classes, four execution conditions, three replications per cell, and four model arms: qwen_local, sonnet, gemma_openrouter, and an auxiliary openai cloud-validation arm. All 1,440 generated outputs are judged by a fixed Sonnet rubric.

The pre-registered exact-winner/CI criterion is not supported: exact winner identity is unstable across model arms, and several predicted strategies are close to, but not above, the best observed alternative. The near-best routing claim of versions 1 and 2 is retired, because the criterion behind it is met as well by fixed policies that ignore problem class. On structured compliance verification, single_agent leads consensus in all four arms, significantly in only one, and in the pre-registered arms the coordination loss is concentrated in the three of the five regulatory-compliance-scored tasks whose obligations the judge scored against an empty requirements list, so that result should not be relied on before those responses are re-judged. A pre-registered Kendall's W test finds no reliable difference between Vietnamese-domain and English-domain tasks in how consistently the four coordination conditions are ranked (mean W of 0.20 in both strata; signed-rank p = .85), so H2 is not supported. We conclude that this design cannot adjudicate dynamic routing against a fixed coordination policy.

## Paper

The canonical version of this paper lives on arXiv: **[arXiv:2606.00804](https://arxiv.org/abs/2606.00804)**. Per the FAOS Research Programme policy, this directory carries reproducibility scaffolding; paper artifacts (PDF, LaTeX, bibliography, submission tarball, figures) are mirrored here only after the canonical version is live on arXiv or accepted by a journal.

## Key results

- **Strict H1 (exact-winner per problem class): not supported.** Winner identity is unstable across model arms; several predicted strategies land close to, but not above, the best observed alternative.
- **Near-best routing: retired (v3 correction note).** The post-hoc criterion (the predicted strategy within **0.10** quality-score points of the best observed condition) is met in all 20 arm-by-problem-class cells, but it does not discriminate. Three fixed policies that ignore problem class (always `single_agent`, always `consensus`, always `debate`) also meet it in 20 of 20 cells; always-`single_agent`, the one policy the predicted mapping cannot emit, strictly dominates the mapping at every tighter band; and routing uniformly at random among the four conditions would meet it in every cell with probability 0.56. Mean per-cell best-minus-worst spread over the 20 cells is 0.0487, so the band admits about twice the range it measures. This design cannot separate problem-class routing from a fixed single-agent policy; that is not a finding that routing is harmful. All of these figures recompute from the cell means in `results-summary/formal_analysis_summary.json`.
- **PC4 (structured compliance verification), with an instrument caveat:** on point estimates `single_agent` leads `consensus` in all four arms, but significantly in only one (per-arm Friedman permutation *p* = .035 for `gemma_openrouter`; .18 to .78 elsewhere). Five of the six PC4 tasks are scored on the regulatory-compliance rubric, and three of them (`banking_vn_T6`, `fintech_T6`, `insurance_T6`) were judged against an empty requirements list. In the pre-registered arms the coordination loss is concentrated in those three (mean coordination effect −0.139 over 27 blocks, against −0.020 over 18 blocks for the other two regulatory-compliance-scored tasks). The v3 paper (Section 7) treats a re-judge against a completed reference list as required before the compliance result is relied on.
- **H2 (Vietnamese- vs English-domain rank concordance): not supported.** Pre-registered Kendall's *W* = 0.20 in both strata; signed-rank *p* = .85.
- **Conclusion:** this design cannot adjudicate dynamic routing against a fixed coordination policy. These data support neither a deterministic winner-selection law nor problem-class routing as a default; the strict exact-winner result (H1 not supported) is unchanged.

Formal statistics use seed `20260527` with 5,000 permutation and 5,000 bootstrap replications over the frozen 1,440-row matrix.

## Contents (reproducibility scaffolding)

- `code/` — analysis and methodology scripts:
  - `formal_analysis.py` — pre-registered omnibus and strict-H1 tests (permutation/bootstrap), plus a post-hoc 0.10 tolerance-band analysis, the retired criterion (see the note on `results-summary/` below)
  - `h2_kendall_w.py` — H2 Kendall's *W* concordance test (VI vs EN strata)
  - `pc2_pc4_failure_coding.py` — systematic coordination-harm coding for PC2/PC4
  - `analyze_results.py` — descriptive aggregation across arms and conditions
  - `build_task_corpus.py` — corpus assembly provenance (RA-3 task pool + RA-1 supplements)
  - `judge_deferred_results.py` — fixed-Sonnet-rubric judging harness
  - `pilot_coder_bias.py` — pilot coder-bias assessment
- `results-summary/` — aggregated analysis JSONs (paths repo-relative):
  - `formal_analysis_summary.json`, `h2_kendall_w_summary.json`, `pc2_pc4_failure_coding.json`, `analysis_summary.json`
  - `SECOND-JUDGE-DEDUP-NOTE-2026-05-30.md` — second-judge dedup discipline (de-duplicate by `(arm, task, condition)` before recomputing)
  - **Note on retired fields.** In `analysis_summary.json`, the `h1_provisional` block (`provisional_pass` true for all four arms under `h1_threshold` ">=4 hits per model", scored with the 0.10 margin in `code/analyze_results.py`) and, in `formal_analysis_summary.json`, the 20 `tolerance_hit_0_10` fields (all true) encode the retired 0.10-band criterion. The files are left unaltered, as published here with v2 on June 4, 2026; a `true` in these fields is not evidence for routing (see Key results). Likewise, the interpretation lines that `code/formal_analysis.py` writes into its generated Markdown packet (the "near-best" label at line 269, "preserves the tolerance-band H1 result" at line 292, and "PC4 remains the main policy revision" at line 294) encode the retired 0.10-band reading and a withdrawn PC4 routing revision. They are not findings; the script is left unaltered so that it reproduces the published outputs.
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
