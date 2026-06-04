# RA-6 — Toward Pre-Deployment Assurance for Enterprise AI Agents: Ontology-Grounded Simulation and Trust Certification

**Authors:** Thanh Luong Tuan, Abhijit Sanyal
**Status:** arXiv-live (posted 2026-06) — [arXiv:2606.04037](https://arxiv.org/abs/2606.04037)
**Last revised:** 2026-05-17 (reproducibility scaffolding)
**Related:** Builds on the neurosymbolic ontology architecture of RA-3 ([`../RA-3/`](../RA-3/), [arXiv:2604.00555](https://arxiv.org/abs/2604.00555)).

Pre-deployment verification of enterprise AI agents remains a critical gap between large language model capability benchmarking and production deployment, where post-deployment monitoring, human-in-the-loop controls, and prompt-level guardrails provide limited assurance. This paper proposes an ontology-grounded verification framework combining an Agent Operational Envelope, an ontology-to-scenario generation pipeline, and a Trust Certificate carrying a machine-verifiable attestation with graduated deployment verdicts. A controlled pilot across four regulated industries — Fintech, Banking, Insurance, and Healthcare — instantiated as five industry-by-regulatory-regime cells across the United States and Vietnam generated 1,800 scenarios evaluated against 125 primary-source regulatory requirements and 25 injected faults. Ontology-grounded generation (G4) achieved 48.3% regulatory coverage versus 33.1% for the persona-based baseline ($p_c = 0.0006$) and the highest domain specificity (4.77/5.0, $p = 2 \times 10^{-6}$); cross-validation across three LLM families (Claude Sonnet 4, Qwen 2.5 72B, Gemma 4 26B; 5,400 total scenarios) replicated the persona-versus-ontology pattern. The results establish ontology-grounded scenario generation as a credible complement to persona-based test suites for regulatory-intensive domains.

## Paper

The canonical paper is published on arXiv at **[arXiv:2606.04037](https://arxiv.org/abs/2606.04037)**. Following the same convention as [`../RA-3/`](../RA-3/), this directory hosts the reproduction code, ontologies, regulatory checklists, fault definitions, and aggregated results; the canonical paper PDF and LaTeX source live on arXiv.

## Contents (reproducibility scaffolding)

- `bib-verified-2026-05-17.md` — WebSearch-verified citation audit (55 entries verified clean, 0 fabrications) per FAOS Research Programme reproducibility commitment
- `code/` — experimental scripts (`generate_scenarios.py`, `assess_coverage.py`, `detect_faults.py`, `analyze_results.py`, `analyze_crossmodel.py`)
- `ontology_context/` — ontology fragments used at $T = 0.0$ generation
- `regulatory_checklists/` — 125 primary-source regulatory requirements
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
