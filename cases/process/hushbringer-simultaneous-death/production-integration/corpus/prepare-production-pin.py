#!/usr/bin/env python3
"""Prepare an already published Phase revision and matching corpus; never upload or commit."""
from pathlib import Path
import argparse,hashlib,io,json,os,re,subprocess,tarfile
a=argparse.ArgumentParser();a.add_argument('revision');args=a.parse_args()
assert re.fullmatch('[0-9a-f]{40}',args.revision)
r=Path('/home/ubuntu/repos/coworld-mtg-publish')
phase=Path('/home/ubuntu/repos/phase-hushbringer-publish')
b=Path('/home/ubuntu/coworld-migration-20260904/phase-main-publication-corpus')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
g=lambda cwd,*a:subprocess.check_output(['git',*a],cwd=cwd,text=True).strip()
assert not g(r,'status','--porcelain')
assert not g(phase,'status','--porcelain')
assert g(phase,'rev-parse','HEAD')==args.revision
published=subprocess.check_output(['git','ls-remote','https://github.com/nishu-builder/phase.git','refs/heads/main'],text=True).split()[0]
assert published==args.revision,'Phase must be published first'
old=json.loads((r/'phase-source.json').read_text())['revision']
old_lock=json.loads((r/'corpus.lock.json').read_text())
assert old_lock['phase_revision']==old
corpus=r/'.private/corpus';old_manifest=json.loads((corpus/'manifest.json').read_text())
assert old_manifest['phase_revision']==old
payloads={n:sha(corpus/n) for n in old_manifest['files']}
for n,expected in old_manifest['files'].items():assert payloads[n]==expected['sha256']
names=['phase-source.json','crates/phase-bridge/Cargo.toml','crates/phase-bridge/src/lib.rs','Dockerfile.coworld','scripts/build-corpus-artifact.py']
before={n:sha(r/n) for n in names+['Cargo.lock','corpus.lock.json']}
for n in names:
 p=r/n;text=p.read_text();assert text.count(old)==1,(n,text.count(old))
 p.write_text(text.replace(old,args.revision))
env=dict(os.environ);env['PATH']='/home/ubuntu/.cargo/bin:'+env['PATH']
with (b/'pin-cargo-update.log').open('x') as f:
 subprocess.run(['scripts/cargo.sh','update','-p','engine'],cwd=r,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
archive=b/('corpus-'+args.revision+'.tar.zst');assert not archive.exists()
generated=subprocess.check_output(['python3','scripts/build-corpus-artifact.py',str(corpus),str(archive)],cwd=r,text=True)
size=archive.stat().st_size;digest=sha(archive)
assert json.loads(generated)=={'bytes':size,'sha256':digest}
raw=subprocess.check_output(['zstd','-q','-d','-c',str(archive)])
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tar:
 members=tar.getmembers()
 assert sorted(m.name for m in members)==sorted([*payloads,'manifest.json'])
 assert all(m.isfile() for m in members)
 contents={m.name:tar.extractfile(m).read() for m in members}
manifest=json.loads(contents['manifest.json'])
assert manifest['phase_revision']==args.revision
for n,h in payloads.items():assert hashlib.sha256(contents[n]).hexdigest()==h
(corpus/'manifest.json').write_bytes(contents['manifest.json'])
uri='s3://observatory-private/cogames/coworlds/coworld-mtg/corpora/v1/'+digest+'/coworld-mtg-corpus-v1.tar.zst'
lock=dict(old_lock,archive_uri=uri,bytes=size,sha256=digest,phase_revision=args.revision)
(r/'corpus.lock.json').write_text(json.dumps(lock,sort_keys=True,indent=2)+'\n')
subprocess.run(['python3','scripts/check-phase-pin.py'],cwd=r,check=True)
receipt={'phase_revision':args.revision,'previous_revision':old,'archive':str(archive),'archive_uri':uri,'sha256':digest,'bytes':size,'card_count':manifest['card_count'],'payloads_unchanged':payloads,'manifest_sha256':hashlib.sha256(contents['manifest.json']).hexdigest(),'old_lock':old_lock,'changed_files':{n:{'before':h,'after':sha(r/n)} for n,h in before.items()},'uploaded':False,'qualification':'New deterministic archive with matching manifest; existing serialized card/deck payloads preserved, not represented as a fresh parser export'}
(b/'prepared-pin.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
