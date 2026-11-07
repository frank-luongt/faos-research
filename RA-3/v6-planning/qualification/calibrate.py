"""Synthetic qualification of cell-mean inference; no live model calls."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import scipy
from scipy.stats import t, norm


def design(industries):
    industry = np.repeat(np.arange(industries), 3)
    country = np.tile(np.arange(3), industries)
    w = np.column_stack([np.ones(len(industry)), *(industry == i for i in range(1, industries)), country == 1, country == 2]).astype(float)
    return industry, country, w


def estimates(w, x, y, industry):
    a = np.column_stack([w, x-.55])
    inv = np.linalg.inv(a.T @ a)
    b = inv @ a.T @ y
    residual = y - a @ b
    n, k = a.shape
    leverage = np.einsum('ij,jk,ik->i', a, inv, a)
    influence = a @ inv
    classic = np.sqrt(np.diag(inv)*np.dot(residual,residual)/(n-k))
    hc3 = np.sqrt(np.sum((influence*(residual/(1-leverage))[:,None])**2, axis=0))
    scores = np.array([influence[industry == g].T @ residual[industry == g] for g in np.unique(industry)])
    g=len(scores)
    cr1 = np.sqrt(np.sum(scores**2, axis=0)*g/(g-1)*(n-1)/(n-k))
    return b, {'OLS':(classic,n-k), 'HC3':(hc3,n-k), 'industry_CR1':(cr1,g-1)}


def corrected_slope(w, x, y, variance):
    """Moment correction diagnostic only, assumes independent unbiased probe errors."""
    m=np.eye(len(x))-w@np.linalg.solve(w.T@w,w.T)
    denominator=x@m@x-np.dot(np.diag(m),variance)
    if denominator <= 1e-10:
        return None
    return float((x@m@y)/denominator)


def wilson(count,n):
    z=norm.ppf(.975); p=count/n
    center=(p+z*z/(2*n))/(1+z*z/n)
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return {'count':count,'rate':p,'mc95':[max(0.,center-half),min(1.,center+half)]}


def run(seed,reps,industries,probe,case):
    rng=np.random.default_rng(seed)
    ind,country,w=design(industries); n=len(ind)
    names=['OLS','HC3','industry_CR1']
    counts={name:{'negative_slope':0,'joint_equivalence':0} for name in names}
    slopes=[]; corrected=[]; failed=0
    for _ in range(reps):
        # New coverage design each replicate: unconditional design sensitivity.
        spread=.025 if case=='low_overlap_null' else .085
        p=np.clip(.67+np.choose(country,[0.,-.20,-.07])[:,None]+np.array([.08,.06,.04,-.03,-.05,-.07])[None,:]+rng.normal(0,spread,(n,1)),.12,.94)
        phat=rng.binomial(probe,p)/probe
        x=p.mean(axis=1) if case=='oracle_full' else phat.mean(axis=1)
        beta= -.8 if case in ('full','oracle_full','boundary_vn') else (-.4 if case=='half' else 0.)
        residual=rng.normal(0,.06,n)
        if case=='heteroskedastic_null':
            residual *= np.choose(country,[.4,2.,1.])
        if case=='industry_correlated_null':
            residual += rng.normal(0,.08,industries)[ind]*np.choose(country,[-1.,0.,1.])
        if case=='heavy_tail_null':
            residual=np.clip(rng.standard_t(3,n)*.06/np.sqrt(3), -.30, .30)
        vn=.05 if case=='boundary_vn' else (.10 if beta==0 else 0.)
        y=.20+beta*(p.mean(axis=1)-.55)+vn*(country==1)+residual+rng.normal(0,.11/np.sqrt(60),n)
        if np.max(np.abs(y)) > 1:
            raise ValueError('Impossible paired score difference under this DGP')
        b, methods=estimates(w,x,y,ind)
        for name,(se,df) in methods.items():
            critical=t.ppf(.95,df)
            counts[name]['negative_slope']+=int(b[-1]+critical*se[-1]<0)
            counts[name]['joint_equivalence']+=int(all(abs(b[j])+critical*se[j]<.05 for j in (industries,industries+1)))
        slopes.append(float(b[-1]))
        variance=np.zeros(n) if case=='oracle_full' else (phat*(1-phat)/(probe-1)).sum(axis=1)/36
        cb=corrected_slope(w,x,y,variance)
        if cb is None: failed+=1
        else: corrected.append(cb)
    return {'industries':industries,'cells':n,'probe_items_per_model_cell':probe,'scenario':case,'replicates':reps,
            'true_slope':beta,'true_vn_contrast':vn,'results':{name:{k:wilson(c,reps) for k,c in rows.items()} for name,rows in counts.items()},
            'naive_slope_mean':float(np.mean(slopes)),
            'moment_correction':{'valid':len(corrected),'nonpositive_denominator':failed,'median':float(np.median(corrected)) if corrected else None,'quantiles_05_95':np.quantile(corrected,[.05,.95]).tolist() if corrected else None,'inferential_status':'DIAGNOSTIC_ONLY_NO_CONFIDENCE_INTERVAL'}}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--reps',type=int,default=3000)
    parser.add_argument('--seed',type=int,default=20261108)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.reps<100: parser.error('At least 100 replicates required')
    cases=['iid_null','heteroskedastic_null','industry_correlated_null','heavy_tail_null','low_overlap_null','full','half','oracle_full','boundary_vn']
    grid=[(i,p,c) for i in (6,10,16,20) for p in (60,120) for c in cases]
    results=[]
    for i,p,c in grid:
        results.append(run(args.seed,args.reps,i,p,c))
        print(i,p,c,flush=True)
    gate={}
    for i in (6,10,16,20):
        for name in ('OLS','HC3','industry_CR1'):
            nulls=[r for r in results if r['industries']==i and r['scenario'].endswith('_null')]
            gate[f'{i}_industries_{name}']={'tested_nulls':len(nulls),'passes_upper_mc95_at_most_006':all(r['results'][name]['negative_slope']['mc95'][1]<=.06 for r in nulls),'worst_upper_mc95':max(r['results'][name]['negative_slope']['mc95'][1] for r in nulls)}
    report={'status':'SYNTHETIC_QUALIFICATION_ONLY','seed':args.seed,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'numpy':np.__version__,'scipy':scipy.__version__,'results':results,'screening_gate':gate,'scope':'Aggregate fixed-six-model MA association; does not qualify full H1-H6 sequence, causal identification, judge/human calibration, or latent-coverage equivalence.'}
    args.output.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__': main()
