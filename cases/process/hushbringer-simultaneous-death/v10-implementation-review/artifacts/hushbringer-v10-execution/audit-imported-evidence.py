from pathlib import Path
import json,hashlib,datetime
base=Path('/home/ubuntu/coworld-migration-20260904');out=base/'hushbringer-v10-execution/imported-evidence-audit.json';cache={};errors=[];checked=[]
def h(p):
 p=Path(p)
 if str(p) not in cache:
  digest=hashlib.sha256()
  with p.open('rb') as stream:
   for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
  cache[str(p)]=digest.hexdigest()
 return cache[str(p)]
def verify(p,want):
 p=Path(p)
 try:actual=h(p);assert actual==want,(str(p),actual,want);checked.append(str(p))
 except Exception as error:errors.append(str(error))
for name,receipt in [('hushbringer-v9-r2-r3-mutations','9977d4ef8b771355b72d0fae046b815681bf5c3daf86a914930c2d53485275c0'),('hushbringer-v9-matcher-mutations','abc25262c6d4cb40ab791d5542c60cba742581f5124787b967cd4ea32fcf04e1')]:
 directory=base/name;verify(directory/'receipt.json',receipt);r=json.loads((directory/'receipt.json').read_text());verify(directory/'manifest.json',r.get('manifest_sha256',r.get('artifact_manifest_sha256')));verify(directory/'audited-results.json',r.get('audit_sha256',r.get('audited_results_sha256')));verify(r['report'],r['report_sha256'])
 for p,want in json.loads((directory/'manifest.json').read_text()).items():verify(directory/p,want)
lib=base/'hushbringer-v9-library-mutations';verify(lib/'original-nineteen-proof-index.json','eba94ec9c4255a431f42fe771fbe2b8823cef25650de991ff4a7e22297cfc526')
for row in json.loads((lib/'original-nineteen-proof-index.json').read_text())['rows']:
 verify(row['outcome'],row['outcome_sha256']);manifests={}
 for phase,p in row['phases'].items():
  for key in ['source_manifest','source_archive','receipt']:
   if p.get(key):verify(p[key],p[key+'_sha256'])
  if p.get('source_manifest'):manifests[phase]=json.loads(Path(p['source_manifest']).read_text())
 if set(manifests)=={'baseline','mutant','restored'}:
  assert manifests['baseline']==manifests['restored'],row['row']['id'];diff=[f for f in manifests['baseline'] if manifests['baseline'][f]!=manifests['mutant'][f]];assert diff==[row['row']['file']],(row['row']['id'],diff)
root=base/'hushbringer-v9-execution/mutations-1';a=base/'hushbringer-v9-public-root-audit-final.json';verify(a,'519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18')
canonical=json.loads((base/'hushbringer-v9-execution/frozen-candidate-v9/source.json').read_text())
for row in json.loads(a.read_text())['rows']:
 for phase,witness in row['verified'].items():
  d=root/row['id']/phase
  for name,key in [('receipt.json','receipt_sha256'),('source.json','source_manifest_sha256'),('source.tar.gz','source_archive_sha256'),('command.log','log_sha256')]:verify(d/name,witness[key])
  observed=json.loads((d/'source.json').read_text());diff=[f for f in canonical if canonical[f]!=observed[f]];assert diff==([row['file']] if phase=='mutant' else []),(row['id'],phase,diff)
 verify(root/row['id']/'result.json',row['result_sha256']);verify(root/row['id']/'mutation.patch',row['mutation_patch_sha256'])
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'unique_artifacts_hashed':len(cache),'verification_operations':len(checked),'errors':errors,'source_lineage':'Original30 public and19 library baseline/mutant/restored manifests checked: restored equals canonical; only declared physical file differs in each mutant. Original5 R2/R3 and9 matcher complete artifact manifests rehashed. Independent original archive-content/semantic audits remain linked; this does not relabel their source or compile methods.','verified_artifact_hashes':cache}
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='verified_artifact_hashes'},indent=2));assert not errors
