"""Offline checks of stage-2 gating (C3g): the known-entry rule, the gate and the prompt.

    python tests/test_gating.py   (from RA-3/v6)
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import design  # noqa: E402
import gating  # noqa: E402
from conditions_v6 import build_prompt, v5  # noqa: E402

TASK = next(t for t in design.load_tasks() if t["cell"] == "banking_us" and t["category"] == "metric_interpretation")
ONTO = v5._load_ontology("banking_us")
ENTRY = "domain_layer.concepts.camels"


class KnownRule(unittest.TestCase):
    TAGS = {"i1": ENTRY, "i2": ENTRY, "i3": "domain_layer.concepts.lcr", "i4": None}

    def test_two_correct_items_make_an_entry_known(self):
        self.assertEqual(gating.known_entries(self.TAGS, {"i1": True, "i2": True, "i3": True}), {ENTRY})

    def test_one_wrong_item_keeps_the_entry(self):
        self.assertEqual(gating.known_entries(self.TAGS, {"i1": True, "i2": False, "i3": True}), set())

    def test_missing_answer_counts_as_unknown(self):
        self.assertEqual(gating.known_entries(self.TAGS, {"i1": True}), set())

    def test_single_item_entries_are_never_gated(self):
        self.assertNotIn("domain_layer.concepts.lcr", gating.known_entries(self.TAGS, {"i3": True}))


class Gate(unittest.TestCase):
    def test_gate_removes_only_known_entries(self):
        out = gating.gate(ONTO, {ENTRY})
        self.assertNotIn("camels", out["domain_layer"]["concepts"])
        self.assertIn("camels", ONTO["domain_layer"]["concepts"])  # input untouched
        self.assertEqual(set(out["domain_layer"]["concepts"]) | {"camels"}, set(ONTO["domain_layer"]["concepts"]))

    def test_validate_rejects_never_gated_and_unknown_paths(self):
        tags = {"x1": "interaction_layer.handoffs.payments_to_sanctions", "x2": "domain_layer.concepts.nope"}
        problems = gating.validate_tags("banking_us", tags, ["x1", "x2"], ONTO)
        self.assertEqual(len(problems), 2)

    def test_validate_flags_untagged_items(self):
        problems = gating.validate_tags("banking_us", {}, ["a", "b"], ONTO)
        self.assertTrue(any("untagged" in p for p in problems))


class Prompt(unittest.TestCase):
    def test_c3g_with_nothing_known_equals_c3(self):
        c3 = build_prompt(TASK, "C3_ontology")[0][0]["content"]
        c3g = build_prompt(TASK, "C3g_gated", known=set())[0][0]["content"]
        self.assertEqual(c3, c3g)

    def test_c3g_is_shorter_and_restores_the_loader(self):
        c3 = build_prompt(TASK, "C3_ontology")[0][0]["content"]
        c3g, meta = build_prompt(TASK, "C3g_gated", known={ENTRY})
        self.assertLess(len(c3g[0]["content"]), len(c3))
        self.assertNotIn("**camels**", c3g[0]["content"])
        self.assertEqual(meta["gated_entries"], 1)
        self.assertEqual(c3, build_prompt(TASK, "C3_ontology")[0][0]["content"])

    def test_c3g_needs_known(self):
        with self.assertRaises(ValueError):
            build_prompt(TASK, "C3g_gated")


class Stage2Matrix(unittest.TestCase):
    def test_792_runs(self):
        runs = design.stage2_matrix([f"t{i}" for i in range(120)])
        self.assertEqual(len(runs), 792)
        self.assertEqual(len({design.run_key(r) for r in runs}), 792)


if __name__ == "__main__":
    unittest.main()
