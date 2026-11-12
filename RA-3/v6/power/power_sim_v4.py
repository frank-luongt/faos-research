"""RA-3 v6 power simulation, generalised: J jurisdictions x I industries.
Same model as power_sim.py (see its docstring); adds design alternatives
for H3. Coverage = country mean + industry offset + model offset (+.08
frontier) + .03 noise; observed via a binomial probe; lift = .12 +
slope*(cov-.70) + VN effect + .03 cell x model noise + task noise (SD .20
over 10 tasks). H3: within-country permutation of cell coverage, model
fixed effects, VN indicator; VN term tested on cell means (t, df=cells-3).
"""
import sys
import numpy as np

T_CRIT = {7: 2.365, 11: 2.201, 9: 2.262, 13: 2.160, 15: 2.131, 14: 2.145, 21: 2.080, 17: 2.110}
MOD, TASK = 6, 10
VN_IDX = 2
FRONTIER = np.array([1, 1, 1, 0, 0, 0], float)


def run(name, cmeans, n_ind, slope, ind_sd=0.06, mod_sd=0.06, probe_n=30,
        vn_effect=0.0, n_sim=300, seed=1, tasks=TASK):
    rng = np.random.default_rng(seed)
    J = len(cmeans); C = J * n_ind
    country = np.repeat(np.arange(J), n_ind)
    vn = (country == VN_IDX).astype(float)
    blocks = [np.where(country == c)[0] for c in range(J)]
    perms = []
    for _ in range(999):
        p = np.arange(C)
        for b in blocks:
            p[b] = rng.permutation(b)
        perms.append(p)
    M = np.zeros((C * MOD, MOD))
    for m in range(MOD):
        M[m::MOD, m] = 1
    VNcol = np.repeat(vn, MOD)

    def slope_of(cov, yy):
        X = np.column_stack([cov.reshape(-1), VNcol, M])
        return np.linalg.lstsq(X, yy, rcond=None)[0][0]

    tcrit = T_CRIT[C - 3]
    h3 = h3h = 0
    for _ in range(n_sim):
        ind_off = rng.normal(0, ind_sd, C)
        mod_off = rng.normal(0, mod_sd, MOD) + 0.08 * FRONTIER
        cov = np.clip(np.array(cmeans)[country][:, None] + ind_off[:, None]
                      + mod_off[None, :] + rng.normal(0, .03, (C, MOD)), .05, .98)
        y = (0.12 + slope * (cov - .70) + vn_effect * vn[:, None]
             + rng.normal(0, .03, (C, MOD)) + rng.normal(0, .20 / np.sqrt(tasks), (C, MOD)))
        obs = rng.binomial(probe_n, cov) / probe_n
        yy = y.reshape(-1)
        s0 = slope_of(obs, yy)
        null = np.array([slope_of(obs[p], yy) for p in perms])
        p3 = (1 + np.sum(null <= s0)) / 1000
        X = np.column_stack([np.ones(C), obs.mean(1), vn])
        cm = y.mean(1)
        b = np.linalg.lstsq(X, cm, rcond=None)[0]
        r = cm - X @ b
        se = np.sqrt(r @ r / (C - 3) * np.linalg.inv(X.T @ X)[2, 2])
        vn_ns = abs(b[2] / se) < tcrit
        h3 += (p3 < .05) and vn_ns
        h3h += (p3 < .0125) and vn_ns
    print(f"{name:58s} cells={C:2d}  H3={h3/n_sim:4.2f}  H3(Holm)={h3h/n_sim:4.2f}", flush=True)


US, VN = .75, .50
def go(name, cm, n_ind, slope, vn_idx, **kw):
    global VN_IDX; VN_IDX = vn_idx
    run(name, cm, n_ind, slope, **kw)
for slope, tag in ((-0.8, "v5 anchor"), (-0.4, "half effect")):
    go(f"{tag}: US+SG+VN x 6 ind (current)", (US, .70, VN), 6, slope, 2, probe_n=60)
    go(f"{tag}: US+VN x 6 ind, probe 60", (US, VN), 6, slope, 1, probe_n=60)
    go(f"{tag}: US+VN x 6 ind, probe 90", (US, VN), 6, slope, 1, probe_n=90)
    go(f"{tag}: US+VN x 6 ind, probe 60, 15 tasks/cell", (US, VN), 6, slope, 1, probe_n=60, tasks=15)
go("null: slope 0, VN +.15, US+VN x 6, probe 60", (US, VN), 6, 0.0, 1, probe_n=60, vn_effect=.15)
