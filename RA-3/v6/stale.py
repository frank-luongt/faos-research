"""Stale-knowledge set (protocol H8): rules that changed between 2022 and 2026.

Each item in ``stale/items.json`` is a four-option question whose options include
both the current value and the value it superseded:

  {"id": "banking_vn_S01", "cell": "banking_vn",
   "question": "...", "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
   "answer": "B",             # the current rule
   "superseded": "D",         # the rule it replaced
   "effective": "2023-03-01", # when the current rule took effect
   "source": "Law 14/2022/QH15, art. 26",
   "evidence": "3 working days",  # text the cell's ontology context must contain
   "status": "draft"}         # draft until a domain expert confirms it

Every model answers every item twice: closed-book, and with the cell's ontology
context. An answer is ``current``, ``superseded`` or ``other``. H8 is supported if
the share of superseded answers is lower with the context.

An item is usable only if the grounded prompt really states the current value,
so ``validate`` checks that ``evidence`` appears in it. Stale items are kept out
of the 90-item coverage probe.
"""

import json
from datetime import date

import numpy as np

import design
from conditions_v6 import v5

ITEMS_FILE = design.V6_DIR / "stale" / "items.json"
PER_JURISDICTION = 30
MIN_INDUSTRIES_PER_JURISDICTION = 4
WINDOW = (date(2022, 1, 1), date(2026, 12, 31))
N_PERM = 10_000

CLOSED_SYSTEM = (
    "Answer from your own knowledge only. You will get a multiple-choice question. "
    "Reply with the single letter of the correct option and nothing else."
)
GROUNDED_SUFFIX = (
    "\n\nYou will get a multiple-choice question. Use the ontology context above where it applies. "
    "Reply with the single letter of the correct option and nothing else."
)


def load_items() -> list[dict]:
    if not ITEMS_FILE.exists():
        return []
    with open(ITEMS_FILE) as f:
        return json.load(f)


def ontology_context(cell: str) -> str:
    """The cell's full C3 context, with regulations, as v5's builder renders it (v6 corrections applied)."""
    return v5.c3_system_prompt({"industry": design.ontology_stem(cell), "metric_tested": "ALL", "ground_truth": {}})


def grounded_system(cell: str) -> str:
    return ontology_context(cell) + GROUNDED_SUFFIX


def classify(item: dict, chosen: str | None) -> str:
    if chosen == item["answer"]:
        return "current"
    if chosen == item["superseded"]:
        return "superseded"
    return "other"


def validate(items: list[dict], complete: bool = True) -> list[str]:
    """Return problems with the stale set (empty list = valid).

    ``complete=False`` skips the size and spread rules, for a set still being written.
    """
    problems = []
    ids = [i["id"] for i in items]
    if len(ids) != len(set(ids)):
        problems.append("duplicate item ids")
    contexts = {}
    for it in items:
        cell = it.get("cell")
        if cell not in design.CELLS:
            problems.append(f"{it['id']}: unknown cell {cell}")
            continue
        if not it["id"].startswith(f"{cell}_S"):
            problems.append(f"{it['id']}: id must start with {cell}_S")
        opts = it["options"]
        if sorted(opts) != ["A", "B", "C", "D"] or len(set(opts.values())) != 4:
            problems.append(f"{it['id']}: needs four distinct options A-D")
        if it["answer"] not in opts or it["superseded"] not in opts or it["answer"] == it["superseded"]:
            problems.append(f"{it['id']}: answer and superseded must be two different options")
        try:
            eff = date.fromisoformat(it["effective"])
            if not WINDOW[0] <= eff <= WINDOW[1]:
                problems.append(f"{it['id']}: effective date {eff} is outside 2022-2026")
        except (KeyError, ValueError):
            problems.append(f"{it['id']}: needs an ISO effective date")
        if not it.get("source"):
            problems.append(f"{it['id']}: needs a source")
        ctx = contexts.setdefault(cell, ontology_context(cell))
        if not it.get("evidence") or it["evidence"] not in ctx:
            problems.append(f"{it['id']}: the ontology context does not state the current value ({it.get('evidence')!r})")
    if complete:
        for j in design.JURISDICTIONS:
            js = [i for i in items if i.get("cell") in design.CELLS and design.jurisdiction(i["cell"]) == j]
            if len(js) != PER_JURISDICTION:
                problems.append(f"{j}: {len(js)} items, expected {PER_JURISDICTION}")
            inds = {i["cell"].rsplit("_", 1)[0] for i in js}
            if len(inds) < MIN_INDUSTRIES_PER_JURISDICTION:
                problems.append(f"{j}: items cover {len(inds)} industries, need {MIN_INDUSTRIES_PER_JURISDICTION}")
        for field in ("answer", "superseded"):
            counts = {k: sum(i[field] == k for i in items) for k in "ABCD"}
            if items and max(counts.values()) - min(counts.values()) > 4:
                problems.append(f"{field} letters unbalanced {counts}")
    return problems


def h8(rows: list[dict], n_perm: int = N_PERM) -> dict:
    """rows: {"item_id", "model", "cell", "closed", "grounded"} with each answer classed by ``classify``.

    Statistic: closed-book share of superseded answers minus the grounded share.
    Null: swap the two answers within pairs, flipping whole items together,
    which keeps each item in its own country.
    """
    items = sorted({r["item_id"] for r in rows})
    idx = {k: i for i, k in enumerate(items)}
    closed = np.zeros(len(items))
    grounded = np.zeros(len(items))
    for r in rows:
        closed[idx[r["item_id"]]] += r["closed"] == "superseded"
        grounded[idx[r["item_id"]]] += r["grounded"] == "superseded"
    n = len(rows)
    diff = closed - grounded  # per item, summed over models
    stat = diff.sum() / n
    rng = np.random.default_rng(design.call_seed("h8-permutation"))
    signs = rng.choice([-1.0, 1.0], size=(n_perm, len(items)))
    null = signs @ diff / n
    by_country = {}
    for j in design.JURISDICTIONS:
        js = [r for r in rows if design.jurisdiction(r["cell"]) == j]
        if js:
            by_country[j] = {
                "n": len(js),
                "closed_superseded": round(sum(r["closed"] == "superseded" for r in js) / len(js), 4),
                "grounded_superseded": round(sum(r["grounded"] == "superseded" for r in js) / len(js), 4),
            }
    wrong_closed = [r for r in rows if r["closed"] != "current"]
    repair = {}
    for kind in ("superseded", "other"):
        ks = [r for r in wrong_closed if r["closed"] == kind]
        repair[kind] = round(sum(r["grounded"] == "current" for r in ks) / len(ks), 4) if ks else None
    return {
        "n_pairs": n,
        "n_items": len(items),
        "closed_superseded": round(float(closed.sum() / n), 4),
        "grounded_superseded": round(float(grounded.sum() / n), 4),
        "difference": round(float(stat), 4),
        "p_one_sided": float((1 + np.sum(null >= stat - 1e-12)) / (1 + n_perm)),
        "n_perm": n_perm,
        "by_country": by_country,
        "repair_rate_by_closed_answer": repair,  # secondary: is an old rule defended more than a guess?
    }
