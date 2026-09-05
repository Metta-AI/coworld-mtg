#!/usr/bin/env python3
"""Library-owner isolated supplemental verification. This script never selects or edits active source."""
from pathlib import Path
import atexit,argparse,datetime,difflib,hashlib,importlib.util,itertools,json,os,re,subprocess,sys,tarfile,traceback
P=argparse.ArgumentParser()
for name in ['manifest','manifest-sha256','archive','archive-sha256','inventory','inventory-sha256','helpers','helpers-sha256','out']:
 P.add_argument('--'+name,required=True)
P.add_argument('--checkout',default='/home/ubuntu/repos/phase-hushbringer-mutations-library')
P.add_argument('--apply-frozen',action='store_true')
P.add_argument('--runtime-input-manifest')
P.add_argument('--runtime-input-manifest-sha256')
P.add_argument('--jobs',default='1',choices=['1'])
a=P.parse_args()
C=Path(a.checkout).resolve();O=Path(a.out)
assert C==Path('/home/ubuntu/repos/phase-hushbringer-mutations-library')
assert not (C/'target').is_symlink()
assert bool(a.runtime_input_manifest)==bool(a.runtime_input_manifest_sha256)
assert a.apply_frozen,'Executor must explicitly apply the final frozen source to its exclusive isolated checkout.'
assert not O.exists(),'Append-only attempt directory must be new.'
O.mkdir(parents=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
for key in ['manifest','archive','inventory','helpers']:
 assert sha(getattr(a,key))==getattr(a,key+'_sha256'),key
S=json.loads(Path(a.manifest).read_text());I=json.loads(Path(a.inventory).read_text())
assert len(S)>=2000 and isinstance(I['rows'],list)
expected_ids={'scope-before-flush','leaf-consumes-member','sba-check_battle_protector'}
assert len(I['rows'])==3 and {r['id'] for r in I['rows']}==expected_ids
with tarfile.open(a.archive) as ar:
 assert set(ar.getnames())==set(S)
 B={f:ar.extractfile(f).read() for f in S}
for f,b in B.items():
 assert not Path(f).is_absolute() and '..' not in Path(f).parts
 assert hashlib.sha256(b).hexdigest()==S[f]
spec=importlib.util.spec_from_file_location('mutation_helpers',a.helpers)
H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
E=dict(os.environ,PATH='/home/ubuntu/.cargo/bin:'+os.environ['PATH'],CARGO_BUILD_JOBS=a.jobs,CARGO_TARGET_DIR=str(C/'target'),RTK_DISABLED='1')
RUNTIME_KEYS=['CARGO', 'CARGO_MANIFEST_DIR', 'CARGO_MANIFEST_PATH', 'CARGO_MANIFEST_LINKS', 'CARGO_BIN_NAME', 'CARGO_TARGET_TMPDIR', 'OUT_DIR', 'RUST_MIN_STACK', 'RUST_BACKTRACE', 'RUST_LIB_BACKTRACE', 'RUST_TEST_THREADS', 'RUST_TEST_NOCAPTURE', 'RUST_LOG', 'RUSTUP_TOOLCHAIN', 'RUSTUP_HOME', 'CARGO_HOME', 'RUSTC', 'RUSTDOC', 'PATH', 'LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH', 'DYLD_FALLBACK_LIBRARY_PATH', 'LANG', 'LC_ALL', 'LC_CTYPE', 'TZ', 'TMPDIR', 'TEMP', 'TMP']
def unsafe_environment(env,allow_runtime_loader=False,allow_capture_runner=False):
 forbidden={}
 for k,v in env.items():
  banned=k.startswith(('PHASE_','FORGE_','DYLD_')) or k in {'RUSTC_WRAPPER','RUSTC_WORKSPACE_WRAPPER','CARGO_BUILD_RUSTC_WRAPPER','CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER','RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','CARGO_BUILD_RUSTFLAGS','RUSTDOCFLAGS','RUSTC_BOOTSTRAP','LD_PRELOAD','LD_AUDIT','LD_DEBUG','LD_ASSUME_KERNEL','LD_BIND_NOW','RUST_TEST_THREADS','RUST_TEST_NOCAPTURE'}
  banned=banned or (k.startswith('CARGO_TARGET_') and k.endswith(('_RUNNER','_RUSTFLAGS','_LINKER')) and not (allow_capture_runner and k=='CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_RUNNER'))
  banned=banned or (k.startswith('LD_') and not (allow_runtime_loader and k=='LD_LIBRARY_PATH'))
  if banned and v:forbidden[k]={'value_sha256':hashlib.sha256(v.encode()).hexdigest(),'present_nonempty':True}
 return forbidden
ambient_unsafe=unsafe_environment(os.environ)
write(O/'ambient-override-audit.json',{'forbidden_nonempty':ambient_unsafe,'policy':'Reject inherited PHASE/FORGE/loader/wrapper/compiler/target/runtime-behavior overrides; values hashed to avoid unrelated disclosure.'})
assert not ambient_unsafe,'Unreviewed ambient runtime/build override; see audit receipt.'
EXTERNAL={}
if a.runtime_input_manifest:
 assert sha(a.runtime_input_manifest)==a.runtime_input_manifest_sha256
 EXTERNAL=json.loads(Path(a.runtime_input_manifest).read_text())
 for name,digest in EXTERNAL.items():
  assert Path(name).is_absolute() and sha(name)==digest
fixture='crates/engine/tests/fixtures/integration_cards.json'
assert fixture in S
def verify_inputs():
 for name,digest in EXTERNAL.items():assert sha(name)==digest
 assert sha(C/fixture)==S[fixture]
def verify(source):
 actual={f:sha(C/f) for f in S}
 assert actual==source,[f for f in actual if actual[f]!=source[f]]
def restore(all_fresh=False):
 restored_files=[]
 for f,b in B.items():
  p=C/f;p.parent.mkdir(parents=True,exist_ok=True)
  if all_fresh or not p.exists() or p.read_bytes()!=b:
   before=p.stat().st_mtime_ns if p.exists() else None;p.write_bytes(b);after=p.stat().st_mtime_ns
   if not all_fresh and before is not None:assert after>before,'Restored mtime must be fresher than observed mutant mtime.'
   restored_files.append({'file':f,'before_write_mtime_ns':before,'restored_mtime_ns':after,'source_sha256':sha(p)})
 verify(S);return restored_files
def snapshot(d,source,patch=''):
 d.mkdir(parents=True,exist_ok=False);verify(source);write(d/'source.json',source)
 with tarfile.open(d/'source.tar.gz','w:gz') as ar:
  for f in S:ar.add(C/f,arcname=f,recursive=False)
 (d/'mutant.patch').write_text(patch)
 return {'source_manifest':str(d/'source.json'),'source_manifest_sha256':sha(d/'source.json'),'source_archive':str(d/'source.tar.gz'),'source_archive_sha256':sha(d/'source.tar.gz'),'mutant_patch_sha256':sha(d/'mutant.patch')}
def counts(text):
 return [{'status':x[0],'passed':int(x[1]),'failed':int(x[2]),'ignored':int(x[3]),'filtered_out':int(x[5])} for x in re.findall(r'test result: (\w+)\. (\d+) passed; (\d+) failed; (\d+) ignored; (\d+) measured; (\d+) filtered out',text)]
def cargo(d,source,patch='',cmd=None,env=None,association=None):
 if association is None:info=snapshot(d,source,patch)
 else:
  d.mkdir(parents=True,exist_ok=False);verify(source)
  info={k:association[k] for k in ['source_manifest','source_manifest_sha256','source_archive','source_archive_sha256','mutant_patch_sha256']}
 cmd=cmd or ['cargo','+nightly-2026-04-19','test','-p','engine','--lib','--message-format=json','--no-run']
 record=dict(info,started=utc(),command=cmd,checkout=str(C),cwd=str(C),target=str(C/'target'),environment={k:E.get(k) for k in ['CARGO_BUILD_JOBS','CARGO_TARGET_DIR','RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','RUSTUP_TOOLCHAIN','RUST_MIN_STACK']})
 write(d/'started.json',record)
 with (d/'command.log').open('wb') as stream:r=subprocess.run(cmd,cwd=C,env=env or E,stdout=stream,stderr=subprocess.STDOUT)
 (d/'command.exit').write_text(str(r.returncode)+'\n')
 text=(d/'command.log').read_text(errors='replace');artifacts=[];build_scripts=[]
 for line in text.splitlines():
  try:v=json.loads(line)
  except (ValueError,TypeError):continue
  if v.get('reason')=='compiler-artifact' and 'engine#' in v.get('package_id',''):
   exe=v.get('executable')
   artifacts.append({'package_id':v['package_id'],'target':v['target'],'profile':v['profile'],'features':v['features'],'fresh':v['fresh'],'executable':exe,'executable_sha256':sha(exe) if exe else None})
  if v.get('reason')=='build-script-executed' and 'engine#' in v.get('package_id',''):build_scripts.append(v)
 verify(source)
 record.update(finished=utc(),exit=r.returncode,log_sha256=sha(d/'command.log'),artifacts=artifacts,build_scripts=build_scripts,counts=counts(text),source_unchanged=True)
 write(d/'receipt.json',record);return record
def fmt(d,check):
 d.mkdir(parents=True,exist_ok=False);cmd=['cargo','+nightly-2026-04-19','fmt','--all']+(['--','--check'] if check else [])
 with (d/'command.log').open('wb') as stream:r=subprocess.run(cmd,cwd=C,env=E,stdout=stream,stderr=subprocess.STDOUT)
 write(d/'receipt.json',{'command':cmd,'exit':r.returncode,'log_sha256':sha(d/'command.log'),'utc':utc()})
 assert r.returncode==0
def integration(build):
 xs=[v for v in build['artifacts'] if v['target']['name']=='engine' and v['executable']]
 assert len(xs)==1;return xs[0]
restore(all_fresh=True)
def exit_restore():
 restore()
 write(O/'exit-source-restoration.json',{'utc':utc(),'all_source_restored':True,'source_manifest_sha256':a.manifest_sha256})
atexit.register(exit_restore)
for label,command in [('cargo',['cargo','+nightly-2026-04-19','-Vv']),('rustc',['rustc','+nightly-2026-04-19','-Vv'])]:
 d=O/('toolchain-'+label);d.mkdir()
 with (d/'command.log').open('wb') as stream:result=subprocess.run(command,cwd=C,env=E,stdout=stream,stderr=subprocess.STDOUT)
 write(d/'receipt.json',{'command':command,'exit':result.returncode,'log_sha256':sha(d/'command.log')});assert result.returncode==0
write(O/'inputs.json',{'utc':utc(),'arguments':vars(a),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=C,text=True).strip(),'source_files':len(S),'all_source_bytes_applied_with_fresh_mtimes':True,'script_sha256':sha(__file__)})
fmt(O/'initial-format-check',True);verify(S)
canonical_build=cargo(O/'canonical-build',S);assert canonical_build['exit']==0
artifact=integration(canonical_build);assert not artifact['fresh'],'Canonical artifact must be freshly compiled for applied source.'
canonical=O/'canonical-engine';canonical.write_bytes(Path(artifact['executable']).read_bytes());canonical.chmod(0o555)
assert sha(canonical)==artifact['executable_sha256'] and canonical.stat().st_nlink==1
assert (canonical.stat().st_dev,canonical.stat().st_ino)!=(Path(artifact['executable']).stat().st_dev,Path(artifact['executable']).stat().st_ino)
wrapper=O/'capture-runtime.py'
wrapper.write_text("from pathlib import Path\nimport os,sys,json,hashlib\np=Path("+repr(str(O/'runtime-context.json'))+")\nassert not p.exists()\nkeys=['CARGO', 'CARGO_MANIFEST_DIR', 'CARGO_MANIFEST_PATH', 'CARGO_MANIFEST_LINKS', 'CARGO_BIN_NAME', 'CARGO_TARGET_TMPDIR', 'OUT_DIR', 'RUST_MIN_STACK', 'RUST_BACKTRACE', 'RUST_LIB_BACKTRACE', 'RUST_TEST_THREADS', 'RUST_TEST_NOCAPTURE', 'RUST_LOG', 'RUSTUP_TOOLCHAIN', 'RUSTUP_HOME', 'CARGO_HOME', 'RUSTC', 'RUSTDOC', 'PATH', 'LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH', 'DYLD_FALLBACK_LIBRARY_PATH', 'LANG', 'LC_ALL', 'LC_CTYPE', 'TZ', 'TMPDIR', 'TEMP', 'TMP']\np.write_text(json.dumps({'cwd':os.getcwd(),'variables':{k:v for k,v in os.environ.items() if k in keys or k.startswith('CARGO_PKG_')},'override_audit':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in os.environ.items() if v and (k.startswith(('PHASE_','FORGE_','DYLD_')) or (k.startswith('LD_') and k!='LD_LIBRARY_PATH') or (k.startswith('CARGO_TARGET_') and k.endswith(('_RUNNER','_RUSTFLAGS','_LINKER')) and k!='CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_RUNNER') or k in ['RUSTC_WRAPPER','RUSTC_WORKSPACE_WRAPPER','CARGO_BUILD_RUSTC_WRAPPER','CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER','RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','CARGO_BUILD_RUSTFLAGS','RUSTDOCFLAGS','RUSTC_BOOTSTRAP','RUST_TEST_THREADS','RUST_TEST_NOCAPTURE'])},'argv':sys.argv[1:],'executable_sha256':hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest()},indent=2)+'\\n')\nos.execv(sys.argv[1],sys.argv[1:])\n")
capture_env=dict(E,CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_RUNNER='python3 '+str(wrapper))
capture=cargo(O/'capture-runtime',S,cmd=['cargo','+nightly-2026-04-19','test','-p','engine','--lib','--message-format=json','departure_scope_','--','--list'],env=capture_env,association=canonical_build)
assert capture['exit']==0
CTX=json.loads((O/'runtime-context.json').read_text())
assert CTX['cwd']==str(C/'crates/engine') and CTX['variables']['RUST_MIN_STACK']=='16777216'
assert CTX['executable_sha256']==artifact['executable_sha256']
assert not CTX['override_audit'],'Cargo child has an unreviewed wrapper/loader/PHASE override.'
assert CTX['variables']['CARGO_MANIFEST_DIR']==str(C/'crates/engine')
assert CTX['variables']['CARGO_MANIFEST_PATH']==str(C/'crates/engine/Cargo.toml')
assert CTX['variables']['RUSTUP_TOOLCHAIN']=='nightly-2026-04-19-x86_64-unknown-linux-gnu'
RE=dict(E,**CTX['variables'])
assert not unsafe_environment(RE,allow_runtime_loader=True)
write(O/'runtime-inputs.json',{'source_manifest_input':a.manifest,'source_manifest_input_sha256':a.manifest_sha256,'fixture_inputs_within_source':{str(C/fixture):S[fixture]},'external_fixture_inputs':EXTERNAL,'external_manifest':a.runtime_input_manifest,'external_manifest_sha256':a.runtime_input_manifest_sha256,'FORGE_TEST_FULL_DB_absent':not RE.get('FORGE_TEST_FULL_DB'),'fixture_path_authority':['crates/engine/src/test_support.rs','crates/engine/tests/integration/support.rs'],'utc':utc()})
def linked_libraries(d,exe):
 log=d/'ldd.log';cmd=['ldd',str(exe)]
 with log.open('wb') as stream:r=subprocess.run(cmd,cwd=CTX['cwd'],env=RE,stdout=stream,stderr=subprocess.STDOUT)
 output=log.read_text();assert r.returncode==0 and 'not found' not in output
 paths=set(re.findall(r'(?:=>\s+|^\s*)(/[^\s()]+)',output,re.M))
 assert paths,'No resolved ELF shared-library/interpreter paths captured.'
 files=[{'path':x,'resolved_path':str(Path(x).resolve()),'sha256':sha(x)} for x in sorted(paths)]
 result={'command':cmd,'exit':r.returncode,'cwd':CTX['cwd'],'runtime_context_sha256':sha(O/'runtime-context.json'),'log_sha256':sha(log),'executable':str(exe),'executable_sha256':sha(exe),'files':files}
 write(d/'linked-libraries.json',result);return str(d/'linked-libraries.json')
def verify_links(path):
 links=json.loads(Path(path).read_text())
 for item in links['files']:
  assert str(Path(item['path']).resolve())==item['resolved_path'] and sha(item['path'])==item['sha256']
 return sha(path)
canonical_links=linked_libraries(O/'canonical-build',canonical)
verify_links(canonical_links)
generated=[]
for build in canonical_build['build_scripts']:
 for file in Path(build['out_dir']).rglob('*'):
  if not file.is_file():continue
  raw=file.read_bytes();offset=canonical.read_bytes().find(raw)
  copy=O/('generated-'+str(len(generated))+'-'+file.name);copy.write_bytes(raw);copy.chmod(0o444)
  generated.append({'path':str(file),'sha256':sha(file),'copy':str(copy),'canonical_embedding_offset':offset,'embedded':offset>=0})
write(O/'canonical-receipt.json',{'source_manifest_sha256':canonical_build['source_manifest_sha256'],'origin_cargo_receipt':str(O/'canonical-build/receipt.json'),'origin_cargo_receipt_sha256':sha(O/'canonical-build/receipt.json'),'executable':str(canonical),'executable_sha256':sha(canonical),'artifact':artifact,'runtime_context_sha256':sha(O/'runtime-context.json'),'linked_libraries':canonical_links,'linked_libraries_sha256':sha(canonical_links),'runtime_input_manifest_sha256':sha(O/'runtime-inputs.json'),'ambient_override_audit_sha256':sha(O/'ambient-override-audit.json'),'generated_build_outputs':generated,'runtime_input_hashes':{f:S[f] for f in S if f.endswith('integration_cards.json') or f.endswith('known-tokens.toml')}})
def direct(d,exe,case,source,association,mode):
 d.mkdir(parents=True,exist_ok=False);verify(source);verify_inputs()
 assert verify_links(association['linked_libraries'])==association['linked_libraries_sha256']
 digest=sha(exe)
 for generated_file in generated:assert sha(generated_file['path'])==generated_file['sha256']
 cmd=[str(exe),case['test'],'--exact','--nocapture','--test-threads=1']
 rec={'started':utc(),'command':cmd,'cwd':CTX['cwd'],'runtime_context_sha256':sha(O/'runtime-context.json'),'executable_sha256':digest,'source_manifest_sha256':association['source_manifest_sha256'],'source_archive':association['source_archive'],'source_archive_sha256':association['source_archive_sha256'],'compilation_receipt':association['compilation_receipt'],'compilation_receipt_sha256':sha(association['compilation_receipt']),'mode':mode,'case':case,'entire_source_manifest_verified':True,'linked_libraries':association['linked_libraries'],'linked_libraries_sha256':association['linked_libraries_sha256'],'runtime_input_manifest_sha256':sha(O/'runtime-inputs.json')}
 write(d/'started.json',rec)
 with (d/'command.log').open('wb') as stream:r=subprocess.run(cmd,cwd=CTX['cwd'],env=RE,stdout=stream,stderr=subprocess.STDOUT)
 (d/'command.exit').write_text(str(r.returncode)+'\n');text=(d/'command.log').read_text(errors='replace')
 evidence=[];after_evidence=[];battle_evidence=[]
 for line in text.splitlines():
  if 'SBA_HANDOFF_EVIDENCE ' in line:evidence.append(json.loads(line.split('SBA_HANDOFF_EVIDENCE ',1)[1]))
  if 'AFTER_HISTORY_EVIDENCE ' in line:after_evidence.append(json.loads(line.split('AFTER_HISTORY_EVIDENCE ',1)[1]))
  if 'BATTLE_DEFENSIVE_EVIDENCE ' in line:battle_evidence.append(json.loads(line.split('BATTLE_DEFENSIVE_EVIDENCE ',1)[1]))
 verify(source);verify_inputs();assert sha(exe)==digest
 assert verify_links(association['linked_libraries'])==association['linked_libraries_sha256']
 rec.update(finished=utc(),exit=r.returncode,counts=counts(text),log_sha256=sha(d/'command.log'),evidence=evidence,after_history_evidence=after_evidence,battle_defensive_evidence=battle_evidence,source_and_executable_unchanged=True)
 write(d/'receipt.json',rec)
 return rec
def pass_one(r):return r['exit']==0 and len(r['counts'])==1 and r['counts'][0]['passed']==1 and r['counts'][0]['failed']==0 and r['counts'][0]['ignored']==0
def valid_sba_evidence(r,case):
 if len(r['evidence'])!=1:return False
 ev=r['evidence'][0]
 return all(ev[k]==case[k] for k in ['subject_departs','observer_departs','reverse']) and ev['life']==20+int(case['subject_departs'])
def valid_after_evidence(r,case,mutant=False):
 if case.get('evidence_kind')=='battle_defensive':
  if len(r['battle_defensive_evidence'])!=1:return False
  ev=r['battle_defensive_evidence'][0]
  records=[x['data'] for x in ev['events'] if x['type']=='ZoneChanged' and x['data']['object_id']==ev['siege'] and x['data']['from']=='Battlefield' and x['data']['to']=='Graveyard']
  if ev['final_incarnation']!=ev['initial_incarnation']+1 or len(records)!=1:return False
  rec=records[0]['record'];snapshot=rec.get('trigger_suppression')
  return snapshot is None if mutant else snapshot=={'before':[],'after':[]} and rec['co_departed']==[]
 if 'initially_live' not in case:return True
 if len(r['after_history_evidence'])!=1:return False
 ev=r['after_history_evidence'][0]
 return ev['initially_live']==case['initially_live'] and ev['life']==case['mutant_life' if mutant else 'canonical_life'] and isinstance(ev['events'],list)
def failed_one(r):return r['exit']==101 and len(r['counts'])==1 and r['counts'][0]['passed']==0 and r['counts'][0]['failed']==1 and r['counts'][0]['ignored']==0
canonical_association={k:canonical_build[k] for k in ['source_manifest_sha256','source_archive','source_archive_sha256']}
canonical_association['compilation_receipt']=str(O/'canonical-build/receipt.json')
canonical_association['linked_libraries']=canonical_links
canonical_association['linked_libraries_sha256']=sha(canonical_links)
results=[]
for row in I['rows']:
 top=O/row['id'];top.mkdir()
 cases=row['tests']
 if row['kind']=='sba':
  assert len(cases)==8
  assert {(x['subject_departs'],x['observer_departs'],x['reverse']) for x in cases}==set(itertools.product([False,True],repeat=3))
 verify(S)
 print(utc(),row['id'],'canonical baseline',flush=True)
 baseline=[direct(top/'baseline'/str(i),canonical,case,S,canonical_association,'direct_preserved_canonical_artifact') for i,case in enumerate(cases)]
 assert all(pass_one(r) and valid_after_evidence(r,case) and (row['kind']!='sba' or valid_sba_evidence(r,case)) for r,case in zip(baseline,cases)),(row['id'],'baseline setup/runtime/guard failure')
 canonical_seam_mtime=(C/row['file']).stat().st_mtime_ns
 original=(C/row['file']).read_text();(C/row['file']).write_text(H.transform(original,row['operations']))
 fmt(top/'format-mutant',False)
 mutated={f:sha(C/f) for f in S};assert [f for f in S if mutated[f]!=S[f]]==[row['file']]
 patch=''.join(difflib.unified_diff(original.splitlines(True),(C/row['file']).read_text().splitlines(True),fromfile='a/'+row['file'],tofile='b/'+row['file']))
 test_pattern=r'(?m)^#\[cfg\(test\)\]\nmod [A-Za-z0-9_]+ \{'
 before_test=re.search(test_pattern,original);after_text=(C/row['file']).read_text();after_test=re.search(test_pattern,after_text)
 assert before_test and after_test
 assert original[before_test.start():]==after_text[after_test.start():],'Mutation changed tests'
 write(top/'transformation.json',{'row':row,'changed_files':[row['file']],'tests_unchanged':True,'canonical_seam_mtime_ns':canonical_seam_mtime,'mutant_seam_mtime_ns':(C/row['file']).stat().st_mtime_ns,'test_tail_sha256':hashlib.sha256(original[before_test.start():].encode()).hexdigest()})
 print(utc(),row['id'],'fresh mutant compilation',flush=True)
 try:
  build=cargo(top/'mutant-build',mutated,patch);mutant=[]
  if build['exit']==0:
   exe=integration(build);assert not exe['fresh']
   mutant_links=linked_libraries(top/'mutant-build',exe['executable'])
   assoc={k:build[k] for k in ['source_manifest_sha256','source_archive','source_archive_sha256']};assoc['compilation_receipt']=str(top/'mutant-build/receipt.json');assoc['linked_libraries']=mutant_links;assoc['linked_libraries_sha256']=sha(mutant_links)
   mutant=[direct(top/'mutant'/str(i),exe['executable'],case,mutated,assoc,'fresh_mutant_Cargo_artifact') for i,case in enumerate(cases)]
 finally:
  restored_files=restore();assert len(restored_files)==1 and restored_files[0]['file']==row['file']
  write(top/'restoration.json',{'files':restored_files,'mutant_snapshot_mtime_ns':json.loads((top/'transformation.json').read_text())['mutant_seam_mtime_ns'],'all_source_restored':True,'comparison':'Observed file mtime before restoration versus fresh write mtime; no wall-clock comparison.'})
  assert restored_files[0]['before_write_mtime_ns']==json.loads((top/'transformation.json').read_text())['mutant_seam_mtime_ns']
 print(utc(),row['id'],'restored canonical controls',flush=True)
 restored=[direct(top/'restored'/str(i),canonical,case,S,canonical_association,'direct_preserved_canonical_artifact_after_exact_source_restoration') for i,case in enumerate(cases)]
 fmt(top/'restored-format-check',True);verify(S)
 classifications=[];required_kills=0;problems=[]
 for i,case in enumerate(cases):
  r=mutant[i] if len(mutant)>i else None
  if not pass_one(restored[i]) or not valid_after_evidence(restored[i],case) or (row['kind']=='sba' and not valid_sba_evidence(restored[i],case)):problems.append({'case':case,'problem':'restored runtime/setup failure'})
  if r is None:classifications.append({'case':case,'classification':'compile_failure_no_runtime'});continue
  text=(top/'mutant'/str(i)/'command.log').read_text(errors='replace')
  if row['kind']=='sba':
   if len(r['evidence'])!=1:problems.append({'case':case,'problem':'missing/ambiguous real-event export'});continue
   ev=r['evidence'][0]
   assert all(ev[k]==case[k] for k in ['subject_departs','observer_departs','reverse'])
   co=case['subject_departs'] and case['observer_departs']
   selected=case['subject_departs'] or (row['id']=='sba-check_lethal_damage' and case['observer_departs'])
   if co and failed_one(r) and ev['life']==20 and 'co-dying observer payoff' in text:
    classification='designated_co_dying_payoff_failure';required_kills+=1
   elif not co and selected and failed_one(r) and ev['life']==20+int(case['subject_departs']) and 'completed departure is authoritative' in text:
    classification='expected_member_snapshot_failure_after_correct_payoff'
   elif not selected and pass_one(r) and ev['life']==20+int(case['subject_departs']):
    classification='unaffected_control_pass'
   else:
    classification='unexpected_runtime_outcome';problems.append({'case':case,'problem':classification,'exit':r['exit'],'counts':r['counts']})
  else:
   if case['role']=='discriminator' and failed_one(r) and case['failure_marker'] in text and all(marker in text for marker in case.get('additional_failure_markers',[])) and valid_after_evidence(r,case,True):classification=('lower_level_defensive_contract_snapshot_failure' if row['id']=='sba-check_battle_protector' else 'private_lexical_contract_failure');required_kills+=1
   elif case['role']=='control' and pass_one(r):classification='unaffected_control_pass'
   else:classification='unexpected_runtime_outcome';problems.append({'case':case,'problem':classification})
  classifications.append({'case':case,'classification':classification})
 if required_kills==0:problems.append({'problem':'no required semantic discriminator'})
 if build['exit']!=0:problems.append({'problem':'mutant compile failed'})
 result={'id':row['id'],'baseline':baseline,'mutant_build':build,'mutant':mutant,'restored':restored,'classifications':classifications,'problems':problems,'status':'verified_required_discriminator_and_controls' if not problems else 'requires_review'}
 write(top/'outcome.json',result);results.append(result)
 print(utc(),row['id'],result['status'],flush=True)
restore()
write(O/'results.json',{'utc':utc(),'rows':results,'full_source_restored':True,'source_manifest_sha256':a.manifest_sha256,'script_sha256':sha(__file__),'inventory_sha256':a.inventory_sha256})
sys.exit(0 if all(r['status']=='verified_required_discriminator_and_controls' for r in results) else 1)
