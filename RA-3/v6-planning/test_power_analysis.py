"""Independent arithmetic checks of consequential planning calculations."""
import unittest
import numpy as np
from scipy.stats import t
from power_analysis import fit_cluster, decide


class PlanningChecks(unittest.TestCase):
    def test_intercept_cluster_se_matches_independent_cell_mean_formula(self):
        # Balanced repeats within cell: CR1 must match SD of cell means / sqrt(G).
        means = np.array([.1, .3, -.2, .4, .15, .05])
        y = np.repeat(means, 4) + np.tile([-.03, -.01, .01, .03], 6)
        b, se = fit_cluster(np.ones((24, 1)), y, np.repeat(np.arange(6), 4))
        self.assertAlmostEqual(b[0], means.mean())
        self.assertAlmostEqual(se[0], means.std(ddof=1)/np.sqrt(6))

    def test_perfect_linear_signal(self):
        x = np.column_stack([np.ones(36), np.arange(36)])
        b, se = fit_cluster(x, x @ np.array([.2, -.01]), np.repeat(np.arange(18), 2))
        np.testing.assert_allclose(b, [.2, -.01], atol=1e-12)
        self.assertLess(max(se), 1e-12)

    def test_nonsignificance_does_not_imply_equivalence(self):
        h2, equivalent = decide(np.array([-.8, 0., 0.]), np.array([.1, .1, .1]), 17, 0, 1, 2, .05)
        self.assertTrue(h2)
        self.assertFalse(equivalent)

    def test_both_jurisdiction_contrasts_required(self):
        self.assertFalse(decide(np.array([-.8, 0., .08]), np.array([.1, .001, .001]), 17, 0, 1, 2, .05)[1])
        self.assertTrue(decide(np.array([-.8, 0., 0.]), np.array([.1, .001, .001]), 17, 0, 1, 2, .05)[1])

    def test_replication_counts(self):
        primary = 6*3*10*3*6
        repeats = primary//10
        self.assertEqual((primary, repeats, primary+repeats), (3240, 324, 3564))
        self.assertEqual(3564 + 2*3564 + 18*6*60, 17172)


if __name__ == '__main__':
    unittest.main()
