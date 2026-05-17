# RA-12 — Entropy-Guided Ontology Design for Enterprise Agentic Systems: A Structural Entropy Analysis of 23 Industry Verticals

**Authors:** Thanh Luong Tuan, Abhijit Sanyal
**Status:** Preprint
**Last revised:** 2026-05-17

Enterprise ontologies are typically designed by domain experts through iterative consultation, producing ontologies of widely varying size, depth, and connectivity without a principled a-priori metric for predicting their downstream utility. This paper extends prior $n = 5$ pilot work to the full Foundation AgenticOS corpus of 23 industry ontologies. Using a layer-wise decomposition $SE_{\text{comp}} = f(SE_{\text{role}}, SE_{\text{dom}}, SE_{\text{int}})$ appropriate to the FAOS three-layer role/domain/interaction schema, and combining cross-model grounding lift data from three generator models (Claude Sonnet 4, Qwen 2.5 72B, Gemma 4 26B; $n = 15$ industry-model cells), the analysis establishes a robust structural-entropy-versus-lift relationship: interaction-layer SE alone predicts overall lift at Spearman $r = 0.811$, $p = 0.0002$; a leave-one-industry-out cross-validation yields pooled Spearman $r = 0.786$, $p = 0.0005$, RMSE $= 0.060$, with calibration slope $0.81$. From this calibration the paper codifies four ontology design principles — a target SE band, a layer-priority ordering, a regulatory-density floor, and a cross-vertical transfer warning — and applies the fitted formula to the remaining 18 non-pilot FAOS production ontologies, identifying software, systems integration, security, and travel/tourism as high-priority targets for future experimental validation. The paper provides the first at-scale empirical analysis of enterprise ontology structural entropy and its quantitative relationship to LLM agent performance, establishing structural entropy as a design-time predictor of ontology value and a reproducible methodology for ontology-quality review.

## Contents

- `main.tex` — source LaTeX
- `main.pdf` — compiled preprint PDF (21 pages)
- `references.bib` — bibliography
- `bib-verified-2026-05-17.md` — WebSearch-verified citation audit per FAOS Research Programme reproducibility commitment
- `figures/` — figure PDFs referenced from `main.tex` (SE-vs-lift scatter, layer/metric heatmap, production-SE distribution, calibration plot, production ranking)

## Citation

```bibtex
@misc{luong2026ra12,
  author       = {Luong, Thanh Tuan and Sanyal, Abhijit},
  title        = {Entropy-Guided Ontology Design for Enterprise Agentic Systems: A Structural Entropy Analysis of 23 Industry Verticals},
  year         = {2026},
  howpublished = {Preprint},
  url          = {https://github.com/frank-luongt/faos-research/tree/main/RA-12}
}
```

## License

This preprint and its accompanying source LaTeX, figures, and bibliography are released under the MIT licence (see repository root [`LICENSE`](../LICENSE)).
