#!/usr/bin/env python3
"""Coverage score per cell x model = probe accuracy. Never computed from C1 scores."""

import csv
import sys

import design
import runlog


def coverage_table() -> list[dict]:
    rows = [r for r in runlog.read(design.RESULTS_DIR / "probe_raw.jsonl") if not r.get("error")]
    agg = {}
    for r in rows:
        a = agg.setdefault((r["cell"], r["model"]), [0, 0])
        a[0] += bool(r["correct"])
        a[1] += 1
    return [
        {"cell": c, "jurisdiction": design.jurisdiction(c), "model": m, "n_items": n, "coverage": round(k / n, 4)}
        for (c, m), (k, n) in sorted(agg.items())
    ]


def main() -> int:
    table = coverage_table()
    out = design.RESULTS_DIR / "coverage.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["cell", "jurisdiction", "model", "n_items", "coverage"])
        w.writeheader()
        w.writerows(table)
    print(f"{len(table)} cell x model rows -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
