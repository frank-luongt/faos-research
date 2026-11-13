#!/usr/bin/env python3
"""Stage 2: coverage-gated grounding (condition C3g, protocol H9).

C3g gives a model only the ontology entries the probe shows it does not know.

Tags. ``probe/tags/<cell>.json`` maps each probe item id to the ontology entry
it tests, as a dotted path into the cell's ontology file, for example
``domain_layer.concepts.npl_ratio`` or ``role_layer.chief_risk_officer.kpis.npl_ratio``.
An item that tests no single entry maps to null. Tags are written and checked
before the main lock; if they are incomplete, stage 2 is dropped.

Gating rule (fixed in the protocol). For one model and cell, an entry is
*known* if at least two probe items map to it and the model answered all of
them correctly. Known entries are removed from that model's C3 context. Entries
with fewer than two items stay. Role decision patterns and interaction-layer
hand-offs are never gated, because the probe does not test them.

``python gating.py`` reports tag coverage. ``python gating.py --addendum``
writes ``assignments/c3g_addendum.json`` after the probe and before any C3g run:
the probe log's hash, and for each task x model the gated context's hash and
its length against C3.
"""

import argparse
import copy
import hashlib
import json
import sys
from collections import defaultdict

import design
import runlog

TAGS_DIR = design.PROBE_DIR / "tags"
ADDENDUM = design.V6_DIR / "assignments" / "c3g_addendum.json"
PROBE_LOG = design.RESULTS_DIR / "probe_raw.jsonl"
MIN_ITEMS = 2
NEVER_GATED = ("decision_patterns", "interaction_layer")
CONDITION = "C3g_gated"


def load_tags(cell: str) -> dict[str, str | None]:
    path = TAGS_DIR / f"{cell}.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def _resolve(onto: dict, path: str):
    obj = onto
    for part in path.split("."):
        if not isinstance(obj, dict) or part not in obj:
            raise KeyError(path)
        obj = obj[part]
    return obj


def validate_tags(cell: str, tags: dict, probe_ids: list[str], onto: dict) -> list[str]:
    """Return problems with one cell's tags (empty list = valid and complete)."""
    problems = []
    missing = sorted(set(probe_ids) - set(tags))
    extra = sorted(set(tags) - set(probe_ids))
    if missing:
        problems.append(f"{cell}: {len(missing)} probe items untagged")
    if extra:
        problems.append(f"{cell}: tags for unknown items {extra[:3]}")
    for item, path in tags.items():
        if path is None:
            continue
        if any(part in path.split(".") for part in NEVER_GATED):
            problems.append(f"{cell}: {item} is tagged to {path}, which is never gated")
            continue
        try:
            _resolve(onto, path)
        except KeyError:
            problems.append(f"{cell}: {item} is tagged to {path}, which is not in the ontology")
    return problems


def known_entries(tags: dict[str, str | None], correct: dict[str, bool]) -> set[str]:
    """Entries with at least MIN_ITEMS tagged items, every one answered correctly.

    ``correct`` maps probe item id to whether this model answered it correctly;
    an item with no logged answer counts as not known.
    """
    by_entry = defaultdict(list)
    for item, path in tags.items():
        if path is not None:
            by_entry[path].append(correct.get(item, False))
    return {p for p, oks in by_entry.items() if len(oks) >= MIN_ITEMS and all(oks)}


def gate(onto: dict, known: set[str]) -> dict:
    """A copy of the ontology with the known entries removed."""
    out = copy.deepcopy(onto)
    for path in sorted(known, key=lambda p: -p.count(".")):  # deepest first
        *parents, leaf = path.split(".")
        obj = out
        for part in parents:
            obj = obj[part]
        del obj[leaf]
    return out


def probe_correct(model: str, cell: str, rows: list[dict] | None = None) -> dict[str, bool]:
    rows = runlog.read(PROBE_LOG) if rows is None else rows
    return {r["item_id"]: bool(r["correct"]) for r in rows
            if not r.get("error") and r["model"] == model and r["cell"] == cell}


def tag_report() -> list[str]:
    from conditions_v6 import v5
    lines, all_ok = [], True
    for cell in design.CELLS:
        with open(design.PROBE_DIR / f"{cell}.json") as f:
            ids = [i["id"] for i in json.load(f)]
        tags = load_tags(cell)
        onto = v5._load_ontology(design.ontology_stem(cell))
        problems = validate_tags(cell, tags, ids, onto)
        all_ok &= not problems
        per_entry = defaultdict(int)
        for p in tags.values():
            if p:
                per_entry[p] += 1
        gateable = sum(1 for n in per_entry.values() if n >= MIN_ITEMS)
        lines.append(f"{cell}: {len(tags)}/{len(ids)} tagged, {gateable} entries gateable"
                     + (f"  [{'; '.join(problems)}]" if problems else ""))
    lines.append("tags complete" if all_ok else "tags incomplete: stage 2 cannot be registered")
    return lines


def write_addendum() -> int:
    from conditions_v6 import build_prompt
    rows = runlog.read(PROBE_LOG)
    if not rows:
        sys.exit("no probe log; run the probe first")
    if any(r.get("condition") == CONDITION for r in runlog.read(design.RESULTS_DIR / "agent_raw.jsonl")):
        sys.exit("C3g runs are already logged; the addendum must come before them")
    report = tag_report()
    if report[-1] != "tags complete":
        sys.exit("\n".join(report))
    entries = []
    for task in design.load_tasks():
        for m in design.agent_models():
            known = known_entries(load_tags(task["cell"]), probe_correct(m["key"], task["cell"], rows))
            c3 = build_prompt(task, "C3_ontology")[0][0]["content"]
            c3g, meta = build_prompt(task, CONDITION, known=known)
            entries.append({
                "task_id": task["id"], "model": m["key"], "known_entries": sorted(known),
                "c3_chars": len(c3), "c3g_chars": meta["system_chars"],
                "c3g_sha256": hashlib.sha256(c3g[0]["content"].encode()).hexdigest(),
            })
    doc = {
        "rule": f"entry known if >= {MIN_ITEMS} tagged probe items, all correct; {', '.join(NEVER_GATED)} never gated",
        "probe_log_sha256": hashlib.sha256(PROBE_LOG.read_bytes()).hexdigest(),
        "mean_length_ratio": round(sum(e["c3g_chars"] / e["c3_chars"] for e in entries) / len(entries), 4),
        "contexts": entries,
    }
    ADDENDUM.parent.mkdir(parents=True, exist_ok=True)
    ADDENDUM.write_text(json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"{len(entries)} gated contexts, mean length {doc['mean_length_ratio']:.0%} of C3 -> {ADDENDUM}")
    print(f"sha256 {hashlib.sha256(ADDENDUM.read_bytes()).hexdigest()}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--addendum", action="store_true")
    args = ap.parse_args()
    if args.addendum:
        return write_addendum()
    print("\n".join(tag_report()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
