#!/usr/bin/env python3
"""Stale-knowledge arm: every item, every model, closed-book and with the cell's ontology context.

    python run_stale.py --dry-run
    python run_stale.py --models qwen3.8-2.4t-a95b --cells banking_vn
    python run_stale.py --analyse        # H8 from the log, after the runs
"""

import argparse
import json
import sys

import design
import runlog
import stale
from run_probe import format_item, parse_letter

OUT = design.RESULTS_DIR / "stale_raw.jsonl"
MODES = ("closed", "grounded")


def paired_rows() -> list[dict]:
    """One row per item x model that has both answers logged."""
    items = {i["id"]: i for i in stale.load_items()}
    seen = {}
    for r in runlog.read(OUT):
        if not r.get("error") and r["item_id"] in items:
            seen.setdefault((r["item_id"], r["model"]), {})[r["mode"]] = stale.classify(items[r["item_id"]], r["chosen"])
    return [
        {"item_id": i, "model": m, "cell": items[i]["cell"], **modes}
        for (i, m), modes in sorted(seen.items()) if set(modes) == set(MODES)
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--analyse", action="store_true")
    ap.add_argument("--models", nargs="*")
    ap.add_argument("--cells", nargs="*")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    if args.analyse:
        rows = paired_rows()
        if not rows:
            sys.exit("no complete closed and grounded pairs in the log")
        print(json.dumps(stale.h8(rows), indent=1))
        return 0

    items = stale.load_items()
    problems = stale.validate(items)
    for p in problems:
        print(f"[warn] {p}")
    lock = design.load_lock()
    models = [m for m in design.agent_models(lock) if not args.models or m["key"] in args.models]
    done = runlog.done_keys(OUT)
    todo = []
    for item in items:
        if args.cells and item["cell"] not in args.cells:
            continue
        for m in models:
            for mode in MODES:
                key = f"{m['key']}|{item['id']}|{mode}"
                if key not in done:
                    todo.append((key, item, m, mode))
    if args.limit:
        todo = todo[: args.limit]
    full = 2 * stale.PER_JURISDICTION * len(design.JURISDICTIONS) * len(design.agent_models(lock))
    print(f"{len(items)} items, {len(todo)} stale-set calls to run (full design: {full})")
    if args.dry_run:
        return 0
    if problems:
        sys.exit("stale set invalid")
    if any(i.get("status") != "confirmed" for i in items):
        sys.exit("every stale item must be expert-confirmed (status 'confirmed') before it is run")

    from openrouter_client import OpenRouterError, chat

    for n, (key, item, m, mode) in enumerate(todo, 1):
        system = stale.CLOSED_SYSTEM if mode == "closed" else stale.grounded_system(item["cell"])
        row = {"key": key, "model": m["key"], "cell": item["cell"], "item_id": item["id"], "mode": mode}
        try:
            res = chat(m["openrouter_id"],
                       [{"role": "system", "content": system}, {"role": "user", "content": format_item(item)}],
                       max_tokens=design.PROBE_MAX_TOKENS, temperature=0.0, seed=design.call_seed(key),
                       provider_order=m.get("provider_order") or None, reasoning=m.get("reasoning"))
            row.update({k: res[k] for k in ("served_model", "provider", "usage", "text")})
            row["chosen"] = parse_letter(res["text"])
            row["class"] = stale.classify(item, row["chosen"])
        except OpenRouterError as exc:
            row["error"] = str(exc)
        runlog.append(OUT, row)
        print(f"[{n}/{len(todo)}] {key} {'ERROR' if row.get('error') else row['class']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
