#!/usr/bin/env python3
"""RA-1 D-Lite — Coder-bias pilot for `qwen3.6:27b-coding-mxfp8`.

Tests whether the local coder-tuned Qwen 27B is fit as the secondary model
for RA-1 by running 10 RA-3 tasks (2/industry x 5 industries) under
C1_ungrounded and C3_ontology, then comparing against existing Sonnet
results in `results_raw.csv`.

Output:
  - pilot_results.csv  -- raw Qwen results (20 rows)
  - pilot_summary.md   -- per-industry Sonnet vs. Qwen comparison

Pass criteria:
  - Qwen mean C1 quality >= 0.60 * Sonnet mean C1 (baseline competence)
  - Qwen mean C3 lift >= 0.70 * Sonnet mean C3 lift (ontology responsiveness)
"""

import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RA3_DIR = Path(__file__).resolve().parents[2] / "experiments" / "RA-3-pilot"
sys.path.insert(0, str(RA3_DIR))

os.environ.setdefault("RA3_AGENT_BACKEND", "ollama")
os.environ.setdefault("RA3_OLLAMA_MODEL", "qwen3.6:27b-coding-mxfp8")
os.environ.setdefault("RA3_OLLAMA_TIMEOUT_SECONDS", "600")

import config  # noqa: E402
import anthropic  # noqa: E402
from run_experiment import call_agent_ollama, evaluate_response  # noqa: E402

PILOT_TASKS = [
    "fintech_T1", "fintech_T4",
    "insurance_T1", "insurance_T4",
    "healthcare_T1", "healthcare_T4",
    "banking_vn_T1", "banking_vn_T4",
    "insurance_vn_T1", "insurance_vn_T4",
]
CONDITIONS = ["C1_ungrounded", "C3_ontology"]
OUT_DIR = Path(__file__).resolve().parent
RESULTS_FILE = OUT_DIR / "pilot_results.csv"


def main():
    with open(config.TASKS_FILE) as f:
        all_tasks = {t["id"]: t for t in json.load(f)}
    tasks = [all_tasks[tid] for tid in PILOT_TASKS]
    print(f"Loaded {len(tasks)} pilot tasks across "
          f"{len({t['industry'] for t in tasks})} industries")

    judge_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    with open(RESULTS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "task_id", "industry", "metric_tested", "condition",
            "TF", "MA", "RC", "RS",
            "agent_response_len", "wall_time_s", "timestamp",
        ])

        total = len(tasks) * len(CONDITIONS)
        done = 0
        for task in tasks:
            for condition in CONDITIONS:
                done += 1
                t0 = time.time()
                print(f"[{done}/{total}] {task['id']} | {condition} ... ",
                      end="", flush=True)
                try:
                    agent_response = call_agent_ollama(task, condition)
                    scores = evaluate_response(judge_client, task, agent_response)
                    metric = task["metric_tested"]
                    score = scores.get(metric, 0.0)
                    elapsed = time.time() - t0
                    print(f"{metric}={score:.2f} ({elapsed:.0f}s)")
                    writer.writerow([
                        task["id"], task["industry"], metric, condition,
                        scores["TF"], scores["MA"], scores["RC"], scores["RS"],
                        len(agent_response), f"{elapsed:.1f}",
                        datetime.now(timezone.utc).isoformat(),
                    ])
                    f.flush()
                except Exception as exc:
                    elapsed = time.time() - t0
                    print(f"ERROR ({elapsed:.0f}s): {exc}")
                    writer.writerow([
                        task["id"], task["industry"], task["metric_tested"], condition,
                        0, 0, 0, 0, 0, f"{elapsed:.1f}", str(exc)[:200],
                    ])
                    f.flush()

    print(f"\nDone. Results: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
