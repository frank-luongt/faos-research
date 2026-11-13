"""RA-3 v6 power simulation v3: H3 with an equivalence criterion.

Same generative model as power_sim_v2.py (18 cells, 6 models, 60-item probe,
v5-anchored slope, within-country permutation for the coverage slope).
H3 supported if (a) within-country permutation p < .05 for coverage slope
AND (b) the Vietnam term is shown equivalent to zero: its 90% CI (TOST,
alpha .05, t df = cells-3) lies inside +/- margin. Inconclusive otherwise.
Vietnam term from cell means: mean lift ~ 1 + coverage + VN.
"""
import numpy as np
MOD, TASK = 6, 10
FRONTIER = np.array([1, 1, 1, 0, 0, 0], float)
T90 = {15: 1.753, 13: 1.771, 9: 1.833}

def run(name, cmeans, n_ind, slope, margin, probe_n=60, vn_effect=0.0,
        ind_sd=.06, mod_sd=.06, task_sd=.20, n_sim=300, seed=3):
    rng = np.random.default_rng(seed)
    J = len(cmeans); C = J * n_ind
    country = np.repeat(np.arange(J), n_ind); vn = (country == 2).astype(float)
    blocks = [np.where(country == c)[0] for c in range(J)]
    perms = []
    for _ in range(999):
        p = np.arange(C)
        for b in blocks: p[b] = rng.permutation(b)
        perms.append(p)
    M = np.zeros((C * MOD, MOD))
    for m in range(MOD): M[m::MOD, m] = 1
    VNcol = np.repeat(vn, MOD)
    def slope_of(cov, yy):
        X = np.column_stack([cov.reshape(-1), VNcol, M])
        return np.linalg.lstsq(X, yy, rcond=None)[0][0]
    t90 = T90[C - 3]; sup = inc = 0; hw = []
    for _ in range(n_sim):
        ind_off = rng.normal(0, ind_sd, C)
        mod_off = rng.normal(0, mod_sd, MOD) + .08 * FRONTIER
        cov = np.clip(np.array(cmeans)[country][:, None] + ind_off[:, None] + mod_off[None, :]
                      + rng.normal(0, .03, (C, MOD)), .05, .98)
        y = (.12 + slope * (cov - .70) + vn_effect * vn[:, None] + rng.normal(0, .03, (C, MOD))
             + rng.normal(0, task_sd / np.sqrt(TASK), (C, MOD)))
        obs = rng.binomial(probe_n, cov) / probe_n; yy = y.reshape(-1)
        s0 = slope_of(obs, yy)
        p3 = (1 + np.sum(np.array([slope_of(obs[p], yy) for p in perms]) <= s0)) / 1000
        X = np.column_stack([np.ones(C), obs.mean(1), vn]); cm = y.mean(1)
        b = np.linalg.lstsq(X, cm, rcond=None)[0]; r = cm - X @ b
        se = np.sqrt(r @ r / (C - 3) * np.linalg.inv(X.T @ X)[2, 2])
        lo, hi = b[2] - t90 * se, b[2] + t90 * se; hw.append(t90 * se)
        eq = (lo > -margin) and (hi < margin)
        if p3 < .05 and eq: sup += 1
        elif p3 < .05: inc += 1
    print(f"{name:55s} supported={sup/n_sim:4.2f} inconclusive={inc/n_sim:4.2f} CI half-width~{np.median(hw):.3f}", flush=True)

US, SG, VN = .75, .70, .50
for m in (.05, .08, .10):
    run(f"v5 anchor, margin {m}", (US, SG, VN), 6, -0.8, m)
    run(f"half effect, margin {m}", (US, SG, VN), 6, -0.4, m)
run("false-support check: slope -0.4 + true VN effect +.10, margin .08", (US, SG, VN), 6, -0.4, .08, vn_effect=.10)
run("false-support check: slope -0.4 + true VN effect +.10, margin .10", (US, SG, VN), 6, -0.4, .10, vn_effect=.10)
