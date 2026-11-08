"""Offline regressions for measurement errors found in the legacy corpus audit."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from contract import normalize_scores, validate_corpus

ROOT = Path(__file__).resolve().parent


class CorpusContractTests(unittest.TestCase):
    def setUp(self):
        self.corpus = json.loads((ROOT / "corpus.json").read_text())
        self.item = self.corpus["tasks"][0]

    def test_bundled_corpus_is_preparation_only(self):
        report = validate_corpus(self.corpus, ROOT)
        self.assertEqual(report["cells_scoped"], 18)
        self.assertEqual(report["ma_rs_candidate_tasks"], 0)
        self.assertEqual(report["launch_ready_cells"], 0)
        self.assertEqual(report["overlap_check"], "NO_PROBES_YET")

    def test_real_zero_and_unscored_metrics_remain_distinct(self):
        row = normalize_scores(self.item, {"MA": 0.0})
        self.assertEqual(row["MA"]["status"], "observed")
        self.assertEqual(row["MA"]["score"], 0.0)
        for metric in ("TF", "RC", "RS"):
            self.assertEqual(row[metric], {"eligible": False, "score": None, "status": "not_eligible"})

    def test_legacy_zero_fill_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "ineligible"):
            normalize_scores(self.item, {"MA": 1.0, "RS": 0.0})

    def test_missing_judge_score_is_never_defaulted_to_zero(self):
        with self.assertRaisesRegex(ValueError, "missing score"):
            normalize_scores(self.item, {})
        row = normalize_scores(self.item, {}, "judge_missing")
        self.assertIsNone(row["MA"]["score"])
        self.assertEqual(row["MA"]["status"], "judge_missing")

    def test_undefined_denominator_is_explicit(self):
        row = normalize_scores(self.item, {}, "undefined_denominator")
        self.assertIsNone(row["MA"]["score"])
        self.assertEqual(row["MA"]["status"], "undefined_denominator")

    def test_invalid_judge_values_are_rejected(self):
        for score in (True, "0.8", float("nan"), float("inf"), -0.1, 1.1):
            with self.subTest(score=score), self.assertRaises(ValueError):
                normalize_scores(self.item, {"MA": score})
        with self.assertRaisesRegex(ValueError, "Unknown metric"):
            normalize_scores(self.item, {"MA": 1.0, "unexpected": 0.5})

    def test_same_fact_cannot_be_used_as_task_and_probe(self):
        probe = copy.deepcopy(self.item)
        probe["item_id"] = "PROBE-DUPLICATE-FACT"
        self.corpus["probes"].append(probe)
        with self.assertRaisesRegex(ValueError, "reused across"):
            validate_corpus(self.corpus, ROOT)

    def test_reworded_fact_cannot_evade_family_overlap_check(self):
        fact = copy.deepcopy(self.corpus["facts"][0])
        fact.update(fact_id="DIFFERENT-FACT-ID", allowed_use="probe")
        self.corpus["facts"].append(fact)
        probe = copy.deepcopy(self.item)
        probe.update(item_id="REWORDED-PROBE", fact_ids=[fact["fact_id"]], prompt="A differently worded question about the same coverage cap.")
        self.corpus["probes"].append(probe)
        with self.assertRaisesRegex(ValueError, "family overlap"):
            validate_corpus(self.corpus, ROOT)

    def test_wrong_jurisdiction_and_missing_rubric_are_rejected(self):
        self.item["fact_ids"] = [self.corpus["facts"][1]["fact_id"]]
        with self.assertRaisesRegex(ValueError, "cells differ"):
            validate_corpus(self.corpus, ROOT)
        self.item["fact_ids"] = [self.corpus["facts"][0]["fact_id"]]
        self.item["metric_eligibility"]["RS"].update(eligible=True, rubric_id="unsubstantiated")
        with self.assertRaisesRegex(ValueError, "reference and rubric"):
            validate_corpus(self.corpus, ROOT)

    def test_source_note_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for source in self.corpus["sources"]:
                path = root / source["evidence_note_path"]
                path.parent.mkdir(exist_ok=True)
                path.write_bytes((ROOT / source["evidence_note_path"]).read_bytes())
            (root / self.corpus["sources"][0]["evidence_note_path"]).write_text("Changed evidence")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                validate_corpus(self.corpus, root)

    def test_account_splitting_does_not_double_the_cap(self):
        expected = {"banking-US": (300000, 250000, 50000),
                    "banking-VN": (150000000, 125000000, 25000000),
                    "banking-SG": (120000, 100000, 20000)}
        for item in self.corpus["tasks"]:
            reference = item["reference_keys"]["MA"]
            self.assertEqual(tuple(reference[k] for k in ("combined_eligible_balance", "covered_amount", "amount_above_cap")), expected[item["cell_id"]])
            self.assertGreater(sum(min(v, reference["cap"]) for v in reference["inputs"]), reference["covered_amount"])


if __name__ == "__main__":
    unittest.main()
