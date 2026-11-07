# RA-3 v6: offline design sensitivity

**Internal local preparation; not a public release, protocol lock, or empirical study.**

The November 7 protocol draft lives in the internal Foundation-AgenticOS paper directory. This package is local/uncommitted in the public-artifact checkout as requested by the PI's November 1 harness-location decision; its presence does not authorize pushing it or distributing the internal protocol.

Run from this directory with Python 3.11+ and the parent RA-3 requirements:

```sh
python -m unittest discover -s . -p 'test_*.py' -v
python power_analysis.py --seed 20261107 --reps 2000 --output power-results.json
```

NumPy 2.3.5 / SciPy 1.17.0 were used; exact versions and the source SHA-256 are in the result. The output is deterministic in this environment. Reproduction across versions is assessed numerically, not promised bit-for-bit.

`power_analysis.py` implements a candidate aggregate analysis, not a data collection harness. Seven assumption scenarios × two probe sizes × 2,000 replicates = 28,000 synthetic studies. Each has 18 cells × six fixed models with ten paired tasks represented through aggregate noise. The same seed gives the same design and common random numbers across scenarios. This is sensitivity conditional on one synthetic coverage design, not unconditional power over all possible study corpora.

Coverage probabilities vary by jurisdiction, model and a cell random effect, and are fixed across replicates. Observed probes have binomial error. Task-mean paired differences have cell shocks (default SD .06) and bivariate MA/RS noise (individual-task SD .11, correlation .6, reduced by sqrt(10)). The full-effect MA/RS expectation is .20 − .8 × (true coverage − .55); the half-effect case halves intercept and slope. The high-noise case uses cell SD .10. Jurisdiction-boundary cases add +.05 VN or −.05 SG. These numbers are illustrative assumptions, not estimated from raw v5 records. The code rejects impossible aggregate differences instead of silently clipping them. It does not simulate discrete/continuous rubric denominators or missing responses.

H1 is a four-component positive-effect conjunction using cell means. H2/H3 fit OLS with industry/jurisdiction/snapshot fixed effects and observed coverage, CR1 cell-cluster covariance and t(17) reference. H3 requires both VN−US and SG−US 90% intervals strictly within ±.05. No probe-error correction is applied. H4/H5/H6, judge-family allocation effects and human sampling are not simulated. Wilson intervals measure Monte Carlo uncertainty only. Five arithmetic tests include an independent cluster-mean standard-error check and a regression preventing nonsignificance from being mistaken for equivalence.

**Readiness: NEEDS REVISION.** Under the pure-Vietnam zero-slope scenario H1 passes, but H2 rejects too often. The 18-cell candidate inference therefore fails calibration before any interpretation of power. Equivalence is also poorly identified/precisely estimated. Do not describe these outputs as demonstrating that the planned study is sufficiently powered, that the original November 1 simulation was reproduced, or that Inverse PKE was tested on actual models.

Next qualification should vary corpus designs and include industry-shared shocks, realistic rubric data, probe error models, heteroskedasticity and overlap stress. Qualify the inferential method before claiming power. An expanded design or a narrower estimand may be needed; repeated generation is not a substitute for independent cells.
