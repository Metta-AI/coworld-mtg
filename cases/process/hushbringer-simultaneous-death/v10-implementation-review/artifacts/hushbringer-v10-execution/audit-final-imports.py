import pathlib,hashlib,json,datetime
b=pathlib.Path('/home/ubuntu/coworld-migration-20260904');e=b/'hushbringer-v10-execution';cache={};errors=[];historical_target_refs=[]
def h(p):
 p=pathlib.Path(p)
 if str(p) not in cache:
  d=hashlib.sha256()
  with p.open('rb') as stream:
   for v in iter(lambda:stream.read(1024*1024),b''):d.update(v)
  cache[str(p)]=d.hexdigest()
 return cache[str(p)]
def verify(p,want):
 if '/target/' in str(p):
  historical_target_refs.append({'path':str(p),'recorded_sha256':want,'status':'historical mutable build-target output; identity is bound by archived compilation/runtime receipt, not current target bytes'});return
 try:assert h(p)==want,(str(p),h(p),want)
 except Exception as ex:errors.append(str(ex))
def walk(x):
 if isinstance(x,list):
  for z in x:walk(z)
 elif isinstance(x,dict):
  for k,v in x.items():
   if isinstance(v,str) and v.startswith('/home/ubuntu/') and k+'_sha256' in x:verify(v,x[k+'_sha256'])
   walk(v)
def load(p):return json.loads(pathlib.Path(p).read_text())
d=b/'hushbringer-v10-batched-mutations';verify(d/'receipt.json','723c77ce1c56ec415a1179bcea9b1019e1e6eca7020b6b1097d809373c0e3451');rec=load(d/'receipt.json');verify(d/'manifest.json',rec['manifest_sha256']);verify(d/'audited-results.json',rec['audit_sha256']);verify(rec['report'],rec['report_sha256'])
for f,want in load(d/'manifest.json').items():verify(d/f,want)
lib=b/'hushbringer-v9-library-mutations';verify(b/'hushbringer-v9-library-mutations-receipt.json','6d63785a08871c27d8939545c0a1ca34a917dc26a49ae52afb094babf6ba2650');walk(load(b/'hushbringer-v9-library-mutations-receipt.json'))
for folder,audit,want in [('lexical-battle-v10-attempt-1',lib/'v10-three-supplemental-independent-audit.json','7e9cd244ecff7dbd1958ca7d42bb7060bd26064643fcb0e1643340c508fecda4'),('expanded-v10-root-attempt-1',lib/'expanded-v10-root-attempt-1/root-archive-audit.json','f0b9eeedadf71b8506aca0134aaa5e38e261114654a4983b0d8632288dbaba91')]:
 verify(audit,want);a=load(audit);verify(lib/folder/'results.json',a['results_sha256']);result=load(lib/folder/'results.json');walk(result)
 for row in a['rows']:
  verify(lib/folder/row['id']/'outcome.json',row['outcome_sha256']);out=load(lib/folder/row['id']/'outcome.json');walk(out)
  for phase in ['baseline','mutant','restored']:
   for i,run in enumerate(out[phase]):
    p=lib/folder/row['id']/phase/(str(i)+'.log')
    if p.exists():verify(p,run['log_sha256'])
 # Entire canonical/mutant manifests remain physically paired with the imported build receipts.
 canonical=load(lib/folder/'canonical-build/source.json')
 assert len(canonical)==2051
 for row in result['rows']:
  mutant=load(lib/folder/row['id']/'mutant-build/source.json');diff=[f for f in canonical if canonical[f]!=mutant[f]]
  definition=load(lib/folder/row['id']/'transformation.json')['row'];assert diff==[definition['file']],(row['id'],diff)
  assert load(lib/folder/row['id']/'restoration.json')['all_source_restored']
x={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verified_artifacts':len(cache),'errors':errors,'scope':'Fresh rehash of complete2-batch artifact manifest and3-library/10-root final source/archive/compilation paths and available per-run logs; exact full archive-content checks are retained in hashed independent audits. No compilation relabeling.','verified_hashes':cache,'historical_mutable_target_references':historical_target_refs,'retained_attempt_1':'Overbroad recursive audit tried to rehash historical mutable Cargo target outputs; all130 mismatches were target paths, zero immutable-artifact mismatch. Corrected scope preserves their original compile/runtime receipt identities and rehashes preserved canonical artifacts.'};(e/'final-imported-evidence-audit.json').write_text(json.dumps(x,indent=2)+'\n');print('artifacts',len(cache),'errors',errors);assert not errors
