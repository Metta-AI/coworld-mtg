import pathlib,json,re,hashlib,datetime
r=pathlib.Path('/home/ubuntu/repos/phase-verifiable-loop');e=pathlib.Path('/home/ubuntu/coworld-migration-20260904/hushbringer-v10-execution')
meta=json.loads((e/'production-path-maintainer-map-v10.json').read_text())['rows'];mapping={}
for row in meta:
 for op in row.get('operations',[]):mapping.setdefault((row['file'],op.get('function','')),[]).append(row['id'])
entries=[]
for f in sorted((r/'crates/engine/src/game').rglob('*.rs')):
 text=f.read_text().split('#[cfg(test)]\nmod tests')[0];fun=''
 for n,line in enumerate(text.splitlines(),1):
  m=re.match(r'\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+(\w+)',line)
  if m:fun=m[1]
  apis=[x for x in ['with_departure_suppression','with_departure_member','without_departure_member','with_departure_leaf'] if x+'(' in line and not re.match(r'\s*(pub\S*\s+)?fn ',line)]
  if not apis:continue
  file=str(f.relative_to(r));refs=mapping.get((file,fun),[]);classification='physical owner/member/leaf/resolver call site'
  if f.name=='sba.rs' and fun=='check_state_based_actions':refs=[x['id'] for x in meta if x['id'].startswith('sba-check')]+['augment-handoff'];classification='single SBA-iteration owner shared by all nine sub-checks and standalone Augment'
  if f.name=='engine_resolution_choices.rs':
   if 3534<=n<=3572:
    refs=[];classification='mapped unaffected native private-zone PutAtLibraryPosition sibling'
   elif n<3350:refs=['choice-sacrifice']
   elif n<3500:refs=['choice-change-bounce']
   elif n>3700:refs=['choice-pay-cost']
  if f.name=='effects/mod.rs' and fun=='resolve_ability_chain':refs=['R2-resolver-barrier']
  if file.endswith('/effects/mod.rs') and fun=='resolve_ability_chain':refs=['R2-resolver-barrier']
  if f.name=='zones.rs':refs=[x['id'] for x in meta if x['id'] in ['normal-leaf-authority','library-leaf-authority','owner-finalization','scope-before-flush','scope-capturing-ancestor-policy','leaf-top-barrier','leaf-consumes-member','member-error-closure-pop','after-world-flush','owner-allocator-reset','added-mid-leaf-flush']]
  entries.append({'file':file,'line':n,'function':fun,'api':apis[0],'classification':classification,'physical_mutation_ids':list(dict.fromkeys(refs)),'source_line':line.strip()})
unmapped=[x for x in entries if not x['physical_mutation_ids'] and 'unaffected' not in x['classification']]
assert not unmapped,unmapped
native=[{'id':'native-library-'+branch,'file':'crates/engine/src/game/engine_resolution_choices.rs','member_line':line,'first_branch':branch+' under real SelectEffectZoneCards -> PutAtLibraryPosition using Hand/Library subjects; no Battlefield candidate is captured.','selected_authority':'Real selected cards and requested library order; live zone excludes ownership.','binding_time':'Completed public selection, empty departure owner; top-level native movement retains existing order.','storage':'Native library vector and ordinary nondeath ZoneChangeRecord; absent departure suppression history.','consumer':consumer,'invalidation':'No Battlefield owner/member snapshot exists to leak; later independent creature death still gets its own snapshot.','serialized_impact':'Native nondeath event shape remains unchanged; no fabricated Some history.','test':'trigger_suppression_event_timing::hand_library_choice_preserves_selected_cards_and_nondeath_payoff','controls':'Selected card order, actual Hand->Library move and exact nondeath observer payoff; real Battlefield->Library dynamic-after twin is separately proven.','classification':'unaffected native public sibling; no mutation-kill claim and not counted among67'} for branch,line,consumer in [('Bottom',3541,'move_to_library_position(false)'),('NthFromTop',3557,'move_to_library_at_index(n-1)'),('Top-default-reversed-iteration',3572,'move_to_library_at_index(0)')]]
for row in native:
 if row['id']!='native-library-Top-default-reversed-iteration':
  row['test']=None;row['controls']='Unresolved: no verified independently reaching public Bottom/Nth test assigned. Source shows non-Battlefield subjects cannot obtain departure ownership, but this is not runtime branch/order/rejection evidence.';row['classification']='unaffected by source reasoning; required public native-arm controls unresolved';row['status']='unresolved review obligation'
 else:
  row['controls']='Actual Top fixture loops Hush/no-Hush and selection order; asserts both selected cards in Library, one Hand departure each, empty peers and missing suppression, spare in Hand, observer surviving, exact life21 and zero Spirit. It does not assert library vector order, rejected selections or Library-origin movement.';row['status']='public Top movement/payoff compatibility only; broader order/rejection obligations unresolved'
x={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'Enumerates actual calls before each file cfg(test) module; mechanical function association plus explicit repeated-arm and common-owner mapping. Physical-seam JSON supplies branch/authority/mutation/test evidence for referenced IDs.','call_sites':entries,'unmapped':unmapped,'native_unaffected_siblings':native,'scope_contract':'Only explicit live Battlefield ObjectId/incarnation candidates own actual emitted events. An unavailable nested world remains None; no fabricated empty snapshot. Closure return/Err/pause closes lexical state, while completed record history survives serde.'}
(e/'production-entry-callsite-map.json').write_text(json.dumps(x,indent=2)+'\n');print('sites',len(entries),'unmapped',len(unmapped))
