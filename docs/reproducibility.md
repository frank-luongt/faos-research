# Reproducibility Notes

This document records the environmental assumptions, API access requirements, and replication protocol for the FAOS Research code.

## Environments tested

- **Primary:** macOS 14.x + Python 3.11.x
- **Secondary (CI):** Ubuntu 22.04 + Python 3.11.x

## API access

Both papers use commercial LLM APIs as generators and a fixed Claude Sonnet 4 judge.

| Role | Provider | Model | Env var |
|---|---|---|---|
| Primary generator · judge | Anthropic | `claude-sonnet-4-20250514` | `ANTHROPIC_API_KEY` |
| Cross-model generator (open-source large) | OpenRouter | `qwen/qwen-2.5-72b-instruct` | `OPENROUTER_API_KEY` |
| Cross-model generator (open-source small) | Google | `gemma-4-26b-it` | `GOOGLE_API_KEY` |

All judge calls use `T = 0.0` for deterministic evaluation. Generator calls use `T = 0.3` (E2 protocol fix) to balance diversity against reproducibility.

## Budget and runtime

| Scope | API cost (USD, approx) | Wall-clock time |
|---|---|---|
| RA-3 single-model pilot (600 runs) | \$40–60 | 6–8 hours |
| RA-3 three-model replication (1,800 runs) | \$120–160 | 3–4 days |
| RA-6 single-model pilot (1,800 scenarios + assess + FDR) | \$60–80 | 8–12 hours |
| RA-6 three-model replication (5,400 scenarios + per-model assess + FDR) | \$150–200 | 5–7 days wall-clock |

Costs dominated by judge calls (Claude Sonnet 4 at \~\$3 input / \$15 output per MTok).

## Resumability

All long-running scripts in both papers support resumption via incremental save:

- `run_experiment.py` (RA-3) checkpoints after every 25 tasks
- `generate_scenarios.py` (RA-6) checkpoints after every industry×condition cell
- `assess_coverage.py` / `detect_faults.py` (RA-6) checkpoint after each regulatory item / fault

Re-running with the same `--run-id` resumes from the last completed checkpoint. This is necessary for three-model replications where API rate limits and credit exhaustion events interrupt runs.

## Anti-circularity controls

### RA-3

- The ontology source files in `RA-3/ontology_context/*.json` are shared among C1–C4 conditions but the task-specific ontology views differ by condition (layer ablation).
- Task ground-truth answers are curated from non-ontology sources (primary regulations + published industry documentation) to prevent the judge from rewarding ontology-regurgitation.

### RA-6

- The 125-item regulatory checklist (25 per industry) in `RA-6/regulatory_checklists/*.json` is curated from primary statutory sources (31 CFR, NAIC Models, 45 CFR, SBV Circulars, Vietnamese Insurance Business Law) — not from the FAOS ontology YAMLs.
- For E1 anti-circularity, 30% of regulatory constraints are held out from the G4 generation prompt; seen vs unseen RC is reported separately in the analysis summaries.
- **Known limitation:** the checklist was curated by the same author who designed the FAOS ontology. This is a pseudo-circularity control, not an independent ground-truth check. Inter-rater validation by a non-author regulatory expert on a 20% random sample is flagged as the top near-term validation priority (see RA-6 Limitations §).

## LLM-as-judge caveats

A single Claude Sonnet 4 judge scores all outputs in both papers. Self-enhancement bias (the judge favouring Claude-style outputs) is a structural concern, not merely a residual one. Cross-generator replication does *not* correct for this because the judge is held constant. Follow-on work will triangulate with a non-Anthropic judge (GPT-4o or Gemini) on a stratified sub-sample and report judge–judge agreement.

## Regenerating paper figures from included summaries

Both paper-figure scripts read from the included aggregated JSONs:

```bash
cd RA-3/code && python generate_paper_figures.py    # reads ../results-summary/analysis_summary.json
cd RA-6/code && python generate_paper_figures.py    # reads ../results-summary/coverage_results.json
cd RA-6/code && python generate_crossmodel_figures.py
```

Outputs are 300-DPI PDFs using academic serif styling (mathpazo-compatible) and a colourblind-safe Okabe–Ito palette.

## Known reproducibility gotchas

- **Anthropic 529 overload responses** are transient; the resumption logic handles them automatically.
- **OpenRouter rate limits** for Qwen are tighter than Anthropic; set `--max-concurrent 2` if needed.
- **Google Gemma** returns `<thought>...</thought>` tags that must be stripped before JSON parsing; code handles this in `judge.py`.
- **Python 3.14 compatibility**: if building on 3.14+, add `certifi.where()` for SSL verification.
