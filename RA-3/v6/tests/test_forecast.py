"""Offline checks of the registered forecasts and the H7 test on synthetic lifts.

    python tests/test_forecast.py   (from RA-3/v6)
"""

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import design  # noqa: E402
import forecast  # noqa: E402

MODELS = [m["key"] for m in design.agent_models()]


def synthetic(slope: float, vn_effect: float = 0.0, seed: int = 1) -> list[dict]:
    """Coverage varies by country, industry and model; lift follows the given slope plus noise."""
    rng = np.random.default_rng(seed)
    ind_off = dict(zip(design.INDUSTRIES, rng.normal(0, 0.08, len(design.INDUSTRIES))))
    points = []
    for cell in design.CELLS:
        vn = design.jurisdiction(cell) == "vn"
        for k, m in enumerate(MODELS):
            cov = float(np.clip((0.50 if vn else 0.75) + ind_off[forecast.industry(cell)]
                                + 0.03 * k + rng.normal(0, 0.03), 0.05, 0.98))
            lift = 0.12 + slope * (cov - 0.70) + vn_effect * vn + rng.normal(0, 0.03)
            points.append({"cell": cell, "model": m, "coverage": round(cov, 4), "lift": float(lift)})
    return points


class ForecastLine(unittest.TestCase):
    def test_line_and_zero_crossing(self):
        self.assertAlmostEqual(forecast.forecast_lift(0.70), 0.12)
        self.assertAlmostEqual(forecast.forecast_lift(0.85), 0.0)
        self.assertAlmostEqual(forecast.ZERO_CROSSING, 0.85)

    def test_forecasts_are_sorted_and_hash_stable(self):
        table = [{"cell": c, "model": m, "coverage": 0.6, "n_items": 90, "jurisdiction": design.jurisdiction(c)}
                 for c in reversed(design.CELLS) for m in MODELS]
        rows = forecast.build_forecasts(table)
        self.assertEqual(len(rows), 72)
        self.assertEqual(rows, sorted(rows, key=lambda r: (r["cell"], r["model"])))
        self.assertEqual(forecast.canonical(rows), forecast.canonical(forecast.build_forecasts(table[::-1])))

    def test_calibration_recovers_a_true_line(self):
        pts = synthetic(-0.8)
        rows = forecast.build_forecasts(pts)
        cal = forecast.calibration(rows, {(p["cell"], p["model"]): p["lift"] for p in pts})
        self.assertAlmostEqual(cal["calibration_slope"], 1.0, delta=0.15)
        self.assertAlmostEqual(cal["observed_zero_crossing"], 0.85, delta=0.03)
        self.assertLess(cal["mean_absolute_error"], 0.05)


class H7(unittest.TestCase):
    def test_holds_72_points_out_once_each(self):
        res = forecast.h7(synthetic(-0.8), n_perm=200)
        self.assertEqual(res["n_held_out"], 72)

    def test_detects_a_within_country_coverage_effect(self):
        res = forecast.h7(synthetic(-0.8), n_perm=2000)
        self.assertGreater(res["mae_gain"], 0)
        self.assertLess(res["p_one_sided"], 0.05)

    def test_does_not_fire_when_only_country_matters(self):
        # Lift differs by country but not by coverage within a country.
        res = forecast.h7(synthetic(0.0, vn_effect=0.15), n_perm=2000)
        self.assertGreater(res["p_one_sided"], 0.05)

    def test_is_seeded(self):
        pts = synthetic(-0.4)
        self.assertEqual(forecast.h7(pts, n_perm=300), forecast.h7(pts, n_perm=300))


if __name__ == "__main__":
    unittest.main()
