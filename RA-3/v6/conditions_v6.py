"""v6 prompts. C1 and C3 reuse v5's builders unchanged; C2b is RAG matched to C3's budget.

v5's C2 carried ~2,000 tokens against C3's larger context, so the C2-C3
comparison was not budget-matched. C2b fills the same character budget as the
task's C3 context from the cell's ``rag_chunks``, in file order, and records any
shortfall so an under-filled cell is visible rather than silent.

The five cells carried over from v5 keep their v5 ``rag_chunks`` unchanged, so
v5's own C2 prompts still rebuild byte for byte. Their extra v6 text sits in
``rag_chunks_v6``, which restates facts already in the cell's ontology as prose
and adds no new facts; C2b reads ``rag_chunks`` first, then ``rag_chunks_v6``.

Where current law superseded v5 content, v6 applies the edits in
``corrections.json`` on load (see ``corrections.py`` and ``V5-TO-V6-DIFF.md``).
"""

import importlib.util
from pathlib import Path

import corrections
import design

_spec = importlib.util.spec_from_file_location(
    "ra3_v5_conditions", design.RA3_DIR / "code" / "conditions.py"
)
v5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v5)
v5.ONTOLOGY_DIR = Path(design.ONTOLOGY_DIR)  # shipped ontologies live one level up

_v5_load_ontology = v5._load_ontology


def _load_corrected_ontology(industry: str) -> dict:
    """v5's loader plus the v6 corrections for that file (corrections.json)."""
    return corrections.apply(_v5_load_ontology(industry), corrections.for_ontology(industry))


v5._load_ontology = _load_corrected_ontology  # every v5 builder now reads corrected content

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
    onto = v5._load_ontology(t["industry"])
    chunks = onto.get("rag_chunks", []) + onto.get("rag_chunks_v6", [])
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


def c3g_system_prompt(task: dict, known: set[str]) -> tuple[str, dict]:
    """C3 with the entries this model already knows removed (stage 2, see gating.py)."""
    import gating

    t = _v5_task(task)
    full = v5._load_ontology(t["industry"])
    gated = gating.gate(full, known)
    v5._load_ontology = lambda _industry: gated
    try:
        system = v5.c3_system_prompt(t)
    finally:
        v5._load_ontology = _load_corrected_ontology
    return system, {"gated_entries": len(known)}


def build_prompt(task: dict, condition: str, known: set[str] | None = None) -> tuple[list[dict], dict]:
    """Return (messages, meta) for one task and condition.

    ``known`` is required for the stage-2 condition C3g_gated: the ontology
    entries this model knows, from gating.known_entries.
    """
    t = _v5_task(task)
    meta = {}
    if condition == "C3g_gated":
        if known is None:
            raise ValueError("C3g_gated needs the model's known entries")
        system, meta = c3g_system_prompt(task, known)
    elif condition == "C1_ungrounded":
        system = v5.c1_system_prompt(t)
    elif condition == "C3_ontology":
        system = v5.c3_system_prompt(t)
    elif condition == "C2b_rag_matched":
        system, meta = c2b_system_prompt(task)
    else:
        raise ValueError(f"unknown condition {condition}")
    meta["system_chars"] = len(system)
    return [{"role": "system", "content": system}, {"role": "user", "content": task["question"]}], meta
