import pathlib,re,json,hashlib,datetime,subprocess
r=pathlib.Path('/home/ubuntu/repos/phase-verifiable-loop');e=pathlib.Path('/home/ubuntu/coworld-migration-20260904/hushbringer-v10-execution');manifest=json.loads((e/'frozen-candidate-v10-final/source.json').read_text())
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
# Strip comments and strings while preserving offsets for balanced-brace construction audit.
def mask(s):
 out=list(s);i=0
 while i<len(s):
  if s.startswith('//',i):
   j=s.find('\n',i);j=len(s) if j<0 else j
  elif s.startswith('/*',i):
   depth=1;j=i+2
   while j<len(s) and depth:
    if s.startswith('/*',j):depth+=1;j+=2
    elif s.startswith('*/',j):depth-=1;j+=2
    else:j+=1
  elif s[i]=='"':
   j=i+1
   while j<len(s):
    if s[j]=='\\':j+=2
    elif s[j]=='"':j+=1;break
    else:j+=1
  else:i+=1;continue
  for k in range(i,min(j,len(s))):
   if out[k]!='\n':out[k]=' '
  i=j
 return ''.join(out)
constructors=[];skips=[]
for f in manifest:
 if not f.endswith('.rs'):continue
 s=(r/f).read_text();m=mask(s)
 for hit in re.finditer(r'\bZoneChangeRecord\s*\{',m):
  line=s.count('\n',0,hit.start())+1;prefix=m[max(0,m.rfind('\n',0,hit.start())+1):hit.start()]
  if re.search(r'(struct|impl)\s+$|->\s*&?\s*$',prefix):skips.append({'file':f,'line':line,'reason':'declaration/impl/function result body'});continue
  start=m.index('{',hit.start());depth=1;end=start+1
  while depth and end<len(m):
   depth+=(m[end]=='{')-(m[end]=='}');end+=1
  body=s[start+1:end-1];mb=m[start+1:end-1];field=re.search(r'\btrigger_suppression\s*:\s*([^,\n]+)',body)
  constructors.append({'file':f,'line':line,'body_sha256':hashlib.sha256(body.encode()).hexdigest(),'trigger_suppression_value':field.group(1).strip() if field else None,'struct_update':bool(re.search(r'\.\.\s*[*&]?\s*\w',mb)),'scope':'test' if '/tests/' in f or ('#[cfg(test)]' in s[:hit.start()]) else 'production'})
missing=[x for x in constructors if x['trigger_suppression_value'] is None and not x['struct_update']]
# Classify all changed files, including untracked modules, using actual diff paths.
changed=json.loads((e/'final-source-audit-3/constructor-consumer-sweep.json').read_text())['changed_files']
classifications={}
for f in changed:
 if f.startswith('crates/engine/tests/') or f.endswith('/test_helpers.rs') or '/casting_tests/' in f or f.endswith('/engine_exile_return_tests.rs'):kind='test fixtures/registered module and mechanical event literal carry-through'
 elif f.endswith('/trigger_suppression.rs'):kind='typed suppression authority helper; cfg(test) private authority matrix'
 elif f.endswith('/casting_costs.rs'):kind='deferred sacrifice component provenance, guards, complete component owner/member grouping and tests'
 elif f.endswith('/game_state.rs'):kind='event snapshot and component schema; serde-skipped lexical state; constructors/normalization/tests'
 elif f.endswith('/pending_cast.rs'):kind='opaque deferred component validation helper and tests'
 elif f.endswith('/haunt.rs'):kind='production dedicated haunted-creature death matcher before-snapshot suppression gate'
 elif f.endswith(('/derived_views.rs','/game_object.rs')):kind='mechanical ZoneChangeRecord None initialization; no new capture authority'
 elif f.endswith('/mod.rs') and '/game/mod.rs' in f:kind='module registration'
 else:kind='production authority/owner/member/consumer change plus existing tests; see physical seam map and diff'
 classifications[f]={'sha256':changed[f],'classification':kind}
x={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_manifest_sha256':h(e/'frozen-candidate-v10-final/source.json'),'literal_audit_method':'Balanced braces after removing comments and strings; exclude struct/impl and return-type function bodies; retain exhaustive literals and struct-update sites. Compiler checks remain authoritative for exhaustiveness.','constructors':constructors,'non_constructor_hits':skips,'unaccounted_literals':missing,'changed_files':classifications}
dump(e/'manual-constructor-boundary-audit.json',x);print('constructors',len(constructors),'skips',len(skips),'unaccounted',missing)
