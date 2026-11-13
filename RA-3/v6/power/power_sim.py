"""RA-3 v6 power simulation for H2/H3 (pre-lock).

Design: 4 industries x 3 jurisdictions (US, SG, VN) = 12 cells; 6 models
(3 frontier, 3 open-weight); 10 tasks per cell; 1 run per condition.
Outcome per task x model: lift = C3 - C1.

Effect sizes anchored on v5 (arXiv 2604.00555 v5, Table industry):
  EN C1 ~ .67, lift ~ .12; VN C1 ~ .46, lift ~ .285
  => slope of lift on baseline knowledge ~ -0.8 (used as the v5 anchor).
Coverage here is the probe accuracy (0..1), modelled as
  country mean + industry offset + model offset + cell x model noise.

H2: coverage slope < 0, permutation shuffling the 12 cells' coverage
    vectors (all models move together).
H3: same slope with a Vietnam indicator in the model; permutation within
    country (preserves the VN-coverage association). Supported if the
    slope is significant (one-sided .05; Holm worst case .0125 also
    reported) AND the VN term is not significant.
"""
import itertools
import numpy as np

rng = np.random.default_rng(20261101)
IND, JUR, MOD, TASK = 4, 3, 6, 10
COUNTRY = np.repeat(np.arange(JUR), IND)  # cell -> country (0 US,1 SG,2 VN)
VN = (COUNTRY == 2).astype(float)
FRONTIER = np.array([1, 1, 1, 0, 0, 0], float)

# all within-country permutations of the 12 cells (4!^3 = 13824); sample 999
perms_within = []
blocks = [np.where(COUNTRY == c)[0] for c in range(JUR)]
for _ in range(999):
    p = np.arange(12)
    for b in blocks:
        p[b] = rng.permutation(b)
    perms_within.append(p)
perms_within = np.array(perms_within)
perms_all = np.array([rng.permutation(12) for _ in range(999)])


def ols_slope(y, X):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta


def design(cov, with_vn):
    # rows: cell x model (72); model fixed effects absorb model-level shifts
    n = 12 * MOD
    cols = [cov.reshape(n)]
    if with_vn:
        cols.append(np.repeat(VN, MOD))
    M = np.zeros((n, MOD))
    for m in range(MOD):
        M[m::MOD, m] = 1
    return np.column_stack(cols + [M])


def simulate(slope, vn_effect, cmeans, ind_sd, mod_sd, task_sd, cm_sd, probe_n=30):
    ind_off = rng.normal(0, ind_sd, 12)
    mod_off = rng.normal(0, mod_sd, MOD) + 0.08 * FRONTIER  # frontier knows more
    cov = (np.array(cmeans)[COUNTRY][:, None] + ind_off[:, None]
           + mod_off[None, :] + rng.normal(0, 0.03, (12, MOD)))
    cov = np.clip(cov, 0.05, 0.98)
    mean_lift = (0.12 + slope * (cov - 0.70) + vn_effect * VN[:, None]
                 + rng.normal(0, cm_sd, (12, MOD)))
    y = mean_lift + rng.normal(0, task_sd / np.sqrt(TASK), (12, MOD))
    observed = rng.binomial(probe_n, cov) / probe_n  # probe measurement error
    return observed, y


def perm_p(cov, y, perms, with_vn):
    yy = y.reshape(-1)
    obs = ols_slope(yy, design(cov, with_vn))
    null = np.array([ols_slope(yy, design(cov[p], with_vn))[0] for p in perms])
    p_slope = (1 + np.sum(null <= obs[0])) / (1 + len(perms))
    return obs, p_slope


def vn_p(cov, y):
    # VN term significance: parametric t on 12 cell means (conservative)
    cm = y.mean(1)
    cc = cov.mean(1)
    X = np.column_stack([np.ones(12), cc, VN])
    b, res, *_ = np.linalg.lstsq(X, cm, rcond=None)
    resid = cm - X @ b
    s2 = resid @ resid / (12 - 3)
    se = np.sqrt(s2 * np.linalg.inv(X.T @ X)[2, 2])
    t = b[2] / se
    return 0.0 if abs(t) >= 2.262 else 1.0  # t crit, df=9, two-sided .05


def run(name, n_sim=300, **kw):
    h2 = h3 = h3h = 0
    for _ in range(n_sim):
        cov, y = simulate(**kw)
        _, p2 = perm_p(cov, y, perms_all, False)
        _, p3 = perm_p(cov, y, perms_within, True)
        vp = vn_p(cov, y)
        h2 += p2 < 0.05
        h3 += (p3 < 0.05) and (vp >= 0.05)
        h3h += (p3 < 0.0125) and (vp >= 0.05)
    print(f"{name:52s} H2={h2/n_sim:5.2f}  H3={h3/n_sim:5.2f}  H3(Holm .0125)={h3h/n_sim:5.2f}")


base = dict(vn_effect=0.0, cmeans=(0.75, 0.70, 0.50), task_sd=0.20, cm_sd=0.03)
print("Power (share of 300 simulated studies), 999 permutations each; probe noise included\n")
run("A v5 anchor: slope -0.8, spread .06/.06, probe 30", slope=-0.8, ind_sd=0.06, mod_sd=0.06, **base)
run("B half effect: slope -0.4, spread .06/.06, probe 30", slope=-0.4, ind_sd=0.06, mod_sd=0.06, **base)
run("C v5 anchor, low spread .03/.03, probe 30", slope=-0.8, ind_sd=0.03, mod_sd=0.03, **base)
run("D half effect, low spread .03/.03, probe 30", slope=-0.4, ind_sd=0.03, mod_sd=0.03, **base)
run("E v5 anchor, SG = US coverage, probe 30", slope=-0.8, ind_sd=0.06, mod_sd=0.06, **{**base, "cmeans": (0.75, 0.75, 0.50)})
run("F half effect, spread .06/.06, probe 60", slope=-0.4, ind_sd=0.06, mod_sd=0.06, probe_n=60, **base)
run("G half effect, low spread .03/.03, probe 60", slope=-0.4, ind_sd=0.03, mod_sd=0.03, probe_n=60, **base)
run("N null: slope 0, VN effect +.15, probe 30", slope=0.0, ind_sd=0.06, mod_sd=0.06, **{**base, "vn_effect": 0.15})
