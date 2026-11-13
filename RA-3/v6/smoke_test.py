#!/usr/bin/env python3
"""One tiny call to every pinned model and judge, to confirm IDs, routing and prices before lock.

    OPENROUTER_API_KEY=... python smoke_test.py

Writes results/smoke.json with the served model, routed provider and usage for
each, which fill the open fields in models.lock.json.
"""

import json
import sys

import design
from openrouter_client import OpenRouterError, chat


def main() -> int:
    lock = design.load_lock()
    targets = [(m["key"], m["openrouter_id"]) for m in lock["agents"]]
    targets.append(("jev", lock["secondary_judge"]["openrouter_id"]))
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
    out = design.RESULTS_DIR / "smoke.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(f"-> {out}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
