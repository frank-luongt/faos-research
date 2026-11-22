#!/usr/bin/env python3
"""One tiny call to every pinned model and judge, to confirm IDs, routing and prices before lock.

    OPENROUTER_API_KEY=... python smoke_test.py

Writes results/smoke.json with the served model, routed provider and usage for
each, which fill the open fields in models.lock.json.
"""

import json
import sys

import design
from openrouter_client import OpenRouterError, chat, decide

# Jev answers typed questions on the Decisions API, not chat. This one-question
# call confirms the request format run_jev.py relies on.
JEV_STATE = "A bank reports a CET1 ratio of 3.9% against a 4.5% regulatory minimum."
JEV_QUESTIONS = {"q": {"type": "score", "instructions": "Is the bank's CET1 ratio adequate?",
                       "criteria": ["Clearly below the minimum", "At the minimum", "Clearly above the minimum"]}}


def main() -> int:
    lock = design.load_lock()
    targets = [(m["key"], m["openrouter_id"]) for m in lock["agents"]]
    report, failed = [], 0
    for key, model in targets:
        try:
            res = chat(model, [{"role": "user", "content": "Reply with the single word OK."}],
                       max_tokens=256, temperature=0.0, retries=1)
            entry = {"key": key, "requested": model, **{k: res[k] for k in
                     ("served_model", "provider", "usage", "finish_reason", "latency_s")},
                     "text": res["text"][:80]}
            status = "ok" if res["text"].strip() else "EMPTY"
        except OpenRouterError as exc:
            entry, status = {"key": key, "requested": model, "error": str(exc)}, "FAIL"
            failed += 1
        report.append(entry)
        print(f"{status:5s} {model:36s} served={entry.get('served_model')} provider={entry.get('provider')}")
    jev = lock["secondary_judge"]["openrouter_id"]
    try:
        res = decide(jev, JEV_STATE, JEV_QUESTIONS, retries=1)
        ans = res["answers"].get("q") or {}
        entry = {"key": "jev", "requested": jev, "answers": res["answers"],
                 **{k: res[k] for k in ("served_model", "provider", "usage", "latency_s")}}
        status = "ok" if ans.get("type") == "score" and "score" in ans else "SHAPE"
        failed += status != "ok"
    except OpenRouterError as exc:
        entry, status = {"key": "jev", "requested": jev, "error": str(exc)}, "FAIL"
        failed += 1
    report.append(entry)
    print(f"{status:5s} {jev:36s} served={entry.get('served_model')} answer={entry.get('answers')}")
    out = design.RESULTS_DIR / "smoke.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(f"-> {out}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
