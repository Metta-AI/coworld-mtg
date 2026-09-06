#!/usr/bin/env python3
from pathlib import Path
import collections,datetime,hashlib,json,os,subprocess
b=Path('/home/ubuntu/coworld-migration-20260904')
r=Path('/home/ubuntu/repos/coworld-mtg-publish')
out=b/'coworld-production-pin-check'
out.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
prepared=json.loads((b/'phase-main-publication-corpus/prepared-pin.json').read_text())
upload=json.loads((b/'phase-main-publication-corpus/upload-receipt.json').read_text())
assert upload['verified_sha256']==prepared['sha256']
names=subprocess.check_output(['git','ls-files','-z'],cwd=r).decode().split(chr(0))
sources={n:sha(r/n) for n in sorted(set(names)) if n and (r/n).is_file()}
(out/'source.json').write_text(json.dumps(sources,indent=2)+'\n')
env=dict(os.environ)
for k in list(env):
 if k.startswith('CARGO_PROFILE_') or k in ('RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','CARGO_BUILD_TARGET'):env.pop(k)
env.update(PATH='/home/ubuntu/.cargo/bin:'+env['PATH'],CARGO_BUILD_JOBS='1',CARGO_PROFILE_DEV_DEBUG='0',CARGO_PROFILE_TEST_DEBUG='0',CARGO_INCREMENTAL='0',CARGO_TARGET_DIR=str(r/'target'))
receipt={'started':now(),'phase_revision':prepared['phase_revision'],'status':'running','source_manifest_sha256':sha(out/'source.json'),'private_corpus_manifest_sha256':sha(r/'.private/corpus/manifest.json'),'commands':[],'environment':{k:env[k] for k in ['CARGO_BUILD_JOBS','CARGO_PROFILE_DEV_DEBUG','CARGO_PROFILE_TEST_DEBUG','CARGO_INCREMENTAL','CARGO_TARGET_DIR']}}
def save():(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
save()
worker=r/'target/debug/coworld-mtg-harness'
for name,cmd in [('corpus-install',['bash','scripts/fetch-corpus.sh']),('repository-check',['bash','scripts/check.sh']),('production-campaign',[str(worker),'case','campaign','--case-dir',str(r/'cases/cards'),'--corpus',str(r/'cases/corpus/corpus.json'),'--worker',str(worker),'--output-dir',str(out/'campaign')])]:
 started=now()
 if name=='production-campaign':receipt['worker_sha256']=sha(worker)
 log=out/(name+'.log')
 command_env=dict(env)
 if name=='corpus-install':command_env['COWORLD_MTG_CORPUS_URI']=prepared['archive']
 with log.open('x') as f:p=subprocess.run(cmd,cwd=r,env=command_env,stdout=f,stderr=subprocess.STDOUT)
 receipt['commands'].append({'name':name,'command':cmd,'exit':p.returncode,'started':started,'finished':now(),'log_sha256':sha(log)})
 receipt['source_changes']=[n for n,h in sources.items() if not (r/n).exists() or sha(r/n)!=h]
 save()
 if p.returncode or receipt['source_changes']:
  receipt['status']='failed';save();raise SystemExit(p.returncode or 1)
receipt['status']='passed';receipt['finished']=now();save()
(out/'verified').write_text('complete\n')
