"""Independent-seed check of 20 industries, 60 probes; selected from earlier design screen."""
import hashlib
import json
from pathlib import Path
from calibrate import run

if __name__=='__main__':
    cases=['iid_null','heteroskedastic_null','industry_correlated_null','heavy_tail_null','low_overlap_null','half']
    results=[run(20261109,5000,20,60,c) for c in cases]
    gate={}
    for method in ['OLS','HC3','industry_CR1']:
        nulls=[r['results'][method]['negative_slope'] for r in results[:-1]]
        alternative=results[-1]['results'][method]['negative_slope']
        gate[method]={'null_screen_pass':all(r['mc95'][1]<=.06 for r in nulls),
                      'worst_null_upper_mc95':max(r['mc95'][1] for r in nulls),
                      'half_effect_power':alternative,
                      'power_lower_mc95_at_least_080':bool(alternative['mc95'][0]>=.80)}
    folder=Path(__file__).parent
    out={'status':'INDEPENDENT_SEED_SYNTHETIC_CHECK_NOT_PROTOCOL_APPROVAL','seed':20261109,'source_sha256':hashlib.sha256((folder/'calibrate.py').read_bytes()).hexdigest(),'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'results':results,'gate':gate}
    (folder/'confirmation.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(gate,indent=2))
