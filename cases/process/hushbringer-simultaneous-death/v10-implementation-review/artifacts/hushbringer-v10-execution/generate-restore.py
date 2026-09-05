from pathlib import Path
import subprocess,hashlib,json,datetime
root=Path('/home/ubuntu/repos/phase-verifiable-loop')
out=Path('/home/ubuntu/coworld-migration-20260904/hushbringer-v10-execution/card-data-final')
out.mkdir(exist_ok=False)
known=['crates/engine/data/known-tokens.toml','crates/engine/data/oracle-subtypes.json']
files=sorted(set(subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','crates','Cargo.toml','Cargo.lock','rust-toolchain.toml','.cargo'],cwd=root).decode().splitlines()))
files=[f for f in files if (root/f).is_file()]
def hashes():return {f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in files}
before=hashes(); originals={f:(root/f).read_bytes() for f in known}
for f,data in originals.items():(out/(Path(f).name+'.before')).write_bytes(data)
(out/'before-source.json').write_text(json.dumps(before,indent=2)+'\n')
receipt={'started':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':['./scripts/gen-card-data.sh'],'checkout':str(root),'target':str(root/'target')}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
with (out/'generation.log').open('wb') as stream:
 result=subprocess.run(['./scripts/gen-card-data.sh'],cwd=root,stdout=stream,stderr=subprocess.STDOUT)
(out/'generation.exit').write_text(str(result.returncode)+'\n')
generated=hashes()
for f in known:(out/(Path(f).name+'.generated')).write_bytes((root/f).read_bytes())
(out/'generated-source.json').write_text(json.dumps(generated,indent=2)+'\n')
(out/'generator-source.patch').write_bytes(subprocess.check_output(['git','diff','--binary','--',*known],cwd=root))
for f,data in originals.items():(root/f).write_bytes(data)
restored=hashes()
receipt.update({'exit':result.returncode,'generation_log_sha256':hashlib.sha256((out/'generation.log').read_bytes()).hexdigest(),
'changed_by_generator':[f for f in files if before[f]!=generated[f]],'post_restore_changed':[f for f in files if before[f]!=restored[f]],
'known_before':{f:before[f] for f in known},'known_generated':{f:generated[f] for f in known},'known_restored':{f:restored[f] for f in known},
'finished':datetime.datetime.now(datetime.timezone.utc).isoformat()})
(out/'restored-source.json').write_text(json.dumps(restored,indent=2)+'\n')
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
raise SystemExit(result.returncode or (1 if receipt['post_restore_changed'] else 0))
