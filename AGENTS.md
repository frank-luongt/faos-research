# AGENTS.md

## Cursor Cloud specific instructions

This repository (FAOS Research Programme) is a **Python research-artifact repo**, not an
application/service. Each `RA-*/` directory is an independent reproducibility bundle for one
paper. There is no web server, no build system, and no lint config. Python 3.11+ is required
(the VM has 3.12); dependencies are refreshed automatically by the environment update script
from the per-subproject `requirements.txt` files (union: `anthropic`, `pandas`, `scipy`,
`matplotlib`, `seaborn`, `numpy`, `certifi`). Do not add lint/build tooling.

### What can run offline (no API keys) — use these to verify the environment

- **RA-6** full offline pipeline (reproduces paper analysis + figures from bundled JSON):
  - `analyze_results.py` recomputes `analysis_summary.json` (Friedman/post-hoc) from
    `coverage_results.json` + `fdr_results.json`.
  - `generate_paper_figures.py` and `generate_crossmodel_figures.py` render PDFs.
- **RA-15/experiment** (`test_cbd_known_examples.py`, `validate_outputs.py`, `analyze_cbd.py`)
  runs entirely on bundled JSONL. Exact commands are in `RA-15/README.md`. Expected results:
  fixtures give PR-box canonical `1.000`; both primary Phase 1.3 endpoints validate 384/384 and
  report `cntx_canonical = 0.000`. `test_cbd_known_examples.py` is the closest thing to a test
  suite in this repo.

### Non-obvious gotchas

- **Data lives one level up from where scripts read it.** RA-3/RA-6 scripts use
  `config.RESULTS_DIR` = `<RA>/code/results/` and `config.ONTOLOGY_DIR` = `<RA>/code/ontology_context/`,
  but the shipped data is in `<RA>/results-summary/*.json` and `<RA>/ontology_context/*.json`.
  Before running offline, copy the needed files into `code/`:
  `mkdir -p RA-6/code/results && cp RA-6/results-summary/*.json RA-6/code/results/`.
- **These staged/generated paths are NOT gitignored:** `RA-*/code/results/`,
  `RA-*/code/ontology_context/`, and generated `papers/` figure dirs. They are derived artifacts —
  do not commit them. (Only `results_raw*.csv` and `generated_scenarios*.json` are gitignored.)
- **RA-1 and RA-3 analysis scripts cannot run offline in this checkout.** They require raw
  per-row CSVs (`results_raw*.csv`, `results_judged*.csv`) that are intentionally withheld
  (gitignored / deferred to Zenodo per the Data Availability policy). `RA-3 analyze_entropy.py`
  loads the baseline CSV in `main()` even with `--ontology-only`, so it also fails without the CSV.
- **RA-4, RA-11, RA-12** are embargo/doc-only placeholders (no runnable code).

### Requires secrets / external infra (do NOT run by default — costs real money)

- Live experiment scripts need API keys via a repo-root `.env` (loaded by `config.py`) or env
  vars: `ANTHROPIC_API_KEY` (always, judge), plus optional `OPENROUTER_API_KEY`, `GOOGLE_API_KEY`,
  `DASHSCOPE_API_KEY`. These include `RA-3/code/run_experiment.py`,
  `RA-6/code/{generate_scenarios,assess_coverage,detect_faults}.py`, and
  `RA-1/code/{judge_deferred_results,pilot_coder_bias}.py`.
- `RA-15/experiment/run_phase*_ollama.py` need a local Ollama daemon + pulled models;
  `run_phase13_openrouter.py` needs `OPENROUTER_API_KEY`.

See `README.md` and `docs/reproducibility.md` for the canonical reproduction commands.
