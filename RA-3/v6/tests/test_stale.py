"""Offline checks of the stale-knowledge set validator and the H8 test on synthetic answers.

    python tests/test_stale.py   (from RA-3/v6)
"""

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import design  # noqa: E402
import stale  # noqa: E402

ITEM = {
    "id": "banking_vn_S01", "cell": "banking_vn",
    "question": "Under Vietnam's 2022 AML Law, when is a suspicious transaction report due?",
    "options": {"A": "Within 24 hours", "B": "Within 3 working days of detection",
                "C": "Within 10 working days", "D": "Within 48 hours of confirmation"},
    "answer": "B", "superseded": "D", "effective": "2023-03-01",
    "source": "Law 14/2022/QH15", "evidence": "3 working days", "status": "draft",
}
MODELS = [m["key"] for m in design.agent_models()]


def synthetic(p_closed: float, p_grounded: float, seed: int = 3) -> list[dict]:
    rng = np.random.default_rng(seed)
    rows = []
    for j in design.JURISDICTIONS:
        for k in range(stale.PER_JURISDICTION):
            cell = design.CELLS[(k % 6) * 2 + (j == "vn")]
            for m in MODELS:
                pick = lambda p: "superseded" if rng.random() < p else ("current" if rng.random() < .8 else "other")
                rows.append({"item_id": f"{cell}_S{k:02d}", "model": m, "cell": cell,
                             "closed": pick(p_closed), "grounded": pick(p_grounded)})
    return rows


class Validate(unittest.TestCase):
    def test_good_item_passes_partial_check(self):
        self.assertEqual(stale.validate([ITEM], complete=False), [])

    def test_evidence_must_be_in_the_ontology_context(self):
        bad = {**ITEM, "evidence": "48 hours of confirmation"}
        self.assertTrue(any("does not state" in p for p in stale.validate([bad], complete=False)))

    def test_answer_and_superseded_differ(self):
        bad = {**ITEM, "superseded": "B"}
        self.assertTrue(stale.validate([bad], complete=False))

    def test_date_window(self):
        bad = {**ITEM, "effective": "2019-07-01"}
        self.assertTrue(any("outside" in p for p in stale.validate([bad], complete=False)))

    def test_complete_check_needs_30_per_country(self):
        self.assertTrue(any("expected 30" in p for p in stale.validate([ITEM])))

    def test_classify(self):
        self.assertEqual(stale.classify(ITEM, "B"), "current")
        self.assertEqual(stale.classify(ITEM, "D"), "superseded")
        self.assertEqual(stale.classify(ITEM, None), "other")


class H8(unittest.TestCase):
    def test_counts(self):
        res = stale.h8(synthetic(.4, .1), n_perm=500)
        self.assertEqual(res["n_items"], 60)
        self.assertEqual(res["n_pairs"], 360)

    def test_detects_repair(self):
        res = stale.h8(synthetic(.4, .1), n_perm=2000)
        self.assertGreater(res["difference"], 0)
        self.assertLess(res["p_one_sided"], .05)

    def test_null_is_not_significant(self):
        res = stale.h8(synthetic(.3, .3), n_perm=2000)
        self.assertGreater(res["p_one_sided"], .05)

    def test_seeded(self):
        rows = synthetic(.3, .2)
        self.assertEqual(stale.h8(rows, n_perm=300), stale.h8(rows, n_perm=300))


if __name__ == "__main__":
    unittest.main()
