import datetime, hashlib, json, pathlib, re, subprocess, sys
root=pathlib.Path('/home/ubuntu/repos/phase-verifiable-loop');out=pathlib.Path(sys.argv[1]);out.mkdir(exist_ok=False)
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=root,text=True)
files=sorted(set(git('ls-files','--cached','--others','--exclude-standard','crates','Cargo.toml','Cargo.lock','rust-toolchain.toml','.cargo').splitlines()));files=[f for f in files if (root/f).is_file()];manifest={f:h(root/f) for f in files};(out/'source.json').write_text(json.dumps(manifest,indent=2)+'\n')
base='2dec6c88915db4697706234a7ba2fcedd97b1689';changed=sorted(set(git('diff','--name-only',base).splitlines()+git('ls-files','--others','--exclude-standard').splitlines()));changed=[f for f in changed if (root/f).is_file()]
# Include every untracked source module in the diff audit.
oldtexts={}
for f in files:
 if not f.endswith(".rs"):continue
 try:oldtexts[f]=subprocess.check_output(['git','show',base+':'+f],cwd=root,text=True,stderr=subprocess.DEVNULL)
 except subprocess.CalledProcessError:oldtexts[f]=''
base_comments={line.strip() for text in oldtexts.values() for line in text.splitlines() if 'CR ' in line}
annotations=[]
for f in changed:
 if not f.endswith('.rs'):continue
 for i,line in enumerate((root/f).read_text().splitlines(),1):
  if 'CR ' in line and line.strip() not in base_comments:
   ids=re.findall(r'\b\d{3}\.\d+[a-z]?\b',line);annotations.append({'file':f,'line':i,'text':line,'ids':ids})
rules_path=root/'docs/MagicCompRules.txt';rulelines=rules_path.read_text().splitlines();rules={};missing=[]
for ident in sorted({x for a in annotations for x in a['ids']}):
 found=[line for line in rulelines if line.startswith(ident+'.') or line.startswith(ident+' ')]
 if not found:missing.append(ident)
 rules[ident]=found
(out/'cr-annotation-audit.json').write_text(json.dumps({'source_manifest_sha256':h(out/'source.json'),'rules_sha256':h(rules_path),'annotations':annotations,'rules':rules,'missing':missing,'method':'Novel CR-bearing source lines compared to base comment text across all source files; includes untracked files and excludes verbatim moved comments. Semantic assessment is recorded separately.'},indent=2)+'\n')
searches={}
for key,pattern in [('record_constructors','ZoneChangeRecord {'),('selection_constructors','DeferredSacrificeSelection {'),('component_consumers','deferred_sacrificed_permanents'),('scope_consumers','departure_suppression_scope'),('before_helper','death_suppressed_before('),('after_helper','death_suppressed_after('),('ordinary_adapter','match_for_ordinary_collection('),('active_suppression','active_suppress_trigger_statics('),('owner','with_departure_suppression('),('member','with_departure_member('),('resolver_barrier','without_departure_member('),('old_marker','mark_simultaneous_departures('),('old_stamp','stamp_simultaneous_from_slice(')]:
 hits=[]
 for f in files:
  if not f.endswith('.rs'):continue
  for n,line in enumerate((root/f).read_text().splitlines(),1):
   if pattern in line:hits.append({'file':f,'line':n,'text':line})
 searches[key]=hits
(out/'constructor-consumer-sweep.json').write_text(json.dumps({'source_manifest_sha256':h(out/'source.json'),'changed_files':{f:h(root/f) for f in changed},'searches':searches},indent=2)+'\n')
print(json.dumps({'changed_files':len(changed),'novel_cr_annotations':len(annotations),'rule_ids':len(rules),'missing_rule_ids':missing,'search_counts':{k:len(v) for k,v in searches.items()}},indent=2))
