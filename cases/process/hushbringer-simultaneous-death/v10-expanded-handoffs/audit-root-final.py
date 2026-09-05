from pathlib import Path
import json,hashlib,tarfile,re,importlib.util,datetime,subprocess
b=Path('/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations');r=b/'expanded-v10-root-attempt-1';c=Path('/home/ubuntu/repos/phase-hushbringer-mutations')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
S=json.loads(Path('/home/ubuntu/coworld-migration-20260904/hushbringer-v10-execution/frozen-candidate-v10/source.json').read_text())
result=json.loads((r/'results.json').read_text());I=json.loads((b/'expanded-v10-inventory.json').read_text());rows={x['id']:x for x in I['rows']}
helper=Path('/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/mutation-tools.py');spec=importlib.util.spec_from_file_location('mh',helper);h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
def archive(rec):
 assert sha(rec['source_manifest'])==rec['source_manifest_sha256'];source=json.loads(Path(rec['source_manifest']).read_text());assert set(source)==set(S)
 assert sha(rec['source_archive'])==rec['source_archive_sha256']
 with tarfile.open(rec['source_archive']) as ar:
  assert set(ar.getnames())==set(source);data={name:ar.extractfile(name).read() for name in source}
 assert {name:hashlib.sha256(value).hexdigest() for name,value in data.items()}==source
 return source,data
canonical=json.loads((r/'canonical-build/receipt.json').read_text());cs,cb=archive(canonical);assert cs==S
crec=json.loads((r/'canonical-receipt.json').read_text());assert sha(r/'canonical-integration')==crec['executable_sha256']
audit=[]
for resultrow in result['rows']:
 row=rows[resultrow['id']];mut=resultrow['mutant_build'];ms,mb=archive(mut);assert mut['exit']==0
 artifacts=[x for x in mut['artifacts'] if x['target']['name']=='integration' and x['executable']];assert len(artifacts)==1 and not artifacts[0]['fresh']
 changed=[x for x in S if ms[x]!=S[x]];assert changed==[row['file']]
 original=cb[row['file']].decode();actual=mb[row['file']].decode();expected=h.transform(original,row['operations'])
 fmt=subprocess.run(['/home/ubuntu/.cargo/bin/rustup','run','nightly-2026-04-19','rustfmt','--edition','2021','--emit','stdout'],input=expected,cwd=c,capture_output=True,text=True,check=True)
 assert fmt.stdout==actual,row['id']
 before=re.search(r'(?m)^#\[cfg\(test\)\]\nmod [A-Za-z0-9_]+ \{',original);after=re.search(r'(?m)^#\[cfg\(test\)\]\nmod [A-Za-z0-9_]+ \{',actual)
 assert original[before.start():]==actual[after.start():]
 n=0
 for phase in ['baseline','mutant','restored']:
  for i,run in enumerate(resultrow[phase]):
   log=r/row['id']/phase/str(i)/'command.log';assert sha(log)==run['log_sha256']
   expected_exe=artifacts[0]['executable_sha256'] if phase=='mutant' else crec['executable_sha256'];assert run['executable_sha256']==expected_exe
   assert run['source_manifest_sha256']==(mut['source_manifest_sha256'] if phase=='mutant' else canonical['source_manifest_sha256'])
   assert run['source_archive_sha256']==(mut['source_archive_sha256'] if phase=='mutant' else canonical['source_archive_sha256'])
   assert run['runtime_context_sha256']==sha(r/'runtime-context.json')
   assert sha(run['compilation_receipt'])==run['compilation_receipt_sha256']
   assert sha(run['linked_libraries'])==run['linked_libraries_sha256']
   assert run['cwd']==str(c/'crates/engine')
   assert len(run['counts'])==1 and run['counts'][0]['ignored']==0;n+=1
 assert resultrow['status']=='verified_required_discriminator_and_controls'
 audit.append({'id':row['id'],'archive_files_verified':len(S),'changed_files':changed,'exact_defined_transform_after_same_pinned_formatter':True,'test_module_bytes_unchanged':True,'fresh_mutant_integration_artifact':True,'independent_run_records_verified':n,'status':resultrow['status'],'outcome_sha256':sha(r/row['id']/'outcome.json')})
out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Root mechanical source/archive/build/run identity audit; not independent implementation review. Expected transform is formatted through pinned rustfmt and compared byte-for-byte. Mutant binaries are identified by compile/runtime receipts and are not claimed retained after target reuse.','canonical_files_verified':len(S),'results_sha256':sha(r/'results.json'),'rows':audit,'commands_verified':sum(x['independent_run_records_verified'] for x in audit),'all_current_source_restored':all(sha(c/p)==v for p,v in S.items())}
(r/'root-archive-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'rows':len(audit),'commands_verified':out['commands_verified'],'audit_sha256':sha(r/'root-archive-audit.json')}))
