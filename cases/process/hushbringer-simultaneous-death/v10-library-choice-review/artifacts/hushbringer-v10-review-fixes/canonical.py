from pathlib import Path
import json,subprocess,hashlib,sys,datetime,os
out=Path('/home/ubuntu/coworld-migration-20260904/hushbringer-v10-review-fixes');root=Path('/home/ubuntu/repos/phase-verifiable-loop')
command=['cargo','test','-p','engine','--test','integration','--no-run','--message-format=json']; p=subprocess.run(command,cwd=root,capture_output=True,text=True);print(p.stdout,end='');print(p.stderr,end='',file=sys.stderr)
artifacts=[]
for line in p.stdout.splitlines():
 try:x=json.loads(line)
 except ValueError:continue
 if x.get('reason')=='compiler-artifact' and x.get('executable'):
  f=Path(x['executable']); artifacts.append({'cargo_artifact':x,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'stat':{'size':f.stat().st_size,'mtime_ns':f.stat().st_mtime_ns,'inode':f.stat().st_ino}})
r={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':command,'exit':p.returncode,'source_manifest_sha256':hashlib.sha256((out/'frozen-source/source.json').read_bytes()).hexdigest(),'cwd':str(root),'env':{k:os.environ.get(k) for k in ['PATH','CARGO_TARGET_DIR','CARGO_BUILD_JOBS','RUST_MIN_STACK','RTK_DISABLED']},'artifacts':artifacts}
(out/'canonical-build.json').write_text(json.dumps(r,indent=2)+'\n');assert p.returncode or any(a['cargo_artifact']['target']['name']=='integration' for a in artifacts)
sys.exit(p.returncode)
