"""Read-only corpus inventory. Locators are not verified regulatory evidence."""
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path('/workspace/Foundation-AgenticOS')
RESEARCH=Path('/workspace/faos-research/RA-3')
OUT=Path(__file__).parent
BP=ROOT/'docs/architecture/ontology-blueprint'
# Conservative planning groups, not a finding of statistical independence.
GROUPS=[
 ('agriculture',['agri-ecosystem','agritech'],['crop-agriculture-ecosystem','agritech ecosystem'], 'Merge overlapping farm-to-fork and precision-agriculture scopes.'),
 ('automotive',['automotive'],['automotive-industry'],'Exclude generic manufacturing and transport operations.'),
 ('aviation',['aviation'],['aviation-industry'],'Exclude airline tasks from hospitality and logistics.'),
 ('banking',['bank','bankvn'],['banking','banking-vn'],'VN overlay is a jurisdiction, not another industry.'),
 ('securities',['investment','capitalmarketsvn'],['capital-markets','capital-markets-vn'],'Merge buy-side/sell-side investment and securities scopes.'),
 ('education',['edutech'],['edutech-industry'],'Define education operators, not generic software products.'),
 ('payments',['fintech'],['fintech'],'Narrow FinTech to payments; exclude banking, wealth and insurance tasks.'),
 ('games',['game'],['game-development'],'Require game-specific facts, not generic software operations.'),
 ('healthcare',['healthcare'],['healthcare'],'Provider scope; do not mix payer/insurance rules.'),
 ('insurance',['insurance','insurancevn'],['insurance','insurance-vn'],'VN overlay is a jurisdiction, not another industry.'),
 ('logistics',['logistic-supplychain'],['logistics-supply-chain'],'Exclude aviation operations and hospitality travel.'),
 ('manufacturing',['manufacturing'],['manufacturing'],'Non-automotive product scope needs an explicit sampling frame.'),
 ('advertising',['martech'],['martech'],'Narrow to advertising services; exclude retail/software tasks.'),
 ('accounting',['profserv'],['professional-services'],'Extract accounting/audit; exclude legal/general management consulting.'),
 ('property',['proptechvn'],['proptech-vn','proptech-asia'],'VN material exists; other countries require authored children.'),
 ('retail',['retail','retailvn'],['retail','retail-vn'],'VN overlay is a jurisdiction, not another industry.'),
 ('cybersecurity',['security'],['cybersecurity-services'],'Require security-service-specific tasks beyond generic IT controls.'),
 ('it_services',['si','software'],['services-integrator','software-product','software-cloud'],'Conservatively merge overlapping IT/SaaS scopes pending task-level review.'),
 ('employment',['talent'],['talent-hr-services'],'Recruitment/staffing operators; exclude generic HR tasks shared everywhere.'),
 ('hospitality',['tth'],['travel-transportation-hospitality'],'Narrow to lodging/hospitality; exclude aviation and freight.'),
]
LEGACY={('payments','US'):'fintech',('insurance','US'):'insurance',('healthcare','US'):'healthcare',('banking','VN'):'banking_vn',('insurance','VN'):'insurance_vn'}

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 tasks=json.loads((RESEARCH/'code/tasks.json').read_text())
 bindings={}; domains=[]; cells=[]; locators=[]
 for name,mods,bps,scope in GROUPS:
  module_paths=[ROOT/'.faos/modules'/('faos-'+m)/'module.yaml' for m in mods]
  blueprints=[BP/(s+'-ontology-blueprint.md') for s in bps]
  for p in module_paths+blueprints:
   if not p.exists():raise FileNotFoundError(p)
   bindings[str(p)]=digest(p)
  urls={'US':set(),'VN':set(),'SG':set()}
  for p in blueprints:
   for line,text in enumerate(p.read_text().splitlines(),1):
    for url in re.findall(r'https?://[^\s<>"\)\]\|]+',text):
     url=url.rstrip('.,;`'); parsed=urlsplit(url); host=parsed.hostname or ''
     jurisdiction='SG' if host.endswith('.gov.sg') else ('VN' if host.endswith('.gov.vn') else ('US' if host.endswith('.gov') else None))
     if jurisdiction:
      urls[jurisdiction].add(url)
      locators.append({'domain':name,'jurisdiction':jurisdiction,'url':url,'file':str(p),'line':line,'root_only':parsed.path in ('','/'),'verification':'NOT_FETCHED_NOT_FACT_VALIDATED'})
  domains.append({'domain':name,'modules':[p.parent.name for p in module_paths],'blueprints':[str(p) for p in blueprints],'scope_proposal':scope,'independence':'UNESTABLISHED'})
  for jurisdiction in ('US','VN','SG'):
   legacy=LEGACY.get((name,jurisdiction)); rows=[x for x in tasks if x['industry']==legacy]
   cells.append({'domain':name,'jurisdiction':jurisdiction,'legacy_set':legacy or '', 'legacy_tasks':len(rows),'explicit_metric_ground_truth':sum(bool(x['ground_truth'].get('metrics')) for x in rows),'legacy_ma_scored_tasks':sum(x['metric_tested'] in ('MA','ALL') for x in rows),'government_url_locators':len(urls[jurisdiction]),'fact_source_validation':'NOT_ESTABLISHED','sixty_probe_items':'NOT_FOUND_IN_REVIEWED_RA3_PACKAGE','expert_competency_and_commitment':'NOT_DOCUMENTED_IN_REVIEWED_RA3_RECORDS','launch_ready':False})
 for p in [RESEARCH/'code/tasks.json',RESEARCH/'code/run_experiment.py',RESEARCH/'code/judge.py']+list((RESEARCH/'ontology_context').glob('*.json')):
  bindings[str(p)]=digest(p)
 report={'status':'INVENTORY_ONLY_NOT_CONTENT_QUALIFICATION','module_directories':len(list((ROOT/'.faos/modules').glob('*/module.yaml'))),'excluded_horizontal_modules':['faos-fleet','faos-scholar'],'candidate_groups':domains,'cells':cells,'government_url_locators':locators,'source_sha256':bindings,'script_sha256':digest(Path(__file__)),'legacy_tasks_by_metric':dict(Counter(t['metric_tested'] for t in tasks)),'scope':'Module descriptors, mapped blueprint files, five RA-3 ontology JSONs, task list and judge dispatch. No primary-source web verification or private expert roster access.'}
 (OUT/'inventory.json').write_text(json.dumps(report,indent=2)+'\n')
 with (OUT/'cell-readiness.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(cells[0]),lineterminator="\n");writer.writeheader();writer.writerows(cells)
 with (OUT/'source-locators.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(locators[0]),lineterminator="\n");writer.writeheader();writer.writerows(locators)
 print(json.dumps({'modules':report['module_directories'],'groups':len(domains),'cells':len(cells),'legacy_tasks':sum(c['legacy_tasks'] for c in cells),'explicit_ma_keys':sum(c['explicit_metric_ground_truth'] for c in cells),'ma_scored_legacy':sum(c['legacy_ma_scored_tasks'] for c in cells),'gov_url_occurrences':len(locators),'gov_url_unique':len({r['url'] for r in locators})},indent=2))

if __name__=='__main__':main()
