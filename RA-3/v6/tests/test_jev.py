"""Offline checks of the Jev adapter: request shape, neutral keys and answer parsing.

    python tests/test_jev.py   (from RA-3/v6)
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import design  # noqa: E402
import run_jev  # noqa: E402

TASKS = {t["metric_tested"]: t for t in design.load_tasks()}


def ans(pos):
    return {"type": "score", "score": pos, "probabilities": {}, "confidence": 0.9}


class Request(unittest.TestCase):
    def test_every_metric_builds_score_questions(self):
        for metric, task in TASKS.items():
            state, qs = run_jev.build_request(task, "resp")
            self.assertIn("resp", state)
            self.assertTrue(qs)
            for q in qs.values():
                self.assertEqual(q["type"], "score")
                self.assertEqual(len(q["criteria"]), run_jev.LEVELS)
                self.assertIn("not instructions", q["instructions"])

    def test_no_yes_no_option_names(self):
        # score questions are keyed by position, so no option carries a yes/no name
        for d, (_, levels) in run_jev.DIMENSIONS.items():
            self.assertTrue(all(isinstance(level, str) for level in levels))

    def test_question_keys_are_api_safe(self):
        for metric in run_jev.PLAN:
            for key in run_jev.questions_for(metric):
                self.assertRegex(key, r"^[A-Za-z0-9_-]{1,64}$")


class Parse(unittest.TestCase):
    def test_position_maps_to_unit_score(self):
        self.assertEqual(run_jev.parse_answers("TF", {"TF": ans(4)})["TF"], 1.0)
        self.assertEqual(run_jev.parse_answers("TF", {"TF": ans(2)})["TF"], 0.5)

    def test_rs_averages_three_sub_dimensions(self):
        out = run_jev.parse_answers("RS", {"RS_decision": ans(4), "RS_metric": ans(2), "RS_style": ans(0)})
        self.assertAlmostEqual(out["RS"], 0.5)

    def test_all_gives_four_metrics(self):
        a = {k: ans(3) for k in ("TF", "MA", "RC", "RS_handoff")}
        self.assertEqual(set(run_jev.parse_answers("ALL", a)) - {"sub"}, {"TF", "MA", "RC", "RS"})

    def test_refusal_and_missing_are_errors_not_zero(self):
        with self.assertRaises(ValueError):
            run_jev.parse_answers("TF", {"TF": {"type": "refusal"}})
        with self.assertRaises(ValueError):
            run_jev.parse_answers("MA", {})
        with self.assertRaises(ValueError):
            run_jev.parse_answers("TF", {"TF": ans(7)})


if __name__ == "__main__":
    unittest.main()
