from pathlib import Path
import datetime,hashlib,json,os,subprocess
work=Path('/home/ubuntu/repos/phase-verifiable-loop')
out=Path('/home/ubuntu/coworld-migration-20260904')
manifest_path=out/'hushbringer-production-final-partial-source-v7.json'
manifest=json.loads(manifest_path.read_text())
for name,digest in manifest['files'].items():
    assert hashlib.sha256((work/name).read_bytes()).hexdigest()==digest,name
command=['cargo','test','-p','engine','--','--test-threads=2']
env=dict(os.environ,PATH='/home/ubuntu/.cargo/bin:'+os.environ['PATH'],CARGO_BUILD_JOBS='2',CARGO_TARGET_DIR=str(work/'target'))
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (out/'hushbringer-root-full-engine-v7.log').open('x') as log:
    result=subprocess.run(command,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT)
(out/'hushbringer-root-full-engine-v7.exit').write_text(str(result.returncode)+'\n')
changed=[name for name,digest in manifest['files'].items() if not (work/name).is_file() or hashlib.sha256((work/name).read_bytes()).hexdigest()!=digest]
receipt={'stage':'v7-partial-broad-suite-before-reviewed-component-repair','started_utc':started,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':command,'cwd':str(work),'target':str(work/'target'),'command_exit':result.returncode,'source_manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),'changed_source_files':changed,'log_sha256':hashlib.sha256((out/'hushbringer-root-full-engine-v7.log').read_bytes()).hexdigest()}
(out/'hushbringer-root-full-engine-v7-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
