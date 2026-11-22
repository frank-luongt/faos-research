"""Offline check that the stage-2 probe tags are complete and resolve in each ontology.

    python tests/test_tags.py   (from RA-3/v6)
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gating  # noqa: E402


class Tags(unittest.TestCase):
    def test_tags_complete_and_valid(self):
        report = gating.tag_report()
        self.assertEqual(report[-1], "tags complete", "\n".join(report))


if __name__ == "__main__":
    unittest.main()
