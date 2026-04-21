# RA-3 Cross-Model Validation Protocol

**Version**: 1.0
**Date**: 2026-04-01
**Purpose**: Replicate RA-3 experiment on local LLMs to establish model-independent claims

---

## 1. Motivation

The arXiv v1.2 paper (600 runs, Claude Sonnet 4) established:
- Three significant metrics (MA, RC, RS) with large effect sizes
- Inverse Parametric Knowledge Effect (Vietnamese 2x amplification)
- TF regression on well-known concepts

A peer reviewer will ask: *"Are these findings Claude-specific?"*

Cross-model validation answers this definitively. If the Inverse PKE and
ontology benefits replicate on a fundamentally different model architecture
(open-weight, smaller, different training data), the claims become
**model-independent** — a much stronger contribution.

## 2. Design

### 2.1 Models

| Role | Original (RA-3 v1.2) | Cross-Model Run |
|------|----------------------|-----------------|
| **Agent** | Claude Sonnet 4 (API) | Qwen 2.5 14B-Instruct (local, Q4_K_M) |
| **Judge** | Claude Sonnet 4 (API, t=0.0) | Claude Sonnet 4 (API, t=0.0) — **unchanged** |

**Rationale**:
- Agent model changes → tests if ontology effects are model-independent
- Judge stays the same → controls for measurement variance
- If both judge AND agent changed, we couldn't attribute differences

### 2.2 Conditions (identical to v1.2)

- **C1** — Ungrounded (system prompt only)
- **C2** — RAG-Only (8 curated chunks per industry)
- **C3** — Ontology-Coupled (L2, three-layer structured injection)
- **C4** — Ontology+Process (L3, C3 + quality judge gate)

Note: C4's quality judge remains Claude API — it's a process component, not the evaluated agent.

### 2.3 Task Set (identical)

50 tasks, 5 industries, 10/industry, same `tasks.json`.

### 2.4 Scale

50 tasks x 4 conditions x 3 reps = **600 runs** (identical to original)

### 2.5 Parameters

| Parameter | Claude Run | Qwen Run | Notes |
|-----------|-----------|----------|-------|
| Agent temperature | 0.3 | 0.3 | Same |
| Agent max_tokens | 1500 | 1500 | Same |
| Judge model | Claude Sonnet 4 | Claude Sonnet 4 | **Same judge** |
| Judge temperature | 0.0 | 0.0 | Same |
| Context budget | 2000 tokens | 2000 tokens | Same |

## 3. Hypotheses

### H1: Ontology effects replicate (primary)
The omnibus Friedman test will be significant (p < .05) for MA, RC, and RS
on Qwen, replicating the Claude finding.

### H2: Inverse PKE amplifies on weaker model
Vietnamese industries will show an even LARGER delta on Qwen than Claude,
because Qwen has less enterprise domain knowledge in its parametric weights
than Claude (especially for Vietnamese regulatory content).

Formally: Delta_Qwen(VN) > Delta_Claude(VN) > Delta_Claude(EN)

### H3: TF regression is model-specific
The TF regression on well-known concepts (IN-T1, IN-T2) may NOT replicate
on Qwen if Qwen has weaker insurance parametric knowledge — there's less
to displace.

### H4: C1 baseline is lower on Qwen
Qwen 14B has less parametric enterprise knowledge than Claude Sonnet 4.
C1 (ungrounded) means will be lower across all metrics, creating a larger
potential improvement range for ontological grounding.

## 4. Implementation

### 4.1 Code Changes

The experiment runner needs a **model backend abstraction** to swap between
Anthropic API and local Ollama/llama.cpp. Minimal changes:

```python
# config.py additions
AGENT_BACKEND = "ollama"  # "anthropic" | "ollama"
OLLAMA_MODEL = "qwen2.5:14b-instruct-q4_K_M"
OLLAMA_BASE_URL = "http://localhost:11434"

# Judge always uses Anthropic API regardless of agent backend
JUDGE_BACKEND = "anthropic"  # always
```

```python
# run_experiment.py — new function
def call_agent_ollama(task: dict, condition: str) -> str:
    """Call agent via Ollama API (OpenAI-compatible)."""
    import requests
    cfg = CONDITION_CONFIGS[condition]
    system_prompt = cfg["system_prompt_fn"](task)
    messages = cfg["messages_fn"](task)

    response = requests.post(
        f"{config.OLLAMA_BASE_URL}/api/chat",
        json={
            "model": config.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                *messages,
            ],
            "options": {
                "temperature": config.AGENT_TEMPERATURE,
                "num_predict": config.AGENT_MAX_TOKENS,
            },
            "stream": False,
        },
    )
    return response.json()["message"]["content"]
```

```python
# run_experiment.py — dispatch
def call_agent(client, task, condition):
    if config.AGENT_BACKEND == "ollama":
        return call_agent_ollama(task, condition)
    else:
        return call_agent_anthropic(client, task, condition)
```

### 4.2 Output Separation

Results are written to separate files to prevent mixing:

```
results/
  results_raw.csv              # Claude runs (existing)
  results_raw_qwen14b.csv      # Qwen runs (new)
  analysis_summary.json        # Claude analysis
  analysis_summary_qwen14b.json # Qwen analysis
  figures/                     # Claude figures
  figures_qwen14b/             # Qwen figures
```

### 4.3 Cross-Model Comparison Analysis

After both runs complete, a new analysis script compares:

```python
# analyze_crossmodel.py — new file
# 1. Load both CSVs
# 2. Friedman test per model per metric (already done individually)
# 3. Paired comparison: Delta_Claude vs Delta_Qwen per task
#    - Wilcoxon signed-rank on per-task deltas
# 4. Interaction test: Model x Condition (mixed ANOVA or ART)
# 5. Visualizations:
#    - Side-by-side radar (Claude vs Qwen)
#    - Delta comparison bar chart (per industry)
#    - Inverse PKE comparison (VN delta by model)
```

## 5. New Paper Sections

The cross-model results add approximately 2-3 pages:

### §8.4 Cross-Model Validation (new)

> To assess whether our findings are model-independent, we replicated
> the full experiment (600 runs, 4 conditions, 5 industries) using
> Qwen 2.5 14B-Instruct (Alibaba, 2024), a 14-billion-parameter
> open-weight model run locally via Ollama at Q4_K_M quantization.
> The judge model (Claude Sonnet 4, temperature 0.0) remained unchanged
> to control for measurement variance.
>
> [Table: Friedman results for Qwen]
> [Table: Side-by-side comparison Claude vs Qwen]
> [Figure: Dual radar chart]

### §9.3 Inverse PKE — Strengthened

> The Inverse PKE replicates across model architectures: ...
> Delta_Qwen(VN) = +.XX vs Delta_Claude(VN) = +.29 ...

### §9.6 Threats to Validity — Reduced

> Threat #3 (single-model) is now addressed through cross-model validation.

## 6. Execution Plan

### Prerequisites
```bash
# Install Ollama
brew install ollama

# Pull model (~9GB download)
ollama pull qwen2.5:14b-instruct-q4_K_M

# Verify
ollama run qwen2.5:14b-instruct-q4_K_M "What is a combined ratio in insurance?"
```

### Run
```bash
# Set backend
export RA3_AGENT_BACKEND=ollama

# Full experiment (~15-20 hours on M2 Pro)
python3 run_experiment.py

# Analyze
python3 analyze_results.py --output-suffix qwen14b

# Cross-model comparison
python3 analyze_crossmodel.py
```

### Timeline
| Day | Task | Hours |
|-----|------|-------|
| 1 | Implement backend abstraction, test on pilot (4 tasks) | 2h code + 30min run |
| 1-2 | Full Qwen experiment (600 runs) | 15-20h (overnight) |
| 3 | Analyze Qwen results + cross-model comparison | 2h |
| 3 | Layer ablation design (Phase B) | 2h |
| 4 | Write §8.4, update §9.3 and §9.6 | 3h |
| 5 | Self-review → arXiv v2 | 2h |

### Cost
- Agent (Qwen local): **$0**
- Judge (Claude API): ~$10-15 (2,400 judge calls at ~800 tokens each)
- **Total: ~$10-15** (vs $120-150 for all-Claude)

## 7. Success Criteria

| Criterion | Threshold | Implication |
|-----------|-----------|-------------|
| MA significant on Qwen | p < .05 | Core finding replicates |
| RS significant on Qwen | p < .05 | Role grounding is universal |
| VN Delta_Qwen > EN Delta_Qwen | Visible separation | Inverse PKE is model-independent |
| Cohen's d for model comparison | > 0.2 | Meaningful model difference exists |

If **H1 holds** (ontology effects replicate on Qwen): paper upgrades from
"we found X on Claude" to "X is a property of ontological grounding,
not a model artifact" — fundamentally stronger claim.

If **H1 fails**: still publishable — documents model-dependence of
neurosymbolic coupling, equally interesting and actionable.

## 8. Layer Ablation Extension (Phase B, optional)

If time permits after cross-model validation, add 3 ablation conditions:

- **C3-R**: Role layer only (no Domain, no Interaction)
- **C3-D**: Domain layer only (no Role, no Interaction)
- **C3-I**: Interaction layer only (no Role, no Domain)

3 conditions x 50 tasks x 3 reps = 450 runs (on Qwen, ~10-15h)

Expected findings:
- C3-R drives RS improvement
- C3-D drives TF + MA improvement
- C3-I drives RC improvement
- Full C3 > any single layer (synergy effect)

This directly answers "which ontology layer matters most?" — a question
every reviewer will ask.
