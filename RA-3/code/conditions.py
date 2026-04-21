"""Condition implementations for RA-3 pilot study.

C1: Ungrounded — bare system prompt, no domain context
C2: RAG-Only — retrieved text chunks (unstructured)
C3: Ontology-Coupled (L2) — structured ontology injection (Role + Domain + Interaction)
C4: Ontology+Process (L3) — C3 plus post-generation quality judge
"""

import json
from pathlib import Path

ONTOLOGY_DIR = Path(__file__).parent / "ontology_context"


def _load_ontology(industry: str) -> dict:
    """Load industry ontology context file."""
    fp = ONTOLOGY_DIR / f"{industry}.json"
    with open(fp) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# C1: Ungrounded
# ---------------------------------------------------------------------------

def build_c1_messages(task: dict) -> list[dict]:
    """Bare system prompt, no domain context."""
    return [
        {"role": "user", "content": task["question"]},
    ]


def c1_system_prompt(_task: dict) -> str:
    return "You are an AI assistant. Answer the user's question."


# ---------------------------------------------------------------------------
# C2: RAG-Only
# ---------------------------------------------------------------------------

def build_c2_messages(task: dict) -> list[dict]:
    """Inject raw text chunks as context (simulating RAG retrieval)."""
    onto = _load_ontology(task["industry"])
    chunks = onto.get("rag_chunks", [])
    # Select most relevant chunks (simple: use all, truncated to budget)
    context_text = "\n\n".join(chunks)
    # Truncate to roughly 2000 tokens (~8000 chars)
    if len(context_text) > 8000:
        context_text = context_text[:8000] + "\n[...truncated]"
    return [
        {"role": "user", "content": task["question"]},
    ]


def c2_system_prompt(task: dict) -> str:
    onto = _load_ontology(task["industry"])
    chunks = onto.get("rag_chunks", [])
    context_text = "\n\n".join(chunks)
    if len(context_text) > 8000:
        context_text = context_text[:8000] + "\n[...truncated]"
    return (
        "You are an AI assistant. Use the following reference documents to "
        "answer the user's question.\n\n"
        f"REFERENCE DOCUMENTS:\n{context_text}"
    )


# ---------------------------------------------------------------------------
# C3: Ontology-Coupled (L2) — Structured injection
# ---------------------------------------------------------------------------

def _build_role_section(onto: dict, task: dict) -> str:
    """Build structured Role section from ontology."""
    role_layer = onto.get("role_layer", {})
    # Pick the most relevant role based on task
    gt = task.get("ground_truth", {})
    role_key = _infer_role_key(gt, role_layer)
    if not role_key or role_key not in role_layer:
        # Fallback: serialize first two roles
        lines = ["## Role Layer"]
        for k, v in list(role_layer.items())[:2]:
            lines.append(f"### {v.get('title', k)}")
            if "kpis" in v:
                lines.append(f"KPIs: {json.dumps(v['kpis'])}")
            if "vocabulary" in v:
                lines.append(f"Vocabulary: {', '.join(v['vocabulary'][:10])}")
        return "\n".join(lines)

    role = role_layer[role_key]
    lines = [
        f"## Role: {role.get('title', role_key)}",
        f"Persona: {role.get('persona', '')}",
        f"Communication Style: {role.get('communication_style', '')}",
    ]
    if "kpis" in role:
        lines.append(f"KPIs: {json.dumps(role['kpis'])}")
    if "decision_patterns" in role:
        lines.append(f"Decision Patterns: {json.dumps(role['decision_patterns'])}")
    if "vocabulary" in role:
        lines.append(f"Vocabulary: {', '.join(role['vocabulary'])}")
    if "domain_knowledge" in role:
        lines.append(f"Domain Knowledge: {json.dumps(role['domain_knowledge'])}")
    return "\n".join(lines)


def _build_domain_section(onto: dict, task: dict) -> str:
    """Build structured Domain section from ontology."""
    domain = onto.get("domain_layer", {})
    concepts = domain.get("concepts", {})
    regulations = domain.get("regulations", {})

    lines = ["## Domain Layer"]

    # Concepts
    if concepts:
        lines.append("### Concepts")
        for name, info in concepts.items():
            defn = info.get("definition", "")
            lines.append(f"- **{name}**: {defn}")
            for field in ("healthy_range", "world_class", "target"):
                if field in info:
                    lines.append(f"  {field}: {info[field]}")

    # Regulations (if RC task)
    if regulations and task.get("metric_tested") in ("RC", "ALL"):
        lines.append("### Regulations")
        for name, info in regulations.items():
            if isinstance(info, dict):
                lines.append(f"- **{name}**: {json.dumps(info)}")
            else:
                lines.append(f"- **{name}**: {info}")

    return "\n".join(lines)


def _build_interaction_section(onto: dict) -> str:
    """Build structured Interaction section from ontology."""
    interaction = onto.get("interaction_layer", {})
    handoffs = interaction.get("handoffs", {})
    if not handoffs:
        return ""
    lines = ["## Interaction Layer (Handoffs)"]
    for name, info in handoffs.items():
        lines.append(f"- **{name}**: {json.dumps(info)}")
    return "\n".join(lines)


def _infer_role_key(gt: dict, role_layer: dict) -> str | None:
    """Infer the relevant role key from ground truth."""
    role_name = gt.get("role", "").lower()
    for key in role_layer:
        if key.replace("_", " ") in role_name or role_name in key.replace("_", " "):
            return key
    # Heuristic matches
    mapping = {
        "bsa": "bsa_officer",
        "head of payments": "head_of_payments",
        "chief actuary": "chief_actuary",
        "chief risk": "chief_risk_officer",
        "chief medical": "chief_medical_officer",
        "cmo": "chief_medical_officer",
        "chief nursing": "chief_nursing_officer",
        "cno": "chief_nursing_officer",
    }
    for pattern, key in mapping.items():
        if pattern in role_name:
            return key
    return None


def build_c3_messages(task: dict) -> list[dict]:
    return [{"role": "user", "content": task["question"]}]


def c3_system_prompt(task: dict) -> str:
    onto = _load_ontology(task["industry"])
    role_section = _build_role_section(onto, task)
    domain_section = _build_domain_section(onto, task)
    interaction_section = _build_interaction_section(onto)

    context = f"{role_section}\n\n{domain_section}\n\n{interaction_section}"
    # Truncate to budget (~8000 chars ≈ 2000 tokens)
    if len(context) > 8000:
        context = context[:8000] + "\n[...truncated]"

    return (
        "You are an AI assistant with structured enterprise domain knowledge.\n\n"
        "ONTOLOGY CONTEXT (Role + Domain + Interaction layers):\n"
        f"{context}"
    )


# ---------------------------------------------------------------------------
# C4: Ontology+Process (L3) — C3 + quality judge gate
# ---------------------------------------------------------------------------

C4_JUDGE_PROMPT = """You are a quality judge evaluating an enterprise AI agent's response.

TASK: {question}
RESPONSE: {response}

Score the response quality on a 0.0-1.0 scale across:
1. Domain accuracy
2. Regulatory correctness
3. Role appropriateness
4. Completeness

Respond with JSON: {{"quality_score": float, "pass": bool, "issues": [str]}}
A score >= 0.7 passes. Below 0.7 would be flagged for escalation."""


def build_c4_messages(task: dict) -> list[dict]:
    return build_c3_messages(task)


def c4_system_prompt(task: dict) -> str:
    return c3_system_prompt(task)


def build_c4_judge_prompt(task: dict, response: str) -> str:
    return C4_JUDGE_PROMPT.format(question=task["question"], response=response)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

CONDITION_CONFIGS = {
    "C1_ungrounded": {
        "system_prompt_fn": c1_system_prompt,
        "messages_fn": build_c1_messages,
        "label": "Ungrounded (L0)",
    },
    "C2_rag": {
        "system_prompt_fn": c2_system_prompt,
        "messages_fn": build_c2_messages,
        "label": "RAG-Only",
    },
    "C3_ontology": {
        "system_prompt_fn": c3_system_prompt,
        "messages_fn": build_c3_messages,
        "label": "Ontology-Coupled (L2)",
    },
    "C4_ontology_process": {
        "system_prompt_fn": c4_system_prompt,
        "messages_fn": build_c4_messages,
        "label": "Ontology+Process (L3)",
        "post_judge_fn": build_c4_judge_prompt,
    },
}
