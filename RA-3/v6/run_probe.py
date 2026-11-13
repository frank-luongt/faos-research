#!/usr/bin/env python3
"""Closed-book coverage probe: 90 items per cell, every model, before any grounded run.

Items live in probe/<cell>.json as a list of
  {"id": "banking_vn_P001", "question": "...", "options": {"A": "...", "B": "...", "C": "...", "D": "..."}, "answer": "B"}
drawn from the cell's ontology facts and never overlapping the tasks.
A model's coverage for a cell is its share of correct answers (see coverage.py).

    python run_probe.py --dry-run
    python run_probe.py --models qwen3.8-2.4t-a95b --cells banking_vn
"""

import argparse
import json
import re
import sys

import design
import runlog

OUT = design.RESULTS_DIR / "probe_raw.jsonl"
SYSTEM = (
    "Answer from your own knowledge only. You will get a multiple-choice question. "
    "Reply with the single letter of the correct option and nothing else."
)


def load_items(cell: str) -> list[dict]:
    path = design.PROBE_DIR / f"{cell}.json"
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def format_item(item: dict) -> str:
    opts = "\n".join(f"{k}. {v}" for k, v in sorted(item["options"].items()))
    return f"{item['question']}\n\n{opts}"


def parse_letter(text: str) -> str | None:
    m = re.search(r"\b([A-D])\b", text.strip().upper())
    return m.group(1) if m else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--models", nargs="*")
    ap.add_argument("--cells", nargs="*")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    lock = design.load_lock()
    models = [m for m in design.agent_models(lock) if not args.models or m["key"] in args.models]
    cells = args.cells or design.CELLS
    done = runlog.done_keys(OUT)
    todo, missing = [], []
    for cell in cells:
        items = load_items(cell)
        if len(items) != design.PROBE_ITEMS_PER_CELL:
            missing.append(f"{cell}: {len(items)}/{design.PROBE_ITEMS_PER_CELL} items")
        for item in items:
            for m in models:
                key = f"{m['key']}|{item['id']}"
                if key not in done:
                    todo.append((key, cell, item, m))
    for line in missing:
        print(f"[warn] {line}")
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(todo)} probe calls to run "
          f"(full design: {len(design.CELLS) * design.PROBE_ITEMS_PER_CELL * len(design.agent_models(lock))})")
    if args.dry_run:
        return 0
    if missing and not args.cells:
        sys.exit("probe item sets incomplete")

    from openrouter_client import OpenRouterError, chat

    for i, (key, cell, item, m) in enumerate(todo, 1):
        row = {"key": key, "model": m["key"], "cell": cell, "item_id": item["id"], "answer": item["answer"]}
        try:
            res = chat(m["openrouter_id"],
                       [{"role": "system", "content": SYSTEM}, {"role": "user", "content": format_item(item)}],
                       max_tokens=design.PROBE_MAX_TOKENS, temperature=0.0, seed=design.call_seed(key),
                       provider_order=m.get("provider_order") or None, reasoning=m.get("reasoning"))
            row.update({k: res[k] for k in ("served_model", "provider", "usage", "text")})
            row["chosen"] = parse_letter(res["text"])
            row["correct"] = row["chosen"] == item["answer"]
        except OpenRouterError as exc:
            row["error"] = str(exc)
        runlog.append(OUT, row)
        print(f"[{i}/{len(todo)}] {key} {'ERROR' if row.get('error') else row['correct']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
