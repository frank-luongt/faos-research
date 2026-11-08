import copy
import json
import unittest

from scoring import paired_lift_bounds, score_annotations, score_role
from validate import ROOT, common_prompt, validate


def ref(identifier, verdict="correct"):
    return {"reference_id": identifier, "verdict": verdict, "evidence": "Synthetic test annotation; not a model output."}


class BatchTwoTests(unittest.TestCase):
    def setUp(self):
        self.corpus = json.loads((ROOT / "corpus.json").read_text())
        self.ids = ["cap", "total", "covered", "above_cap"]

    def test_snapshot_counts_revisions_once(self):
        result = validate(self.corpus)
        self.assertEqual(result["draft_tasks"], 6)
        self.assertEqual(result["revision_count"], 3)
        self.assertEqual(result["ma_rs_candidate_tasks"], 3)
        self.assertEqual(result["independently_reviewed_tasks"], 0)

    def test_omission_is_visible_without_changing_precision(self):
        coverage = dict.fromkeys(self.ids, "omitted")
        coverage["cap"] = "correct"
        result = score_annotations([ref("cap")], coverage, self.ids)
        self.assertEqual(result["precision"], 1)
        self.assertEqual(result["completeness"], 0.25)
        with self.assertRaisesRegex(ValueError, "full requested denominator"):
            score_annotations([ref("cap")], {"cap": "correct"}, self.ids)

    def test_incorrect_extraneous_claim_reduces_precision(self):
        result = score_annotations([ref("cap"), ref("fabricated_sla", "incorrect")],
                                   {"cap": "correct"}, ["cap"])
        self.assertEqual(result["precision"], 0.5)
        self.assertEqual(result["completeness"], 1)

    def test_abstention_differs_from_transport_failure(self):
        abstain = score_annotations([], dict.fromkeys(self.ids, "omitted"), self.ids, "abstained")
        failed = score_annotations([], dict.fromkeys(self.ids, "pending"), self.ids, "generation_failed")
        self.assertIsNone(abstain["precision"])
        self.assertEqual(abstain["precision_status"], "undefined_denominator")
        self.assertEqual(abstain["completeness"], 0)
        self.assertIsNone(failed["completeness"])
        self.assertEqual(failed["precision_status"], "generation_failed")

    def test_duplicate_pending_and_contradictory_annotations(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            score_annotations([ref("cap"), ref("cap")], {"cap": "correct"}, ["cap"])
        result = score_annotations([ref("cap", "pending")], {"cap": "pending"}, ["cap"])
        self.assertIsNone(result["precision"])
        self.assertIsNone(result["completeness"])
        with self.assertRaisesRegex(ValueError, "without any reference"):
            score_annotations([], {"cap": "correct"}, ["cap"])
        with self.assertRaisesRegex(ValueError, "Transport failure"):
            score_annotations([ref("cap")], {"cap": "correct"}, ["cap"], "generation_failed")

    def test_rs_uses_all_three_dimensions(self):
        ratings = {"decision_pattern": 1, "metric_alignment": 0.5, "communication_style": 0}
        self.assertEqual(score_role(ratings)["score"], 0.5)
        ratings["communication_style"] = None
        self.assertIsNone(score_role(ratings)["score"])
        del ratings["communication_style"]
        with self.assertRaisesRegex(ValueError, "three RS"):
            score_role(ratings)

    def test_missing_outcome_keeps_full_support_bounds(self):
        self.assertEqual(paired_lift_bounds(None, None), {"lower": -1, "upper": 1, "status": "support_bound"})
        bounds = paired_lift_bounds(0.4, None)
        self.assertAlmostEqual(bounds["lower"], -0.4)
        self.assertAlmostEqual(bounds["upper"], 0.6)
        point = paired_lift_bounds(0.4, 0.7)
        self.assertAlmostEqual(point["lower"], 0.3)
        self.assertEqual(point["lower"], point["upper"])
        for invalid in (True, float("nan"), 2):
            with self.assertRaises(ValueError):
                paired_lift_bounds(invalid, 0.5)

    def test_role_context_is_explicit_and_identical(self):
        tasks = [t for t in self.corpus["tasks"] if t["cell_id"].startswith("banking")]
        self.assertEqual(len({t["common_context"] for t in tasks}), 1)
        for task in tasks:
            self.assertIn(task["common_context"], common_prompt(task))
        tasks[0]["common_context"] = "Condition-specific role instructions"
        with self.assertRaisesRegex(ValueError, "Common role context"):
            validate(self.corpus)

    def test_fictional_kpis_cannot_be_relabelled_as_law(self):
        self.corpus["scenario_policies"][0]["status"] = "REGULATORY_REQUIREMENT"
        with self.assertRaisesRegex(ValueError, "provenance"):
            validate(self.corpus)

    def test_vietnam_task_has_no_invented_numeric_key(self):
        task = next(t for t in self.corpus["tasks"] if t["cell_id"] == "healthcare-VN")
        self.assertFalse(task["metric_eligibility"]["MA"]["eligible"])
        self.assertNotIn("MA", task["reference_keys"])
        self.assertEqual(task["required_numeric_ids"], [])
        task["required_numeric_ids"] = ["deadline"]
        with self.assertRaisesRegex(ValueError, "numeric references"):
            validate(self.corpus)

    def test_numeric_completion_and_notification_keys_are_distinct(self):
        tasks = {t["cell_id"]: t for t in self.corpus["tasks"]}
        self.assertEqual(tasks["healthcare-US"]["reference_keys"]["MA"],
                         {"initial_calendar_days": 30, "maximum_additional_calendar_days": 30})
        self.assertEqual(tasks["healthcare-SG"]["reference_keys"]["MA"], {"written_update_trigger_days": 30})

    def test_bank_original_and_revision_cannot_both_be_active(self):
        original = copy.deepcopy(self.corpus["tasks"][0])
        original["item_id"] = original.pop("supersedes_item_id")
        self.corpus["tasks"].append(original)
        with self.assertRaisesRegex(ValueError, "alongside original"):
            validate(self.corpus)


if __name__ == "__main__":
    unittest.main()
