"""Independent read-only acceptance audit; never runs accept or creates approval."""
from pathlib import Path
import json,hashlib,subprocess,datetime,copy,re
R=Path('/home/ubuntu/repos/coworld-mtg');P=Path('/home/ubuntu/repos/phase-verifiable-loop');O=Path(__file__).parent;E=O.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
def write(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def normal(case):
 x=copy.deepcopy(case)
 if x.get('origin',{}).get('kind','authored')=='authored':x.pop('origin',None)
 x.setdefault('guards',[])
 for c in x['scenario']['cards']:c.setdefault('tapped',False);c.setdefault('plus_one_counters',0)
 for op in x['scenario']['operations']:
  if op['kind']=='cast':op.setdefault('x',None)
 return x
pre=read(O/'preaudit.json'); C=R/'tmp/verifiable-loop/hushbringer-final-comparison'; B=R/'tmp/verifiable-loop/isolated-baseline-build';D=R/'tmp/verifiable-loop/isolated-candidate-build';K=R/'tmp/verifiable-loop/attributed-baseline-build/worker'
assert (E/'final-committed-worker-run/done').read_text()=='complete\n'
launch=read(E/'final-committed-worker-run/receipt.json')
assert launch.get('finished') and launch['acceptance_executed'] is False and len(launch['commands'])==3
for command in launch['commands']:assert command['exit']==0 and sha(command['log'])==command['log_sha256']
assert not (C/'accepted').exists()
assert not (C/'review-approved.json').exists()
b=read(B/'build.json');d=read(D/'build.json');source=read(E/'hushbringer-v10-citation-fix/frozen-source/source.json')
assert sha(K)==pre['checker_sha256'] and sha(B/'worker')==b['binary_sha256']==pre['baseline_worker_sha256']
assert sha(D/'worker')==d['binary_sha256']==launch['candidate_sha256'] and d['binary_sha256']!=b['binary_sha256']
for key in ['harness_source_files','compiler','build_environment','builder_sha256']:assert d[key]==b[key],key
assert b['harness_source_files']==pre['harness_source_files'] and len(b['harness_source_files'])==39
for folder,record in [(B,b),(D,d)]:
 for name,h in record['harness_source_files'].items():
  assert sha(folder/'source'/('Cargo.lock.input' if name=='Cargo.lock' else name))==h,(folder,name)
 assert sha(folder/'source/Cargo.lock')==record['cargo_lock_sha256']
for name,h in pre['harness_source_files'].items():assert sha(R/name)==h,name
phase=d['phase']; assert phase['kind']=='checkout' and b['phase']['kind']=='pinned'
assert phase['revision']==pre['phase_committed_revision']=='fa0ebfe88db224ebd32624bb96ef033d338c2d8c'
assert phase['base_revision']==b['phase']['revision']=='2dec6c88915db4697706234a7ba2fcedd97b1689' and phase['repository']==b['phase']['repository']
assert phase['worktree_clean'] and phase['dirty_patch_sha256']==hashlib.sha256(b'').hexdigest()
assert set(source)-set(phase['source_files'])=={'.cargo/config.toml'} and len(source)==2051 and len(phase['source_files'])==2050
assert all(source[name]==h for name,h in phase['source_files'].items())
for name,h in source.items():assert sha(P/name)==h,(P,name)
for name,h in phase['source_files'].items():assert sha(D/'phase-source'/name)==h,(D,name)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=P,text=True).strip()==phase['revision']
assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=normal'],cwd=P)
patch=subprocess.check_output(['git','diff','--binary','--full-index',phase['base_revision'],'HEAD','--'],cwd=P)
assert patch== (D/'phase.patch').read_bytes()
assert sha(D/'phase.patch')==phase['patch_sha256'] and patch
assert not (D/'phase-dirty.patch').read_bytes()
plan=read(C/'plan.json');assert plan==pre['plan'] and digest(plan)==pre['frozen_plan_typed_id']
assert sha(R/'tmp/verifiable-loop/hushbringer-acceptance-plan.json')==pre['frozen_plan_raw_sha256']
assert sha(R/'cases/corpus/corpus.json')==pre['corpus_sha256']
cases={c['typed_case_id']:c for c in pre['cases']};expected_ids={plan['case_id'],*plan['regression_case_ids'],*plan['holdout_case_ids']};assert set(cases)==expected_ids
for row in cases.values():assert sha(row['path'])==row['raw_sha256'] and normal(read(row['path']))==row['case']
assert len(plan['regression_case_ids'])==7 and len(plan['holdout_case_ids'])==2 and len(expected_ids)==10

def measure(p,o):
 k=p['kind']
 if k=='life':return o['life'][{'player':0,'opponent':1}[p['seat']]]
 if k=='zone_count':return sum(x['owner']==p['seat'] and x['zone']==p['zone'] and x['name']==p['name'] for x in o['objects'])
 objs={x['object_id']:x for x in o['objects']};x=objs[o['labels'][p['object']]]
 if k=='offered_cast_spell':return p['seat'] in x['cast_spell_offered_to']
 return x[k]

rows=[];receipts={};evidence_files={};commands=[]
logs=O/'verification-logs';logs.mkdir(exist_ok=False)
for label,folder,worker in [('baseline',B,b['binary_sha256']),('candidate',D,d['binary_sha256'])]:
 cmd=[str(K),'case','build-check','--build',str(folder)]
 cp=subprocess.run(cmd,cwd=R,capture_output=True,text=True);(logs/f'{label}-build.log').write_text(cp.stdout+cp.stderr);assert cp.returncode==0
 commands.append(dict(command=cmd,exit=cp.returncode,log_sha256=sha(logs/f'{label}-build.log')))
 campaign=read(C/label/'campaign.json');assert len(campaign)==10 and {x['case_id'] for x in campaign}==expected_ids
 for caseid in sorted(expected_ids):
  f=C/label/caseid;case=normal(read(f/'case.json'));req=read(f/'request.json');rec=read(f/'receipt.json');ex=[read(f/f'execution-{i}.json') for i in range(2)]
  assert case==cases[caseid]['case'] and digest(case)==rec['case_id']==caseid
  assert rec==next(x for x in campaign if x['case_id']==caseid)
  assert req['scenario']==case['scenario'] and set(req)=={'protocol','corpus_path','corpus_sha256','scenario'}
  assert req['corpus_sha256']==rec['corpus_sha256']==sha(f/'corpus.json')==pre['corpus_sha256']
  assert rec['worker_sha256']==worker and rec['checker_sha256']==pre['checker_sha256']
  assert rec['repeatability']=='verified' and ex[0]==ex[1]
  assert rec['evidence_sha256']==[digest(x) for x in ex]
  for x in ex:
   assert x['request_id']==digest(req) and x['binary_sha256']==worker and x['outcome']['kind']=='completed'
   assert x['protocol']==req['protocol']==rec['protocol']=='coworld-improvement-v1'
   assert x['declared_phase_revision']==phase['base_revision']
   assert [s['operation_index'] for s in x['outcome']['steps']]==list(range(len(case['scenario']['operations'])))
   assert all(re.fullmatch('[0-9a-f]{64}',s['state_sha256']) for s in x['outcome']['steps'])
  obs=ex[0]['outcome']['observation'];ids=[o['object_id'] for o in obs['objects']]
  assert ids==sorted(set(ids)) and len(set(obs['labels'].values()))==len(obs['labels'])
  assert set(obs['labels'])=={c['label'] for c in case['scenario']['cards']}
  measures=[];fail=[]
  for role in ['guards','assertions']:
   for a in case[role]:
    actual=measure(a['predicate'],obs);equal=actual==a['predicate']['equals']
    measures.append(dict(role=role,id=a['id'],predicate=a['predicate'],actual=actual,passed=equal))
    if role=='guards':assert equal,(label,caseid,a['id'],actual)
    elif not equal:fail.append(a['id'])
  expected={'kind':'violated','assertion_ids':fail} if fail else {'kind':'satisfied'}
  assert rec['result']==expected
  assert bool(fail)==(label=='baseline' and caseid==plan['case_id'])
  cmd=[str(K),'case','verify','--receipt',str(f/'receipt.json')]
  cp=subprocess.run(cmd,cwd=R,capture_output=True,text=True);lp=logs/f'{label}-{caseid}.log';lp.write_text(cp.stdout+cp.stderr);assert cp.returncode==0
  commands.append(dict(command=cmd,exit=cp.returncode,log_sha256=sha(lp)))
  receipts[(label,caseid)]=rec
  rows.append(dict(worker=label,case_id=caseid,classification=cases[caseid]['classification'],title=case['title'],receipt_id=digest(rec),receipt_raw_sha256=sha(f/'receipt.json'),request_id=digest(req),evidence_ids=rec['evidence_sha256'],steps=len(ex[0]['outcome']['steps']),result=rec['result'],measurements=measures,observation=obs))
 for p in sorted((C/label).rglob('*')):
  if p.is_file():evidence_files[str(p)]=sha(p)
comparison=read(C/'comparison.json');assert comparison['plan_id']==digest(plan) and len(comparison['cases'])==10
assert {x['case_id'] for x in comparison['cases']}==expected_ids
for row in comparison['cases']:
 assert row['title']==cases[row['case_id']]['case']['title']
 for label in ['baseline','candidate']:assert row[label]==receipts[(label,row['case_id'])]['result']
template=read(C/'review-template.json');assert template==dict(plan_id=digest(plan),baseline_receipt_id=digest(receipts[('baseline',plan['case_id'])]),candidate_receipt_id=digest(receipts[('candidate',plan['case_id'])]),reviewer='',rationale='',decision='reject')
command=read(C/'accept-command.json')
expected_command=[str(K),'case','accept','--case',str(C/'baseline'/plan['case_id']/'case.json'),'--plan',str(C/'plan.json'),'--baseline',str(C/'baseline'/plan['case_id']/'receipt.json'),'--candidate',str(C/'candidate'/plan['case_id']/'receipt.json')]
for id in plan['regression_case_ids']+plan['holdout_case_ids']:expected_command.extend(['--gate',str(C/'candidate'/id/'receipt.json')])
expected_command.extend(['--review',str(C/'review-approved.json'),'--baseline-build',str(B),'--candidate-build',str(D),'--output-dir',str(C/'accepted')]);assert command==expected_command
for p in [C/'plan.json',C/'comparison.json',C/'review-template.json',C/'accept-command.json',B/'build.json',B/'worker',D/'build.json',D/'worker',D/'phase.patch',D/'phase-dirty.patch',K,E/'final-committed-worker-run/receipt.json']:
 evidence_files[str(p)]=sha(p)
write(O/'verified-final.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='PASS: final build and all frozen bundles independently verified; approval not yet written',baseline_build=b,candidate_build=d,build_launch_receipt=launch,template=template,case_results=rows,verification_commands=commands,evidence_hashes=evidence_files,phase_files_verified_live=2051,phase_files_verified_build_copy=2050,builder_scope_exclusion='.cargo/config.toml contains aliases and RUST_MIN_STACK; frozen builder runs from copied Coworld workspace, not Phase dependency checkout',harness_files_verified=39,acceptance_executed=False))
print('PASS: exact clean committed source and isolated build; 20 receipt bundles; 40 matching retained executions; all guards; baseline target alone violated; candidate target+7 regression+2 holdout satisfied; approval not yet written')
print('candidate worker SHA256',d['binary_sha256']);print('baseline receipt ID',template['baseline_receipt_id']);print('candidate receipt ID',template['candidate_receipt_id'])
