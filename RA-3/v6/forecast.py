#!/usr/bin/env python3
"""Registered forecasts of grounding lift from the coverage probe (protocol H7).

Before any grounded run, the probe's coverage gives one predicted lift per
cell x model from the line the power simulation anchored on v5:

    predicted lift = 0.12 - 0.8 * (coverage - 0.70)      (zero at coverage 0.85)

``python forecast.py`` writes ``assignments/forecasts.json`` and prints its
SHA-256, which is recorded beside the protocol lock. It refuses to run once a
grounded agent run is in the log.

After the runs:
  * ``calibration`` scores the point forecasts (descriptive only: v5's models
    are retired, so the line's level may be off even if its direction holds);
  * ``h7`` is the confirmatory test. Leave one industry out, fit lift ~ coverage
    on the other five, predict the sixth, and compare the mean absolute error
    with a country-only model fitted the same way. The null permutes coverage
    across cells within each country.

The lift itself (which metrics, how averaged) is fixed at lock and passed in.
"""

import hashlib
import json
import sys

import numpy as np

import design
import runlog
from coverage import coverage_table

INTERCEPT, SLOPE, ANCHOR = 0.12, -0.8, 0.70
ZERO_CROSSING = ANCHOR - INTERCEPT / SLOPE  # 0.85
OUT = design.V6_DIR / "assignments" / "forecasts.json"
AGENT_LOG = design.RESULTS_DIR / "agent_raw.jsonl"
N_PERM = 10_000


def forecast_lift(coverage: float) -> float:
    return INTERCEPT + SLOPE * (coverage - ANCHOR)


def build_forecasts(table: list[dict]) -> list[dict]:
    """One row per cell x model, sorted, from coverage.py's table."""
    rows = [
        {"cell": r["cell"], "model": r["model"], "coverage": r["coverage"],
         "forecast_lift": round(forecast_lift(r["coverage"]), 4)}
        for r in table
    ]
    return sorted(rows, key=lambda r: (r["cell"], r["model"]))


def canonical(obj) -> bytes:
    return (json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode()


def grounded_runs_logged() -> int:
    return sum(1 for r in runlog.read(AGENT_LOG) if r.get("condition") != "C1_ungrounded")


def industry(cell: str) -> str:
    return cell.rsplit("_", 1)[0]


def _arrays(points: list[dict]):
    """points: {"cell", "model", "coverage", "lift"} for every cell x model."""
    cells = sorted({p["cell"] for p in points})
    models = sorted({p["model"] for p in points})
    cov = np.full((len(cells), len(models)), np.nan)
    lift = np.full_like(cov, np.nan)
    for p in points:
        i, j = cells.index(p["cell"]), models.index(p["model"])
        cov[i, j], lift[i, j] = p["coverage"], p["lift"]
    if np.isnan(cov).any() or np.isnan(lift).any():
        raise ValueError("every cell x model needs a coverage and a lift")
    return cells, cov, lift


def calibration(forecasts: list[dict], lifts: dict[tuple[str, str], float]) -> dict:
    """Observed lift regressed on forecast lift, the forecast error, and the observed zero-crossing."""
    f = np.array([r["forecast_lift"] for r in forecasts])
    c = np.array([r["coverage"] for r in forecasts])
    y = np.array([lifts[(r["cell"], r["model"])] for r in forecasts])
    slope, intercept = np.polyfit(f, y, 1)
    b, a = np.polyfit(c, y, 1)  # observed lift ~ coverage
    return {
        "n": len(y),
        "calibration_slope": round(float(slope), 4),
        "calibration_intercept": round(float(intercept), 4),
        "mean_absolute_error": round(float(np.mean(np.abs(y - f))), 4),
        "forecast_zero_crossing": round(ZERO_CROSSING, 4),
        "observed_zero_crossing": round(float(-a / b), 4) if b < 0 else None,
    }


def _loio_gain(cells: list[str], cov: np.ndarray, lift: np.ndarray) -> tuple[float, float, float]:
    """(MAE country-only, MAE coverage-only, their difference) over all held-out cell x model lifts."""
    inds = [industry(c) for c in cells]
    vn = np.array([design.jurisdiction(c) == "vn" for c in cells])
    err_cov, err_country = [], []
    for held in sorted(set(inds)):
        test = np.array([i == held for i in inds])
        train = ~test
        slope, intercept = np.polyfit(cov[train].ravel(), lift[train].ravel(), 1)
        err_cov.append(np.abs(lift[test] - (intercept + slope * cov[test])).ravel())
        for is_vn in (False, True):
            rows = test & (vn == is_vn)
            if rows.any():
                err_country.append(np.abs(lift[rows] - lift[train & (vn == is_vn)].mean()).ravel())
    mae_cov = float(np.concatenate(err_cov).mean())
    mae_country = float(np.concatenate(err_country).mean())
    return mae_country, mae_cov, mae_country - mae_cov


def h7(points: list[dict], n_perm: int = N_PERM) -> dict:
    """Leave-one-industry-out forecast test; supported if p < alpha in its Holm family."""
    cells, cov, lift = _arrays(points)
    mae_country, mae_cov, gain = _loio_gain(cells, cov, lift)
    vn = np.array([design.jurisdiction(c) == "vn" for c in cells])
    groups = [np.flatnonzero(vn == v) for v in (False, True)]
    rng = np.random.default_rng(design.call_seed("h7-permutation"))
    hits = 0
    for _ in range(n_perm):
        order = np.arange(len(cells))
        for g in groups:
            order[g] = rng.permutation(g)
        hits += _loio_gain(cells, cov[order], lift)[2] >= gain
    return {
        "n_held_out": int(lift.size),
        "mae_country_only": round(mae_country, 4),
        "mae_coverage_only": round(mae_cov, 4),
        "mae_gain": round(gain, 4),
        "p_one_sided": (1 + hits) / (1 + n_perm),
        "n_perm": n_perm,
    }


def main() -> int:
    n = grounded_runs_logged()
    if n:
        sys.exit(f"{n} grounded runs are already logged; forecasts must be registered before them")
    table = coverage_table()
    expected = len(design.CELLS) * len(design.agent_models())
    if len(table) != expected:
        sys.exit(f"coverage has {len(table)} cell x model rows, expected {expected}; finish the probe first")
    short = [r for r in table if r["n_items"] != design.PROBE_ITEMS_PER_CELL]
    if short:
        sys.exit(f"{len(short)} cell x model rows have an incomplete probe")
    doc = {
        "rule": "forecast_lift = 0.12 - 0.8 * (coverage - 0.70)",
        "zero_crossing": round(ZERO_CROSSING, 4),
        "forecasts": build_forecasts(table),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(canonical(doc))
    print(f"{len(doc['forecasts'])} forecasts -> {OUT}")
    print(f"sha256 {hashlib.sha256(OUT.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
