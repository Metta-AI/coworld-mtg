#!/usr/bin/env python3
from pathlib import Path
import datetime,hashlib,json,os,subprocess,time
b=Path('/home/ubuntu/coworld-migration-20260904')
out=b/'phase-main-integration'
r=Path('/home/ubuntu/repos/phase-hushbringer-publish')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((out/'source.json').read_text())
receipt={'started':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'waiting for isolated worker build to finish before compiling in separate target','commands':[]}
def save():(out/'verification-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
save()
while not (b/'final-committed-worker-run/done').exists():
 p=b/'final-committed-worker-run/receipt.json'
 if p.exists():
  prior=json.loads(p.read_text())
  if any(c['exit'] for c in prior['commands']):raise SystemExit('Preceding worker build/comparison failed')
 time.sleep(10)
for n,h in manifest.items():assert sha(r/n)==h,n
assert not (r/'target').exists(),'New integration checkout must use its own fresh target'
env=dict(os.environ)
for k in list(env):
 if k.startswith('CARGO_PROFILE_') or k in ('CARGO_TARGET_DIR','RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','CARGO_BUILD_TARGET','FORGE_TEST_FULL_DB'):env.pop(k)
env.update(PATH='/home/ubuntu/.cargo/bin:'+env['PATH'],CARGO_BUILD_JOBS='1',CARGO_PROFILE_DEV_DEBUG='0',CARGO_PROFILE_TEST_DEBUG='0',CARGO_INCREMENTAL='0')
receipt.update(status='running',environment={k:env[k] for k in ('CARGO_BUILD_JOBS','CARGO_PROFILE_DEV_DEBUG','CARGO_PROFILE_TEST_DEBUG','CARGO_INCREMENTAL')},source_manifest_sha256=sha(out/'source.json'))
generated=['crates/engine/data/known-tokens.toml','crates/engine/data/oracle-subtypes.json']
original={n:(r/n).read_bytes() for n in generated}
for i,cmd in enumerate([['cargo','clippy','--workspace','--all-targets','--locked','--','-D','warnings'],['cargo','test','-p','engine','--locked'],['bash','scripts/gen-card-data.sh']]):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 log=out/f'verification-{i}.log'
 with log.open('x') as f:p=subprocess.run(cmd,cwd=r,env=env,stdout=f,stderr=subprocess.STDOUT)
 receipt['commands'].append({'command':cmd,'exit':p.returncode,'started':start,'finished':datetime.datetime.now(datetime.timezone.utc).isoformat(),'log':str(log),'log_sha256':sha(log)})
 if i==2:
  changes=[]
  for n,data in original.items():
   if (r/n).read_bytes()!=data:
    changes.append({'path':n,'before':hashlib.sha256(data).hexdigest(),'generated':sha(r/n)})
    (r/n).write_bytes(data)
  receipt['generated_tracked_files_restored']=changes
 save()
 if p.returncode:raise SystemExit(p.returncode)
for n,h in manifest.items():assert sha(r/n)==h,n
subprocess.run(['cargo','fmt','--all','--check'],cwd=r,env=env,check=True)
subprocess.run(['git','diff','--exit-code'],cwd=r,check=True)
receipt.update(status='passed',source_unchanged=True,finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
save();(out/'verified').write_text('complete\n')
