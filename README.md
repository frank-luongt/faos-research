# FAOS Research

**Code, data, and ontologies for ontology-powered enterprise AI agent verification.**

This repository accompanies two research papers from the Foundation AgenticOS (FAOS) programme at Golden Gate University. It provides the analysis code, industry ontologies, regulatory checklists, fault definitions, and aggregated results needed to reproduce and audit the papers' empirical claims.

---

## Papers

### RA-3 — Neurosymbolic Enterprise AI

*Ontology-Driven vs. RAG-Augmented vs. Baseline: A Controlled Study of Neurosymbolic Grounding for Enterprise AI Agents.*
Thanh Luong Tuan · Abhijit Sanyal. 2026.
Four-condition study across five regulated industries with Claude Sonnet 4 / Qwen 2.5 72B / Gemma 4 26B (1,800 runs total). Code + data in [`RA-3/`](./RA-3/).

### RA-6 — Agent Simulation, Testing & Formal Verification

*Toward Verifiable Enterprise AI Agents: Ontology-Powered Simulation and Formal Trust Certification.*
Thanh Luong Tuan · Abhijit Sanyal. 2026.
Four-condition scenario-generation study across five regulated industries, replicated across three generator LLMs (5,400 scenarios). Code + data in [`RA-6/`](./RA-6/).

Both papers share Vietnamese Banking and Vietnamese Insurance as empirical verticals; both use industry ontologies drawn from the FAOS platform; both use an LLM-as-judge evaluation pipeline at $T = 0.0$.

---

## Repository layout

```text
faos-research/
├── README.md                    ← this file
├── LICENSE                      ← MIT
├── CITATION.cff                 ← structured citation metadata
├── .gitignore
├── RA-3/
│   ├── CROSS-MODEL-PROTOCOL.md  ← 3-model replication protocol
│   ├── requirements.txt
│   ├── code/
│   │   ├── run_experiment.py
│   │   ├── analyze_results.py
│   │   ├── analyze_crossmodel.py
│   │   ├── analyze_entropy.py
│   │   ├── conditions.py
│   │   ├── config.py
│   │   ├── judge.py
│   │   ├── generate_paper_figures.py
│   │   ├── generate_dissertation_figures.py
│   │   └── tasks.json           ← 50 evaluation tasks
│   ├── ontology_context/        ← industry ontologies (5 verticals)
│   └── results-summary/         ← aggregated JSONs (no raw transcripts)
└── RA-6/
    ├── CROSS-MODEL-PROTOCOL.md
    ├── requirements.txt
    ├── code/
    │   ├── run_experiment.py
    │   ├── generate_scenarios.py
    │   ├── assess_coverage.py
    │   ├── detect_faults.py
    │   ├── analyze_results.py
    │   ├── analyze_crossmodel.py
    │   ├── generate_paper_figures.py
    │   ├── generate_crossmodel_figures.py
    │   └── config.py
    ├── ontology_context/        ← industry ontologies (5 verticals)
    ├── regulatory_checklists/   ← 125-item primary-source checklist
    ├── fault_definitions/       ← 25 injected faults across 5 categories
    └── results-summary/         ← aggregated JSONs
```

---

## Staged data release policy

This repository follows a staged release model:

| Release stage | Contents | Status |
|---|---|---|
| **v0.1 (now)** | All analysis code · ontology context · regulatory checklists · fault definitions · aggregated result JSONs (summaries, per-condition means, stat tests) | public |
| **v0.2 (on paper acceptance)** | Full scenario corpus · raw LLM outputs · judge evaluation logs | planned |
| **v1.0 (post-publication)** | Zenodo archive with DOI for citable long-term preservation | planned |

**What is in `results-summary/` now:** per-model aggregated analyses sufficient to re-derive every numeric claim in the papers (effect sizes, $p$-values, Kendall's $W$, per-industry breakdowns, cross-model comparisons).

**What is NOT in `results-summary/` yet:** raw LLM-generated scenario text and raw judge transcripts. These will be released under the same license at paper acceptance, per the papers' Data Availability statements.

---

## Reproduction

### Prerequisites

- Python 3.11+
- API access to one or more of: Anthropic (Claude Sonnet 4 — judge and one generator), OpenRouter (Qwen 2.5 72B), Google (Gemma 4 26B)
- Approximately \$150–200 USD Anthropic API budget for full three-model replication (RA-6) or \$50–80 for single-model pilot
- 4–8 hours wall-clock for single-model pilot; 3–5 days for three-model replication

### Setup

```bash
git clone https://github.com/frank-luongt/faos-research
cd faos-research/RA-6      # or RA-3
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Create .env in the parent project root with:
#   ANTHROPIC_API_KEY=sk-ant-...
#   OPENROUTER_API_KEY=...      (optional, for Qwen)
#   GOOGLE_API_KEY=...          (optional, for Gemma)
```

### Re-derive paper figures from included summary JSONs

```bash
cd RA-6/code
python generate_paper_figures.py     # reads ../results-summary/analysis_summary.json
python generate_crossmodel_figures.py
```

### Full experimental re-run (requires API access)

```bash
cd RA-6/code
python generate_scenarios.py --industry fintech --condition G4 --reps 3
python assess_coverage.py --industry fintech --condition G4
python detect_faults.py --industry fintech --condition G4
python analyze_results.py
```

---

## Citation

If you use this repository in academic work, please cite both the code release and the relevant paper(s).

### Repository

```bibtex
@misc{faos-research-repo,
  author       = {Luong, Thanh Tuan and Sanyal, Abhijit},
  title        = {{FAOS}~Research: Code, Data, and Ontologies for Ontology-Powered Enterprise Agent Verification},
  year         = {2026},
  howpublished = {\url{https://github.com/frank-luongt/faos-research}}
}
```

### Papers

See `CITATION.cff` and each paper's arXiv landing page for the canonical bibtex.

---

## Authors

- **Thanh Luong Tuan** (Golden Gate University · ORCID 0009-0000-1199-837X)
- **Dr. Abhijit Sanyal** (Novartis Healthcare Pvt. Ltd. · PhD Computer Science & Engineering, University of Calcutta)

---

## License

MIT. See [`LICENSE`](./LICENSE).

---

## Acknowledgements

We thank the FAOS team for platform access and ontology content used in the empirical evaluation. We also acknowledge the Anthropic, OpenRouter, and Google API platforms that made the three-model cross-validation study feasible.
