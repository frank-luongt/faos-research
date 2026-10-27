# FAOS Research Programme — Research, in the open.

**Public research artifacts and links to canonical preprints from the Foundation AgenticOS research portfolio. Artifact availability is recorded per paper; an arXiv posting does not imply peer-reviewed acceptance.**

The FAOS Research Programme studies structured domain knowledge, evaluation methods, and coordination mechanisms for enterprise AI. Its public outputs include empirical studies, negative results, and measurement tools. The programme is led by Thanh Luong Tuan, with co-authors listed per paper. The release commitment below describes intended reproducibility materials; availability and limitations are recorded per artifact.
---

## Papers

Public record checked **27 October 2026**. This index separates preprints, venue acceptance, released artifacts, and research still awaiting public release.

| Paper | Title | Public paper status | Available materials |
|---|---|---|---|
| **REGATTA** | Cross-Domain Measurement and Fault-Injection Harness | [arXiv:2610.30924](https://arxiv.org/abs/2610.30924), posted 22 October; arXiv record reports acceptance at 2026 IEEE ICoDSE | [Artifact DOI](https://doi.org/10.5281/zenodo.23006005) · [release guide](./REGATTA/) |
| **RA-1** | Multi-Agent Coordination | [arXiv:2606.00804](https://arxiv.org/abs/2606.00804) preprint | [RA-1](./RA-1/) |
| **RA-3** | Neurosymbolic Enterprise AI | [arXiv:2604.00555](https://arxiv.org/abs/2604.00555) preprint | [RA-3](./RA-3/) |
| **RA-4** | Empirical Bounds of Ontological Context | Canonical public preprint pending; no current release date asserted | [Status page](./RA-4/) |
| **RA-6** | Agent Simulation & Verification | [arXiv:2606.04037](https://arxiv.org/abs/2606.04037) historical preprint; see the later REGATTA source audit | [Historical reproduction bundle and caveat](./RA-6/) |
| **RA-11** | Quantum Context Engineering | Research in progress; no current release date asserted | [Status page](./RA-11/) |
| **RA-12** | Entropy-Guided Ontology Design | Canonical public preprint pending; no current release date asserted | [Status and citation audit](./RA-12/) |
| **RA-15 / RA-17** | Ontology-Amplified Distillation and Contextuality Auditing | [Combined preprint, arXiv:2607.11948](https://arxiv.org/abs/2607.11948), posted 11 July | [RA-15 contextuality artifacts](./RA-15/) · [artifact DOI](https://doi.org/10.5281/zenodo.21288508); this bundle is not a complete distillation/model release |

**Interpretation:** REGATTA audits instruments shared with the historical RA-6 corpus. Those instruments need correction before legal use; the historical measurements do not establish compliance or deployment readiness. See [the dated public-record notes](./docs/public-record-2026-10-27.md). The combined RA-15/RA-17 article reports a contextuality null and a bounded distillation pilot, without establishing superiority, statistical equivalence, safety, or deployability.

**Status legend:** `preprint` means publicly posted on arXiv; it does not establish journal acceptance. `accepted` is used only where the linked public record states venue acceptance. `artifacts public` describes a specific released bundle. `pending` and `research in progress` carry no promised publication date. No presentation or proceedings-publication claim is made here.

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
├── REGATTA/                     ← canonical paper + archived artifact links
│   └── README.md
├── RA-1/                        ← public reproduction artifacts
│   └── README.md
├── RA-3/                        ← arXiv-live; code + ontologies + summaries
│   ├── CROSS-MODEL-PROTOCOL.md
│   ├── requirements.txt
│   ├── code/
│   ├── ontology_context/
│   └── results-summary/
├── RA-4/                        ← status page; canonical public preprint pending
│   └── README.md
├── RA-6/                        ← arXiv-live (arXiv:2606.04037); reproducibility scaffolding (code + ontologies + checklists + faults + summaries + citation audit); canonical PDF/LaTeX on arXiv
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
├── RA-12/                       ← status page + citation audit; canonical public preprint pending
│   ├── README.md
│   └── bib-verified-2026-05-17.md
└── RA-15/                       ← contextuality artifacts v1.1; combined RA-15/RA-17 preprint linked
    ├── README.md
    ├── ARTIFACT-MANIFEST-v1.1.md
    └── experiment/              ← synthetic inputs, outputs, summaries, code, protocols, reports
```

Status-only directories do not constitute paper or result releases. RA-15 contains a synthetic contextuality-audit bundle; its canonical paper is now part of the combined RA-15/RA-17 preprint. RA-1, RA-3, and RA-6 contain public reproduction materials; consult their directories for the available scope. Canonical paper PDFs and source remain available through the linked arXiv records. REGATTA's later audit and release are linked separately, without changing the historical RA-6 corpus.

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
