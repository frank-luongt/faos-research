# RA-6 — Toward Pre-Deployment Assurance for Enterprise AI Agents: Ontology-Grounded Simulation and Trust Certification

**Authors:** Thanh Luong Tuan, Abhijit Sanyal
**Status:** arXiv-live (posted 2026-06) — [arXiv:2606.04037](https://arxiv.org/abs/2606.04037)
**Last revised:** 2026-05-17 (reproducibility scaffolding)
**Related:** Builds on the neurosymbolic ontology architecture of RA-3 ([`../RA-3/`](../RA-3/), [arXiv:2604.00555](https://arxiv.org/abs/2604.00555)).

## Current interpretation (27 October 2026)

This directory preserves the historical RA-6 reproduction bundle and its June 2026 preprint. The later [REGATTA preprint, arXiv:2610.30924](https://arxiv.org/abs/2610.30924), shares the experimental corpus and two-stage approach and adds a source audit and measurement diagnostics. Its public record reports acceptance at 2026 IEEE ICoDSE; this is a separate paper, not an acceptance claim for RA-6.

REGATTA identifies defects in the checklist and fault instruments and requires correction before they are used as legal ground truth. Historical coverage and fault-detection measurements concern the instruments as written; they do not establish legal compliance, a validated deployment verdict, or production readiness. The earlier framing of all 125 items as verified primary-source requirements should therefore not be relied upon.

The historical result files, checklist texts, fault definitions, code, and citation audit are retained unchanged for provenance. The bibliography audit below is not a legal-source validation of the checklist. Use [REGATTA's archived release](https://doi.org/10.5281/zenodo.23006005) for the later audit and reusable instruments.

## Paper

The canonical paper is published on arXiv at **[arXiv:2606.04037](https://arxiv.org/abs/2606.04037)**. Following the same convention as [`../RA-3/`](../RA-3/), this directory hosts the reproduction code, ontologies, regulatory checklists, fault definitions, and aggregated results; the canonical paper PDF and LaTeX source live on arXiv.

## Contents (reproducibility scaffolding)

- `bib-verified-2026-05-17.md` — WebSearch-verified citation audit (55 entries verified clean, 0 fabrications) per FAOS Research Programme reproducibility commitment
- `code/` — experimental scripts (`generate_scenarios.py`, `assess_coverage.py`, `detect_faults.py`, `analyze_results.py`, `analyze_crossmodel.py`)
- `ontology_context/` — ontology fragments used at $T = 0.0$ generation
- `regulatory_checklists/` — 125 historical source-cited checklist items; see the source-audit caveat above
- `fault_definitions/` — 25 injected fault scenarios
- `results-summary/` — aggregated analysis JSONs across three generator models
- `CROSS-MODEL-PROTOCOL.md` — cross-model replication protocol
- `requirements.txt` — Python dependencies

## Citation

Please cite the arXiv preprint for the paper, and the repository if you use the code/data:

```bibtex
@misc{luong2026predeployment,
  author        = {Luong Tuan, Thanh and Sanyal, Abhijit},
  title         = {Toward Pre-Deployment Assurance for Enterprise {AI} Agents: Ontology-Grounded Simulation and Trust Certification},
  year          = {2026},
  eprint        = {2606.04037},
  archivePrefix = {arXiv},
  primaryClass  = {cs.AI}
}

@misc{faos-research-repo,
  author       = {Luong, Thanh Tuan and Sanyal, Abhijit},
  title        = {{FAOS}~Research Programme: Source, Data, and Ontologies for Ontology-Powered Enterprise Agent Verification},
  year         = {2026},
  howpublished = {\url{https://github.com/frank-luongt/faos-research}}
}
```

## License

Code, ontologies, regulatory checklists, fault definitions, and aggregated results released under the MIT licence (see repository root [`LICENSE`](../LICENSE)).
