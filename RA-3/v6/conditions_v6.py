"""v6 prompts. C1 and C3 reuse v5's builders unchanged; C2b is RAG matched to C3's budget.

v5's C2 carried ~2,000 tokens against C3's larger context, so the C2-C3
comparison was not budget-matched. C2b fills the same character budget as the
task's C3 context from the cell's ``rag_chunks``, in file order, and records any
shortfall so an under-filled cell is visible rather than silent.
"""

import importlib.util
from pathlib import Path

import design

_spec = importlib.util.spec_from_file_location(
    "ra3_v5_conditions", design.RA3_DIR / "code" / "conditions.py"
)
v5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v5)
v5.ONTOLOGY_DIR = Path(design.ONTOLOGY_DIR)  # shipped ontologies live one level up

RAG_HEADER = (
    "You are an AI assistant. Use the following reference documents to "
    "answer the user's question.\n\nREFERENCE DOCUMENTS:\n"
)


def _v5_task(task: dict) -> dict:
    """v5 builders look up the ontology by ``industry``; point it at the cell's file."""
    return {**task, "industry": design.ontology_stem(task["cell"])}


def c2b_system_prompt(task: dict) -> tuple[str, dict]:
    t = _v5_task(task)
    budget = len(v5.c3_system_prompt(t)) - len(RAG_HEADER)
    chunks = v5._load_ontology(t["industry"]).get("rag_chunks", [])
    picked, used = [], 0
    for chunk in chunks:
        sep = 2 if picked else 0
        if used + sep + len(chunk) > budget:
            room = budget - used - sep
            if room > 200:  # keep a meaningful partial chunk, cut at a word
                picked.append(chunk[:room].rsplit(" ", 1)[0])
                used += sep + len(picked[-1])
            break
        picked.append(chunk)
        used += sep + len(chunk)
    meta = {"budget_chars": budget, "context_chars": used, "shortfall_chars": max(0, budget - used)}
    return RAG_HEADER + "\n\n".join(picked), meta


def build_prompt(task: dict, condition: str) -> tuple[list[dict], dict]:
    """Return (messages, meta) for one task and condition."""
    t = _v5_task(task)
    meta = {}
    if condition == "C1_ungrounded":
        system = v5.c1_system_prompt(t)
    elif condition == "C3_ontology":
        system = v5.c3_system_prompt(t)
    elif condition == "C2b_rag_matched":
        system, meta = c2b_system_prompt(task)
    else:
        raise ValueError(f"unknown condition {condition}")
    meta["system_chars"] = len(system)
    return [{"role": "system", "content": system}, {"role": "user", "content": task["question"]}], meta
