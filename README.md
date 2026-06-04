# FAOS Research Programme — Research, in the open.

**Source LaTeX, raw model outputs, judge logs, evaluation scripts, and frozen-version DOIs for every accepted paper in the Foundation AgenticOS research portfolio.**

The FAOS Research Programme is the empirical research arm of the [Foundation AgenticOS](https://www.faosx.ai) platform. We study how ontology-grounded, neurosymbolic, and context-engineered agent systems behave under the conditions enterprises actually face — regulated industries, multi-agent coordination, verification under uncertainty. The programme is run by Thanh Luong Tuan and a rotating bench of co-authors and chairs, with empirical work executed against the live FAOS platform across 22+ industry modules. We run our lab in the open: every accepted paper ships with reproduction artifacts under MIT licence.

---

## Papers

| Paper | Title | Status | ETA |
|---|---|---|---|
| **RA-1** | Multi-Agent Coordination | [`arXiv-live`](https://arxiv.org/abs/2606.00804) · [`./RA-1/`](./RA-1/) | Published |
| **RA-3** | Neurosymbolic Enterprise AI | [`arXiv-live`](https://arxiv.org/abs/2604.00555) · [`./RA-3/`](./RA-3/) | Published |
| **RA-4** | Empirical Bounds of Ontological Context | [`arXiv-ready — minor pre-submit revision`](./RA-4/) | Q2 2026 |
| **RA-6** | Agent Simulation & Verification | [`arXiv-live`](https://arxiv.org/abs/2606.04037) · [`./RA-6/`](./RA-6/) | Published |
| **RA-11** | Quantum Context Engineering | `gated — Q3 2026` | Q3 2026 |
| **RA-12** | Entropy-Guided Ontology Design | [`preprint pending — arXiv submission imminent`](./RA-12/) | Q2 2026 |
| **RA-15** | Contextuality Auditor | `method paper — Q2 2026` | Q2 2026 |

Status legend: `arXiv-live` = posted to arXiv; paper PDF mirrored in this repo alongside reproduction code/data · `preprint pending — arXiv submission imminent` = paper artifacts (PDF/LaTeX/bib) will be added to this repo once the canonical version is posted to arXiv; reproduction scaffolding (code/ontologies/checklists/results-summary/citation-audit) available now · `arXiv-ready — minor pre-submit revision` = source package is prepared and peer-review simulation is complete, but PDF/LaTeX remain private until the canonical arXiv version is posted · `method paper` = methods contribution under reframe, embargo placeholder · `gated` = clearing publication gates (co-author sign-off, bib-verification, chair review), embargo placeholder.

**Programme policy (2026-05-17):** Paper PDFs, LaTeX source, bibliographies, and arXiv submission tarballs are mirrored to this repository ONLY after the canonical version is live on arXiv or accepted by a journal. The repository's purpose is reproducibility scaffolding; pre-arXiv distribution short-circuits the canonical-version-on-arXiv discipline.

---

## Programme-level reproducibility commitment (v0.2 promise)

For every accepted paper, we publish:

- **Source LaTeX** — `main.tex`, bibliography, figure scripts
- **Raw model outputs** — full scenario corpora and generated transcripts (post-acceptance)
- **Judge logs** — LLM-as-judge evaluation traces where applicable, at $T = 0.0$
- **Evaluation scripts** — `run_experiment.py`, `analyze_results.py`, `analyze_crossmodel.py`, figure generation
- **A frozen-version DOI on Zenodo** — citable long-term preservation snapshot per release

This is the programme-level reproducibility commitment. It replaces the v0.1 per-paper staged-release policy with a single uniform contract.

---

## What is NOT in this repository

The FAOS dissertation manuscript and topic proposal are not public research artifacts and will not appear in this repository. The empirical papers above are independent research outputs that may share co-authors with dissertation work but are scoped, written, and released as standalone contributions.

---

## Repository layout

```text
faos-research/
├── README.md                    ← this file
├── LICENSE                      ← MIT
├── CITATION.cff                 ← structured citation metadata
├── .gitignore
├── docs/
│   └── reproducibility.md       ← cross-paper reproduction notes
├── RA-1/                        ← embargo placeholder
│   └── README.md
├── RA-3/                        ← arXiv-live; code + ontologies + summaries
│   ├── CROSS-MODEL-PROTOCOL.md
│   ├── requirements.txt
│   ├── code/
│   ├── ontology_context/
│   └── results-summary/
├── RA-4/                        ← arXiv-ready status page; paper PDF + LaTeX added at arXiv post
│   └── README.md
├── RA-6/                        ← preprint pending arXiv; reproducibility scaffolding (code + ontologies + checklists + faults + summaries + citation audit) — paper PDF + LaTeX added at arXiv post
│   ├── README.md
│   ├── bib-verified-2026-05-17.md
│   ├── CROSS-MODEL-PROTOCOL.md
│   ├── requirements.txt
│   ├── code/
│   ├── ontology_context/
│   ├── regulatory_checklists/
│   ├── fault_definitions/
│   └── results-summary/
├── RA-11/                       ← embargo placeholder
│   └── README.md
├── RA-12/                       ← preprint pending arXiv; citation audit only — full reproducibility scaffolding + paper PDF + LaTeX added at arXiv post
│   ├── README.md
│   └── bib-verified-2026-05-17.md
└── RA-15/                       ← embargo placeholder
    └── README.md
```

Embargo placeholder directories (RA-1, RA-11, RA-15) contain only a `README.md` with the paper's working title, authors, status badge, ETA, and research-question teaser. RA-4 has advanced to an arXiv-ready status page, but its paper PDF / LaTeX source still follows the same canonical-version policy and will be added only after arXiv posting. Preprint-pending directories (RA-6, RA-12) contain reproducibility scaffolding and a citation audit but **not** the paper PDF / LaTeX source — those are added once the paper is posted to arXiv. The arXiv-live directory (RA-3) ships reproduction code + ontologies + summaries; the canonical paper PDF lives on arXiv at https://arxiv.org/abs/2604.00555.

---

## Reproduction (live papers)

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
  title        = {{FAOS}~Research Programme: Source, Data, and Ontologies for Ontology-Powered Enterprise Agent Verification},
  year         = {2026},
  howpublished = {\url{https://github.com/frank-luongt/faos-research}}
}
```

### Papers

See `CITATION.cff` and each paper's arXiv / preprint landing page for the canonical BibTeX entries.

---

## Authors

- **Thanh Luong Tuan** (Golden Gate University · ORCID 0009-0000-1199-837X) — programme lead
- **Dr. Abhijit Sanyal** (Novartis Healthcare Pvt. Ltd. · PhD Computer Science & Engineering, University of Calcutta) — co-author on RA-3, RA-6, RA-12
- Additional co-authors per paper — see each paper directory's `README.md`

---

## License

MIT. See [`LICENSE`](./LICENSE).

---

## Acknowledgements

We thank the FAOS team for platform access and ontology content used in the empirical evaluation. We also acknowledge the Anthropic, OpenRouter, and Google API platforms that made multi-model cross-validation studies feasible.
