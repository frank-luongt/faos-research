"""Offline design sensitivity, not empirical data or reproduction of the Nov 1 simulation."""
import argparse
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import scipy
from scipy.stats import t, norm


def fit_cluster(x, y, clusters):
    """OLS CR1 covariance; small-cluster t reference is provisional, not exact."""
    bread = np.linalg.inv(x.T @ x)
    coef = bread @ x.T @ y
    residual = y - x @ coef
    scores = np.array([x[clusters == c].T @ residual[clusters == c]
                       for c in np.unique(clusters)])
    n, k = x.shape
    g = len(scores)
    cov = bread @ scores.T @ scores @ bread * (g / (g - 1)) * ((n - 1) / (n - k))
    return coef, np.sqrt(np.maximum(0, np.diag(cov)))


def decide(coef, se, df, slope_index, vn_index, sg_index, margin):
    critical = t.ppf(.95, df)
    h2 = coef[slope_index] + critical * se[slope_index] < 0
    h3 = all(abs(coef[i]) + critical * se[i] < margin for i in (vn_index, sg_index))
    return bool(h2), bool(h3)


def simulate(seed, reps, probe_items, scenario):
    rng = np.random.default_rng(seed)
    cell = np.repeat(np.arange(18), 6)
    jurisdiction = cell % 3
    industry = cell // 3
    model = np.tile(np.arange(6), 18)
    # A fixed design distribution, NOT measured model knowledge.
    cell_knowledge = rng.normal(0, .085, 18)
    coverage = np.clip(.67 + np.choose(jurisdiction, [0., -.20, -.07])
                       + np.choose(model, [.08, .06, .04, -.03, -.05, -.07])
                       + cell_knowledge[cell], .12, .94)
    # fixed industry, jurisdiction, model effects; reference US, industry 0, model 0
    fixed = np.column_stack([np.ones(108), *(industry == i for i in range(1, 6)),
                             jurisdiction == 1, jurisdiction == 2,
                             *(model == m for m in range(1, 6))]).astype(float)
    # coverage column appended: VN=6, SG=7, coverage=13
    rates = dict(h1=0, h2=0, h3_equivalence=0, full_sequence=0)
    bias = []
    for _ in range(reps):
        measured = rng.binomial(probe_items, coverage) / probe_items
        measured -= .55
        x = np.column_stack([fixed, measured])
        shared = rng.normal(0, scenario.get('cluster_sd', .06), 18)[cell]
        # Mean paired differences from 10 tasks, 2 metrics; bivariate noise.
        noise = rng.multivariate_normal([0, 0], [[.0121, .00726], [.00726, .0121]], 108) / np.sqrt(10)
        mean = scenario.get('lift', .20) + scenario['slope'] * (coverage - .55)
        mean += scenario.get('vn', 0.) * (jurisdiction == 1)
        mean += scenario.get('sg', 0.) * (jurisdiction == 2)
        y = mean[:, None] + shared[:, None] + noise
        # Simulate paired DIFFERENCES directly; no clipping-induced slope.
        if np.max(np.abs(y)) > 1:
            raise ValueError('DGP produced an impossible paired difference; revise assumptions')
        # H1: conjunction of positive MA/RS effects in each model class.
        h1 = True
        for group in (model < 3, model >= 3):
            for metric in range(2):
                averages = np.array([y[group & (cell == c), metric].mean() for c in range(18)])
                h1 &= averages.mean() - t.ppf(.95, 17) * averages.std(ddof=1) / np.sqrt(18) > 0
        coef, se = fit_cluster(x, y[:, 0], cell)
        h2, equivalent = decide(coef, se, 17, 13, 6, 7, .05)
        rates['h1'] += bool(h1)
        rates['h2'] += h2
        rates['h3_equivalence'] += equivalent
        rates['full_sequence'] += bool(h1 and h2 and equivalent)
        bias.append(float(coef[13]))
    # Wilson intervals quantify Monte Carlo uncertainty, not study-effect uncertainty.
    out = {}
    z = norm.ppf(.975)
    for key, count in rates.items():
        p = count / reps
        center = (p + z*z/(2*reps)) / (1 + z*z/reps)
        half = z*np.sqrt(p*(1-p)/reps + z*z/(4*reps*reps))/(1+z*z/reps)
        out[key] = {'count': count, 'rate': p, 'mc_95ci': [center-half, center+half]}
    return {'assumptions': scenario, 'probe_items': probe_items, 'reps': reps,
            'mean_estimated_slope': float(np.mean(bias)), 'tests': out}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reps', type=int, default=2000)
    parser.add_argument('--seed', type=int, default=20261107)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.reps < 100:
        parser.error('use at least 100 replicates')
    scenarios = {
        'coverage_full': {'slope': -.8},
        'coverage_half': {'slope': -.4, 'lift': .10},
        'pure_vietnam_null_slope': {'slope': 0., 'vn': .10},
        'zero_grounding': {'slope': 0., 'lift': 0.},
        'equivalence_boundary_vn': {'slope': -.8, 'vn': .05},
        'equivalence_boundary_sg': {'slope': -.8, 'sg': -.05},
        'coverage_half_high_cluster_noise': {'slope': -.4, 'lift': .10, 'cluster_sd': .10},
    }
    results = {f'{name}_probe{probe}': simulate(args.seed, args.reps, probe, s)
               for i, (name, s) in enumerate(scenarios.items()) for probe in (30, 60)}
    report = {'status': 'SYNTHETIC_PLANNING_ONLY_NOT_A_LOCK', 'seed': args.seed,
              'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__},
              'unit': '18 industry-jurisdiction cells; six fixed model snapshots; ten tasks/cell',
              'limitations': ['Direct Gaussian paired-difference DGP, not rubric-item simulation',
                             'CR1 t(17) is approximate with only 18 clusters',
                             'Probe error is not corrected; attenuation is retained',
                             'Calibration scenarios cannot prove error control for all null configurations',
                             'H4/H5/H6 and task-level fitting are not powered here',
                             'Does not reproduce the unavailable November 1 simulation'],
              'results': results}
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: {j: round(v['rate'], 3) for j, v in r['tests'].items()} for k,r in results.items()}, indent=2))


if __name__ == '__main__':
    main()
