#!/usr/bin/env python3
"""Agent runs: every task x condition x model once, plus the seeded 10% repeats.

    python run_agents.py --dry-run                 # counts and prompt sizes, no calls
    python run_agents.py --dry-run --v5-tasks      # same, on v5's tasks mapped to v6 cells
    python run_agents.py --models kimi-k3.1-pro --limit 5
"""

import argparse
import sys

import design
import runlog
from conditions_v6 import build_prompt

OUT = design.RESULTS_DIR / "agent_raw.jsonl"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--v5-tasks", action="store_true", help="use v5 tasks (dry runs only)")
    ap.add_argument("--models", nargs="*", help="model keys from models.lock.json")
    ap.add_argument("--cells", nargs="*")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    if args.v5_tasks and not args.dry_run:
        sys.exit("--v5-tasks is for dry runs only")
    lock = design.load_lock()
    if not args.v5_tasks and not design.TASKS_FILE.exists():
        sys.exit(f"{design.TASKS_FILE.name} not written yet; use --dry-run --v5-tasks to check the harness")
    tasks = design.load_v5_tasks_as_v6() if args.v5_tasks else design.load_tasks()
    if not args.v5_tasks:
        problems = design.validate_tasks(tasks)
        if problems and not args.dry_run:
            sys.exit("task set invalid:\n  " + "\n  ".join(problems))
        for p in problems:
            print(f"[warn] {p}")
    by_id = {t["id"]: t for t in tasks}
    models = {m["key"]: m for m in design.agent_models(lock)}

    runs = design.run_matrix(list(by_id), lock)
    if args.models:
        runs = [r for r in runs if r["model"] in args.models]
    if args.cells:
        runs = [r for r in runs if by_id[r["task_id"]]["cell"] in args.cells]
    done = runlog.done_keys(OUT)
    todo = [r for r in runs if design.run_key(r) not in done]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(runs)} runs in scope ({sum(r['rep'] == 2 for r in runs)} repeats), "
          f"{len(runs) - len([r for r in runs if design.run_key(r) not in done])} done, {len(todo)} to run")

    if args.dry_run:
        sizes = {}
        for r in runs:
            if r["model"] != runs[0]["model"] or r["rep"] != 1:
                continue
            _, meta = build_prompt(by_id[r["task_id"]], r["condition"])
            sizes.setdefault(r["condition"], []).append(meta)
        for cond, metas in sizes.items():
            chars = [m["system_chars"] for m in metas]
            line = f"  {cond}: system prompt {min(chars)}-{max(chars)} chars"
            short = [m["shortfall_chars"] for m in metas if m.get("shortfall_chars")]
            if short:
                line += f"; {len(short)}/{len(metas)} under budget (max shortfall {max(short)} chars)"
            print(line)
        return 0

    from openrouter_client import OpenRouterError, chat

    for i, r in enumerate(todo, 1):
        key = design.run_key(r)
        task, m = by_id[r["task_id"]], models[r["model"]]
        messages, meta = build_prompt(task, r["condition"])
        row = {"key": key, **r, "cell": task["cell"], "openrouter_id": m["openrouter_id"], "prompt_meta": meta}
        try:
            res = chat(m["openrouter_id"], messages, max_tokens=design.AGENT_MAX_TOKENS,
                       temperature=design.AGENT_TEMPERATURE, seed=design.call_seed(key),
                       provider_order=m.get("provider_order") or None, reasoning=m.get("reasoning"))
            row.update(res)
        except OpenRouterError as exc:
            row["error"] = str(exc)
        runlog.append(OUT, row)
        print(f"[{i}/{len(todo)}] {key} {'ERROR ' + row['error'][:80] if row.get('error') else row.get('provider')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
