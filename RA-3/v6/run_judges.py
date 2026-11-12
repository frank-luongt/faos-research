#!/usr/bin/env python3
"""Judge panel: two cross-family judges per agent response, by the seeded rotation.

A judge never scores its own family's response. Open-weight responses get the
three judge pairs balanced within each cell x model x condition. Repeat runs
(rep 2) use the same pair as their primary run. Prompts are v5's rubrics.

    python run_judges.py --dry-run
    python run_judges.py --limit 20
"""

import argparse
import importlib.util
import json
import sys

import design
import runlog

AGENT_LOG = design.RESULTS_DIR / "agent_raw.jsonl"
OUT = design.RESULTS_DIR / "judge_raw.jsonl"
SYSTEM = "You are a precise evaluation judge. Always respond with valid JSON only."

_spec = importlib.util.spec_from_file_location("ra3_v5_judge", design.RA3_DIR / "code" / "judge.py")
v5_judge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v5_judge)


def parse_scores(text: str, metric: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        text = text.rsplit("```", 1)[0].strip()
    data = json.loads(text)
    if metric == "ALL":
        return {k: float(data.get(f"{k}_score", 0.0)) for k in ("TF", "MA", "RC", "RS")} | {"detail": data}
    return {metric: float(data.get("score", 0.0)), "detail": data}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    lock = design.load_lock()
    if not design.TASKS_FILE.exists():
        print(f"{design.TASKS_FILE.name} not written yet; nothing to judge")
        return 0
    tasks = {t["id"]: t for t in design.load_tasks()}
    tasks_by_cell = {}
    for t in tasks.values():
        tasks_by_cell.setdefault(t["cell"], []).append(t["id"])
    assignment = design.assign_judge_pairs(tasks_by_cell, lock)
    judges = {j["family"]: j for j in design.panel_judges(lock)}

    agent_rows = [r for r in runlog.read(AGENT_LOG) if not r.get("error")]
    done = runlog.done_keys(OUT)
    todo = []
    for r in agent_rows:
        for fam in assignment[(r["cell"], r["model"], r["condition"])][r["task_id"]]:
            key = f"{r['key']}|judge={fam}"
            if key not in done:
                todo.append((key, fam, r))
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(agent_rows)} responses, {len(todo)} judge calls to run")
    if args.dry_run:
        return 0

    from openrouter_client import OpenRouterError, chat

    for i, (key, fam, r) in enumerate(todo, 1):
        task, judge = tasks[r["task_id"]], judges[fam]
        metric = task["metric_tested"]
        prompt = v5_judge.JUDGE_BUILDERS[metric](task, r["text"])
        row = {"key": key, "agent_key": r["key"], "judge_family": fam,
               "judge_id": judge["openrouter_id"], "metric_tested": metric}
        try:
            res = chat(judge["openrouter_id"],
                       [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
                       max_tokens=design.JUDGE_MAX_TOKENS, temperature=design.JUDGE_TEMPERATURE,
                       seed=design.call_seed(key), provider_order=judge.get("provider_order") or None)
            row.update({k: res[k] for k in ("served_model", "provider", "usage", "generation_id")})
            row["raw"] = res["text"]
            row["scores"] = parse_scores(res["text"], metric)
        except OpenRouterError as exc:
            row["error"] = str(exc)
        except (json.JSONDecodeError, ValueError) as exc:
            row["error"] = f"invalid judge JSON: {exc}"
        runlog.append(OUT, row)
        print(f"[{i}/{len(todo)}] {key} {'ERROR' if row.get('error') else row['scores'].get(metric, '')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
