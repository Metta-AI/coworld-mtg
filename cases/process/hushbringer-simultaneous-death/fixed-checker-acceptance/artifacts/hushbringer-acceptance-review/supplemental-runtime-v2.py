from pathlib import Path
import json,hashlib,subprocess,datetime,re
O=Path(__file__).parent;E=O.parent;R=Path('/home/ubuntu/repos/coworld-mtg');D=R/'tmp/verifiable-loop/isolated-candidate-build';W=D/'worker';I=E/'hushbringer-review-v10-final/original-runtime';out=O/'final-worker-runtime';out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
assert sha(W)==read(D/'build.json')['binary_sha256']=='f5b0de9436da31a00aaf7a1d28b92bd4288bd47077412970e0c3585f0cce1784'
rows=[]
for name,expected in [('hush-first',0),('traveler-first',0),('no-hush',1)]:
 req=I/f'{name}-request.json';v=read(req);assert sha(Path(v['corpus_path']))==v['corpus_sha256']=='8b7151e61d99082ba22c39ee5dc56e798e339e44387af5834f6b3c1982dfbb3c'
 for card in v['scenario']['cards']:card.setdefault('tapped',False);card.setdefault('plus_one_counters',0)
 for op in v['scenario']['operations']:
  if op['kind']=='cast':op.setdefault('x',None)
 executions=[];commands=[]
 for i in range(2):
  target=out/f'{name}-{i}-execution.json';log=out/f'{name}-{i}.log';cmd=[str(W),'case','execute','--request',str(req),'--output',str(target)]
  prior=target.exists()
  if prior:assert name=='hush-first' and i==0 and log.exists()
  else:
   cp=subprocess.run(cmd,cwd=R,capture_output=True,text=True);log.write_text(cp.stdout+cp.stderr);assert cp.returncode==0
  x=read(target);assert x['request_id']==digest(v) and x['binary_sha256']==sha(W) and x['outcome']['kind']=='completed'
  assert [s['operation_index'] for s in x['outcome']['steps']]==list(range(len(v['scenario']['operations'])))
  obs=x['outcome']['observation'];objects={o['object_id']:o for o in obs['objects']}
  for label in ['traveler','wrath']+(['hush'] if name!='no-hush' else []):assert objects[obs['labels'][label]]['zone']=='graveyard'
  spirits=sum(o['owner']=='player' and o['zone']=='battlefield' and o['name']=='Spirit' for o in obs['objects']);assert spirits==expected
  executions.append(x);commands.append(dict(command=cmd,exit=0,existing_successful_execution_checked_after_normalizing_serde_defaults=prior,evidence_sha256=sha(target),evidence_id=digest(x),log_sha256=sha(log)))
 assert executions[0]==executions[1]
 rows.append(dict(name=name,request_path=str(req),request_sha256=sha(req),request_id=digest(v),spirits=expected,repeatability='exact two-run equality',commands=commands,observation=executions[0]['outcome']['observation']))
cp=subprocess.run(['ldd',str(W)],capture_output=True,text=True,check=True);(out/'ldd.txt').write_text(cp.stdout);libs={}
for line in cp.stdout.splitlines():
 match=re.search(r'(/[^\s]+)',line)
 if match:
  p=Path(match.group(1));libs[str(p)]=sha(p)
v=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),worker_sha256=sha(W),phase_revision='fa0ebfe88db224ebd32624bb96ef033d338c2d8c',newly_compiled=True,build_json_sha256=sha(D/'build.json'),runtime_cwd=str(R),loader_libraries=libs,scenarios=rows,scope='Supplemental final-worker executions using the independently preserved original scenario requests. Frozen acceptance inputs, plan and case IDs are not modified; these are not added planned gates.')
with (out/'receipt.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
print('PASS: actual final fa0eb worker Hush-first0,Traveler-first0,no-Hush1 Spirit, each repeated identically with all graveyard guards;6 fresh executions.')
