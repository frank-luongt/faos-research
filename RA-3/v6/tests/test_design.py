"""Offline checks of the v6 design arithmetic and seeded assignments.

    python tests/test_design.py   (from RA-3/v6)
"""

import json
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import design  # noqa: E402
from conditions_v6 import build_prompt  # noqa: E402

LOCK = design.load_lock()
TASKS_BY_CELL = {c: [f"{c}_T{i}" for i in range(1, 11)] for c in design.CELLS}
ALL_TASKS = [t for ts in TASKS_BY_CELL.values() for t in ts]


class DesignArithmetic(unittest.TestCase):
    def test_protocol_counts(self):
        runs = design.run_matrix(ALL_TASKS, LOCK)
        primary = [r for r in runs if r["rep"] == 1]
        self.assertEqual(len(design.CELLS), 12)
        self.assertEqual(len(primary), 2160)  # 120 tasks x 3 conditions x 6 models
        self.assertEqual(len(runs) - len(primary), 216)  # 10% repeats
        self.assertEqual(2 * len(runs), 4752)  # panel judge calls
        self.assertEqual(len(design.CELLS) * design.PROBE_ITEMS_PER_CELL * 6, 6480)

    def test_run_keys_unique_and_repeats_stable(self):
        a = design.run_matrix(ALL_TASKS, LOCK)
        self.assertEqual(len({design.run_key(r) for r in a}), len(a))
        self.assertEqual(a, design.run_matrix(ALL_TASKS, LOCK))

    def test_model_types(self):
        types = Counter(m["type"] for m in design.agent_models(LOCK))
        self.assertEqual(types, {"frontier": 3, "open-weight": 3})


class JudgeRotation(unittest.TestCase):
    def setUp(self):
        self.assign = design.assign_judge_pairs(TASKS_BY_CELL, LOCK)
        self.models = {m["key"]: m for m in design.agent_models(LOCK)}

    def test_no_self_judging(self):
        for (_, model, _), per_task in self.assign.items():
            for pair in per_task.values():
                self.assertNotIn(self.models[model]["family"], pair)
                self.assertEqual(len(set(pair)), 2)

    def test_open_weight_pairs_balanced(self):
        for (_, model, _), per_task in self.assign.items():
            if self.models[model]["type"] != "open-weight":
                continue
            counts = Counter(per_task.values())
            self.assertEqual(len(counts), 3)
            self.assertTrue(set(counts.values()) <= {3, 4}, counts)

    def test_deterministic(self):
        self.assertEqual(self.assign, design.assign_judge_pairs(TASKS_BY_CELL, LOCK))


class Materials(unittest.TestCase):
    def test_written_probe_sets_valid(self):
        import json
        for path in sorted(design.PROBE_DIR.glob("*.json")):
            cell = path.stem
            self.assertIn(cell, design.CELLS)
            with open(path) as f:
                self.assertEqual(design.validate_probe(cell, json.load(f)), [])


class Prompts(unittest.TestCase):
    def test_c2b_never_exceeds_c3_budget(self):
        for t in design.load_v5_tasks_as_v6():
            c3, _ = build_prompt(t, "C3_ontology")
            c2b, meta = build_prompt(t, "C2b_rag_matched")
            self.assertLessEqual(len(c2b[0]["content"]), len(c3[0]["content"]))
            self.assertEqual(meta["budget_chars"] - meta["context_chars"], meta["shortfall_chars"])


class Corrections(unittest.TestCase):
    def test_every_correction_applies_to_unchanged_v5_files(self):
        import corrections
        data = corrections.load()
        with open(design.RA3_DIR / "code" / "tasks.json") as f:
            v5_tasks = {t["id"]: t for t in json.load(f)}
        for tid in data["tasks"]:
            corrections.apply(v5_tasks[tid], corrections.for_task(tid))
        for stem in data["ontologies"]:
            with open(design.ONTOLOGY_DIR / f"{stem}.json") as f:
                corrections.apply(json.load(f), corrections.for_ontology(stem))

    def test_v6_prompts_use_corrected_ontology(self):
        task = next(t for t in design.load_v5_tasks_as_v6() if t["id"] == "banking_vn_T7")
        system = build_prompt(task, "C3_ontology")[0][0]["content"]
        self.assertIn("Law 32/2024", system)
        self.assertNotIn("nd116_aml", system)
        self.assertIn("3 working days", system)

    def test_diff_is_current(self):
        import corrections
        before = corrections.DIFF_FILE.read_text()
        corrections.write_diff()
        self.assertEqual(before, corrections.DIFF_FILE.read_text())


if __name__ == "__main__":
    unittest.main()
