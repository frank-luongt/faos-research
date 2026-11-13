#!/usr/bin/env python3
"""Write the seeded judge-pair rotation and 10% repeat list for the locked task set.

Run once at lock; the two files are hashed with the protocol.
"""

import json
import sys

import design


def main() -> int:
    tasks = design.load_tasks()
    problems = design.validate_tasks(tasks)
    if problems:
        sys.exit("task set invalid:\n  " + "\n  ".join(problems))
    lock = design.load_lock()
    by_cell = {}
    for t in tasks:
        by_cell.setdefault(t["cell"], []).append(t["id"])
    pairs = design.assign_judge_pairs(by_cell, lock)
    out_dir = design.V6_DIR / "assignments"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "judge_pairs.json").write_text(json.dumps(
        {"|".join(k): {t: list(p) for t, p in v.items()} for k, v in sorted(pairs.items())}, indent=1))
    repeats = [r for r in design.run_matrix([t["id"] for t in tasks], lock) if r["rep"] == 2]
    (out_dir / "repeats.json").write_text(json.dumps(repeats, indent=1))
    print(f"seed {design.GLOBAL_SEED}: {len(pairs)} judge rotations, {len(repeats)} repeats -> {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
