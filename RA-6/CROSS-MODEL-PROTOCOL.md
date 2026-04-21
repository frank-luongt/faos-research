# RA-6 Cross-Model Validation Protocol v1.0

**Date**: 2026-04-04
**Study**: RA-6 — Agent Simulation, Testing & Formal Verification
**Purpose**: Replicate the RA-6 pilot with two additional generator models to confirm that ontology-powered scenario generation advantages generalize beyond Claude.

## Design

### Models

| Role | Model | Backend | Suffix |
|------|-------|---------|--------|
| Generator (baseline) | Claude Sonnet 4 | Anthropic API | _(none)_ |
| Generator (replication 1) | Qwen 2.5 72B Instruct | OpenRouter | `qwen_2_5_72b` |
| Generator (replication 2) | Gemma 4 27B IT | Google AI Studio | `gemma_4_27b_it` |
| Judge (fixed) | Claude Sonnet 4 | Anthropic API | _(always)_ |
| Faulty Agent (fixed) | Claude Sonnet 4 | Anthropic API | _(always)_ |

**Rationale**: Same 3-model matrix as RA-3 cross-model validation for dissertation consistency. Judge remains fixed on Claude to control measurement variance — only the generator is swapped.

### Experiment Parameters

- **Conditions**: G1 (baseline), G2 (persona), G3 (RAG), G4 (ontology)
- **Industries**: fintech, insurance, healthcare, banking_vn, insurance_vn
- **Repetitions**: 3
- **Scenarios per suite**: 30
- **Total per model**: 4 × 5 × 3 = 60 suites = 1,800 scenarios
- **Total new runs**: 2 models × 60 suites = 120 suites, 3,600 scenarios
- **Judge calls per model**: ~5,000 (RC + ISS + AC + FDR-design + FDR-exec)

### Hypotheses

| # | Hypothesis | Test |
|---|-----------|------|
| H5 | RC advantage (G4 > G2) replicates across models | G4 RC mean > G2 RC mean for all 3 models |
| H6 | ISS advantage (G4 > all) replicates across models | G4 ISS mean > G1 ISS mean for all 3 models |
| H7 | Coverage-precision tradeoff persists | G4 FDR gap (design - exec) > 5pp for all 3 models |
| H8 | Weaker models show larger G4 advantage | RC delta (G4-G2) inversely correlated with baseline quality |

## Execution

### Phase 1: Qwen 2.5 72B via OpenRouter

```bash
export RA6_GENERATOR_BACKEND=openrouter
export OPENROUTER_API_KEY=<your-key>
# Optional: export RA6_OPENROUTER_MODEL=qwen/qwen-2.5-72b-instruct

# Generate scenarios
python3 run_experiment.py --phase generate

# Assess coverage (judge = Claude, always)
python3 run_experiment.py --phase assess

# Fault detection
python3 run_experiment.py --phase fdr

# Analysis
python3 run_experiment.py --phase analyze
```

Output files: `generated_scenarios_qwen_2_5_72b.json`, `coverage_results_qwen_2_5_72b.json`, etc.

### Phase 2: Gemma 4 27B via Google AI Studio

```bash
export RA6_GENERATOR_BACKEND=google
export GOOGLE_API_KEY=<your-key>
# Optional: export RA6_GOOGLE_MODEL=gemma-4-27b-it

python3 run_experiment.py  # Full pipeline
```

Output files: `generated_scenarios_gemma_4_27b_it.json`, etc.

### Phase 3: Cross-Model Comparison

```bash
python3 analyze_crossmodel.py --models ,qwen_2_5_72b,gemma_4_27b_it
```

Produces:
- `results/crossmodel/crossmodel_radar.pdf`
- `results/crossmodel/crossmodel_comparison.pdf`
- `results/crossmodel/crossmodel_summary.json`

## Cost Estimate

| Model | Generation | Judge (assess) | Judge (FDR) | Total |
|-------|-----------|---------------|-------------|-------|
| Qwen 2.5 72B | ~$5-8 (OpenRouter) | ~$15-20 (Claude) | ~$10-15 (Claude) | ~$30-45 |
| Gemma 4 27B | Free tier / ~$2-5 | ~$15-20 (Claude) | ~$10-15 (Claude) | ~$27-40 |
| **Total** | | | | **~$57-85** |

## Timeline

| Step | Duration | Notes |
|------|----------|-------|
| Qwen generation (60 suites) | ~4-6h | API rate limits |
| Qwen assessment + FDR | ~20-30h | Claude judge calls |
| Gemma generation (60 suites) | ~4-6h | Google AI Studio |
| Gemma assessment + FDR | ~20-30h | Claude judge calls |
| Cross-model analysis | <1h | Local computation |
| Paper update (§8.5) | ~2h | New subsection + figures |

## Paper Sections to Update

1. **§8.5 Cross-Model Validation** (new subsection in Results)
2. **§11 Threats to Validity** — address "single LLM family" concern (line ~1870)
3. **§12 Conclusion** — update with 3-model generalizability claim
4. **Abstract** — add cross-model replication count

## Anti-Circularity

The same E1 holdout partition (30%) is applied regardless of generator model. The ontology content available to G4 is identical across Claude, Qwen, and Gemma — ensuring fair comparison of how each model *utilizes* structured ontology context, not differences in available content.
