# RA-15 — Contextuality Auditor for Enterprise LLM Agents

**Full title:** Contextuality Auditor for Enterprise LLM Agents: A Negative-Results Method Study of Direct Influence and Construct Coupling

**Author:** Thanh Luong Tuan (Foundation AgenticOS; Golden Gate University)

**ORCID:** [0009-0000-1199-837X](https://orcid.org/0009-0000-1199-837X)

**Status:** reproducibility artifacts v1.1 public; arXiv submission pending

**Release tag:** `ra-15-artifacts-v1.1`

## Scope and claim boundary

RA-15 develops a bounded Contextuality-by-Default-style audit for forced-choice enterprise-agent decisions. The corrected Phase 1.3 result is a canonical contextuality null across every Qwen 3.6 and Gemma 4 group. The release therefore supports a method / negative-results claim: the audit separates stable controls, direct influence, measurement artifacts, and patterns consistent with construct coupling before any routing decision is made.

This release does **not** claim surviving canonical contextuality, independently validated construct coupling, or validated gains from debate, synthesis, or human-arbitration routing.

## Evidence included

The [`experiment/`](./experiment/) directory is the complete exploratory pilot history used by the manuscript, including:

- synthetic task and ontology inputs;
- prompt templates, rendered prompt matrices, and prompt-freeze metadata;
- local Qwen 3.6 and OpenRouter Gemma 4 raw and repaired Phase 1.3 outputs;
- Phase 0 through Phase 1.3 reports and protocols;
- the CbD analyzer, validators, prompt renderers, and model runners;
- canonical summary JSON files and five analytic fixtures.

The manuscript's primary endpoint uses these two repaired Phase 1.3 files:

- `phase13_outputs_qwen3_6_27b_nvfp4_construct_decoupling_repaired_20260512.jsonl` — 384 / 384 valid;
- `phase13_outputs_openrouter_gemma4_31b_construct_decoupling_repaired_20260515.jsonl` — 384 / 384 valid.

Both canonical summaries report `cntx_canonical = 0.000` for all eight task/block/condition rows per endpoint. Twelve repetitions per context are repeated stochastic draws from a fixed endpoint, not independent task or subject units.

## Quick verification

From `RA-15/experiment/`:

```bash
python3 test_cbd_known_examples.py
python3 validate_outputs.py \
  --input phase13_outputs_qwen3_6_27b_nvfp4_construct_decoupling_repaired_20260512.jsonl
python3 validate_outputs.py \
  --input phase13_outputs_openrouter_gemma4_31b_construct_decoupling_repaired_20260515.jsonl
python3 analyze_cbd.py \
  --input phase13_outputs_qwen3_6_27b_nvfp4_construct_decoupling_repaired_20260512.jsonl \
  --output /tmp/ra15-qwen-summary.json
python3 analyze_cbd.py \
  --input phase13_outputs_openrouter_gemma4_31b_construct_decoupling_repaired_20260515.jsonl \
  --output /tmp/ra15-gemma-summary.json
```

The expected fixture results include a PR-box arithmetic check with canonical degree `1.000` and a legacy-positive/canonical-zero guard with canonical degree `0.000`.

## Data and ethics boundary

All prompts are synthetic benchmark scenarios. No human-subject observations, customer records, production tenant data, or personally identifiable information are included. Only synthetic prompts were sent to OpenRouter.

## Paper availability

The canonical manuscript will be linked here after it is posted to arXiv. In accordance with this repository's canonical-version policy, the pre-arXiv PDF, LaTeX source, and submission tarball are not mirrored in this release.

## Citation

Until the arXiv identifier is assigned, cite this tagged artifact release. The Zenodo DOI will be added to this page after the release is archived.

## License

The files in this public repository are released under the repository-level [MIT License](../LICENSE).
