# RA-3 v6 inference qualification — 7 November 2026

Local synthetic planning only. This package extends, and preserves, the earlier v0.3 sensitivity package. It does not collect empirical responses, qualify the full protocol, approve a sample expansion, or publish artifacts.

## Reproduce

From this directory, with the parent RA-3 NumPy/SciPy dependencies:

```sh
python -m unittest discover -s . -p 'test_*.py' -v
OPENBLAS_NUM_THREADS=1 python calibrate.py --reps 3000 --seed 20261108 --output results.json
```

Seed 20261108 is an arbitrary fixed integer, not a date of execution. Environment versions and source SHA-256 are recorded. Four industry counts (6, 10, 16, 20), two per-model/cell probe sizes (60, 120), nine scenarios and 3,000 replicates give 216,000 synthetic studies. Outputs are repeatable within the recorded environment. No dataset generated here is an observed RA-3 result.

## Estimand and candidate tests

Each cell is one industry×jurisdiction combination. Average paired MA lift equally over six fixed models and ten tasks/model. Average independent probe accuracy equally over six models. Fit cell mean lift to an intercept, industry fixed effects, two jurisdiction indicators and mean observed coverage minus .55. With I industries there are 3I rows and I+3 coefficients, leaving 2I−3 residual degrees of freedom.

This targets association between **cell-average** knowledge and lift. It does not estimate the within-cell, model-specific slope in v0.3. The change is a proposal and must be accepted explicitly before a study lock. Six model rows inside a cell no longer increase the inferential sample size.

Compare conventional OLS t(2I−3), HC3 covariance with the same t reference, and industry-cluster CR1 covariance with t(I−1). These are candidate frequentist approximations; Monte Carlo screening does not prove universal validity. H2 rejects for a negative upper one-sided 95% bound. Joint H3 requires both jurisdiction 90% intervals inside ±.05. The practical margin remains proposed. All tests are standalone; this package does not simulate H1 gates or the entire confirmatory family.

## Data-generating assumptions

A fresh coverage design is drawn each replicate. Cell-level true coverage has SD .085 (low-overlap scenario .025), jurisdiction offsets 0/−.20/−.07, six fixed model offsets, and clipping to [.12,.94]. Every model/cell has binomial probe noise independent of other probe errors. Model-level probe averages therefore have known simulation variance, estimated from observed proportions for the correction diagnostic.

Mean lift is .20 + beta×(true mean coverage−.55), with beta 0, −.4 or −.8. Only the slope halves in the half-effect scenario; the overall grounding intercept stays .20 because this package assesses standalone H2, not H1 power. Cell outcome SD is .06 plus task-mean noise .11/sqrt(60). Null scenarios add a .10 Vietnam effect. The boundary case adds .05 Vietnam with beta −.8. Oracle uses latent coverage, omitting probe measurement error.

Stress cases: jurisdiction-dependent outcome SD; an industry-shared random jurisdiction slope (dependence not absorbed by a constant industry fixed effect); t(3) errors scaled by .06/sqrt(3) and symmetrically capped at ±.30; and limited coverage overlap. Aggregate differences outside [−1,1] raise an error. These are score-difference surrogates, not item-level or rubric-complete response simulations. No model-class-dependent slopes, missingness, nonlinear response surfaces, data-dependent task eligibility, or systematic judge/probe bias is simulated. The .06 calibration screen is prespecified in the v0.3 draft as a proposed threshold, not a proven scientific standard.

Every scenario uses the same seed for paired comparisons across methods. The five null cases per design are tested at both probe sizes. `screening_gate` passes only if every tested H2-null Wilson upper 95% Monte Carlo bound is ≤ .06. Bounds are pointwise, not simultaneous across scenarios; passing is a limited screen. Power should be interpreted only alongside this calibration and its assumptions. A new independent-seed grid is necessary before selecting a final method based on these exploratory results.

## Measurement error

The diagnostic subtracts tr(M V) from x'Mx, with M projecting off the fixed covariates and V the diagonal estimated binomial-probe variance. It reports a moment-corrected slope only if that denominator is positive. Failure is missing, never zero; median and 5th/95th percentiles are recorded. These percentiles describe the simulation distribution, not a study confidence interval. The ratio can be unstable, and validity assumes independent unbiased probe errors and correctly specified linear effects. There is no qualified corrected interval or equivalence test. No H3 result uses the moment-corrected slope.

## Verification

Four checks compare the slope and standard error with independent partial-regression arithmetic, HC3 with explicit leave-one-out fits, the zero-error correction with OLS, and an unidentified denominator with an explicit missing result. Source/result bindings and preservation of the v0.3 package are recorded in the internal qualification manifest. This is local verification, not external peer review or hosted CI.
