# RA-15 Artifact Manifest v1.1

**Release date:** 2026-07-10

**Release tag:** `ra-15-artifacts-v1.1`

**Public snapshot:** <https://github.com/frank-luongt/faos-research/tree/ra-15-artifacts-v1.1/RA-15/experiment>

**Zenodo version DOI:** <https://doi.org/10.5281/zenodo.21288508>

**Zenodo concept DOI:** <https://doi.org/10.5281/zenodo.21288507>

**License:** MIT; see repository `LICENSE`

This manifest identifies the primary empirical artifacts used by the RA-15 method / negative-results manuscript. The complete exploratory pilot history is stored in `experiment/`. It contains synthetic prompts only; it contains no customer records, production tenant data, human-subject observations, or personally identifiable information.

## Primary Experiment Artifact Checksums

```text
2b23861915fdb68cfd57baa675e1effd3ecd825ea0581e0bf1dbc25d38ce9f42  experiment/phase13_prompts_construct_decoupling_20260512.jsonl
95133224c208491256cfa46526fbea2028ffcf3c57dcef98b3b3555bc0c98ea7  experiment/phase13_prompt_freeze_construct_decoupling_20260512.json
08091219645a7f781f6915ea901334c1b4fa4ec26a8931f200e92299904e3cb0  experiment/phase13_outputs_qwen3_6_27b_nvfp4_construct_decoupling_20260512.jsonl
064242ab5c4343cf54c6e68178c261d8abce6b59387e97b40559f8d5bb4453c7  experiment/phase13_outputs_qwen3_6_27b_nvfp4_construct_decoupling_repaired_20260512.jsonl
ca07e8bdcf50f2ca5de4dd53c460189bbf27fc8b79696d4e5e274f202fcd6fc5  experiment/phase13_cbd_summary_qwen3_6_27b_nvfp4_construct_decoupling_20260512.json
5fbe125819197f9b7d2465d9425cbae0d6cf3c893e19f5265573ec9b4b738d1a  experiment/phase13_outputs_openrouter_gemma4_31b_construct_decoupling_20260515.jsonl
d54c93d8db013c0aab7851642cfa415d86aef683ef58bc561b970098597a4b6e  experiment/phase13_outputs_openrouter_gemma4_31b_construct_decoupling_repaired_20260515.jsonl
6fe56c579ab0d293deb79d424236f766e9aee3686495ed66ccd9973d0b2b32e5  experiment/phase13_cbd_summary_openrouter_gemma4_31b_construct_decoupling_20260515.json
15ddc2d31504e038f6c6925b32c837883ead676cbc20e514c5fc8f0f9b6a8faf  experiment/analyze_cbd.py
621e76a037976d3f5133973b85592b0795be51d10e3d953b7d6a21bc485e248f  experiment/validate_outputs.py
89e3767ca86b4a6bb50a3c04fd624c9651d7fd8b33c4c7f2521818f7984f1f39  experiment/test_cbd_known_examples.py
```

## Model and Sampling Scope

- Local endpoint: Ollama `qwen3.6:27b-coding-nvfp4`, artifact ID `42a2d9de99b0`, architecture `qwen3_5`, 27.4B parameters, NVFP4; temperature `0.2`, no JSON response-format constraint, timeout 420 seconds, no explicit token cap.
- Routed endpoint: OpenRouter alias `google/gemma-4-31b-it`; temperature `0.2`, 500-token cap, prompt-only JSON instruction, timeout 240 seconds.
- Historical records do not retain seeds, cache state, randomized call order, or the immutable OpenRouter provider/backend revision.
- Twelve repetitions per context are repeated stochastic draws from a fixed endpoint, not independent task or subject units.

## Paper-package boundary

The pre-arXiv PDF, LaTeX source, generated bibliography, and submission tarball are intentionally excluded under the repository's canonical-version policy. They will be mirrored only after the canonical preprint is live on arXiv.
