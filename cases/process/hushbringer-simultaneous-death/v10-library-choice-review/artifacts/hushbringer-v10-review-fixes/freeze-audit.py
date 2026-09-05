from pathlib import Path
import subprocess,hashlib,json,re,tarfile,difflib,datetime,collections,sys
root=Path('/home/ubuntu/repos/phase-verifiable-loop'); out=Path('/home/ubuntu/coworld-migration-20260904/hushbringer-v10-review-fixes'); old=out.parent/'hushbringer-v10-execution'; frozen=out/'frozen-source'
if (frozen/'receipt.json').exists():
 expected=json.loads((frozen/'source.json').read_text())
 assert all(hashlib.sha256((root/f).read_bytes()).hexdigest()==v for f,v in expected.items())
 print('Existing frozen source reverified after generation restore; no sealed artifacts rewritten.')
 sys.exit(0)
frozen.mkdir(exist_ok=False)
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sha(data):return hashlib.sha256(data).hexdigest()
def dump(p,obj):p.write_text(json.dumps(obj,indent=2)+'\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=root,text=True)
files=sorted(set(f for f in git('ls-files','--cached','--others','--exclude-standard','crates','Cargo.toml','Cargo.lock','rust-toolchain.toml','.cargo').splitlines() if (root/f).is_file()))
manifest={f:h(root/f) for f in files};dump(frozen/'source.json',manifest); key=h(frozen/'source.json')
assert manifest==json.loads((out/'focused-1/0-source.json').read_text())
prior=json.loads((old/'frozen-candidate-v10-final/source.json').read_text()); prior_archive=old/'source-archives/885baf9780651ece1b38291acbcfa2ab2cb766defd3fe49671ace1ca40a73d0b.tar.gz'
with tarfile.open(prior_archive) as tar:previous={f:tar.extractfile(f).read() for f in files}
assert all(sha(previous[f])==prior[f] for f in files)
changed=[f for f in files if manifest[f]!=prior[f]]
assert changed==['crates/engine/src/game/effects/change_zone.rs','crates/engine/src/game/engine_resolution_choices.rs','crates/engine/src/game/sba.rs','crates/engine/tests/integration/trigger_suppression_event_timing.rs'],changed
lineage=[];delta='';line_maps={}
for f in changed:
 a=previous[f].decode();b=(root/f).read_text();al=a.splitlines(keepends=True);bl=b.splitlines(keepends=True)
 delta+=''.join(difflib.unified_diff(al,bl,fromfile='prior-v10/'+f,tofile='review-fixes/'+f))
 if f.startswith('crates/engine/src/'):
  strip=lambda t:''.join(l for l in t.splitlines(keepends=True) if not l.lstrip().startswith('//'))
  assert strip(a)==strip(b),f
  kind='Comment lines only; all non-comment source bytes identical'
 else:
  assert b.startswith(a),f
  kind='Append-only 9 public tests and typed helper; original 7329 lines byte-identical'
 lineage.append({'file':f,'prior_sha256':prior[f],'current_sha256':manifest[f],'delta':kind})
 mappings={}
 for tag,i,j,k,l in difflib.SequenceMatcher(None,al,bl,autojunk=False).get_opcodes():
  if tag=='equal':mappings.update({x+1:k+(x-i)+1 for x in range(i,j)})
 line_maps[f]=mappings
(frozen/'review-fixes.patch').write_text(delta)
patch=git('diff','HEAD','--binary')
for f in git('ls-files','--others','--exclude-standard').splitlines():
 if (root/f).is_file():patch+=subprocess.run(['git','diff','--no-index','--binary','/dev/null',f],cwd=root,capture_output=True,text=True).stdout
(frozen/'candidate.patch').write_text(patch)
archive=out/'source-archives'/f'{key}.tar.gz';assert archive.exists()
with tarfile.open(archive) as tar:assert all(sha(tar.extractfile(f).read())==manifest[f] for f in files)
dump(frozen/'lineage.json',{'source_manifest_sha256':key,'prior_source_manifest_sha256':h(old/'frozen-candidate-v10-final/source.json'),'prior_source_archive_sha256':h(prior_archive),'historical_lineage':{'path':str(old/'frozen-candidate-v10-final/proof-lineage.json'),'sha256':h(old/'frozen-candidate-v10-final/proof-lineage.json'),'note':'Retain its exact historical mutation compilation identities; no old binary relabeled as built from review-fix source.'},'changed':lineage,'unchanged_files':len(files)-len(changed),'production_behavior_change':False,'new_mutation_claims':False})
def remap(f,n):return line_maps.get(f,{}).get(n,n)
# Full historical physical seam matrix. Preserve every measured mutation and real build identity.
a=json.loads((old/'production-path-maintainer-map-v10.json').read_text());a['status']='All 67 historical physical mutation rows retained; native library arms now have explicit public source-unaffected controls. Final verification is bound separately by the review-fix handoff receipt.';a['final_source_manifest_sha256']=key;a['review_fix_lineage']=str(frozen/'lineage.json')
for r in a['rows']:
 r['historical_source_lineage']=r.pop('source_lineage',None)
 r['source_lineage']='Historical evidence retains its original source identity. Review-fix production delta is comment-only; old integration tests remain a byte-identical prefix. See frozen-source/lineage.json.'
dump(out/'production-path-maintainer-map-v10.json',a)
(out/'production-path-maintainer-map-v10.md').write_text('# Complete production path matrix\n\nAll 67 historical mutations retain their measured source/binary/command identities. The review-fix source changes only comments and appends nine public tests. Native private-zone library arms have source-unaffected controls, with no invented mutation kill.\n\n'+ '\n'.join('## '+r['id']+'\n\n'+json.dumps(r,indent=2)+'\n' for r in a['rows']))
# Native entry map, including both real constructors and the exact first changed handler arm.
native=[]
for label,needle in [('bottom','Some(LibraryPosition::Bottom) => {'),('nth','Some(LibraryPosition::NthFromTop { n }) => {'),('top','_ => {')]:
 lines=(root/'crates/engine/src/game/engine_resolution_choices.rs').read_text().splitlines(); start=next(i for i,l in enumerate(lines) if 'EffectKind::PutAtLibraryPosition => super::zones::with_departure_suppression(' in l)
 idx=next(i for i in range(start,start+70) if needle in lines[i]); handoff=next(i for i in range(idx,idx+10) if 'with_departure_member(' in lines[i])
 tests=['native_library_choice_'+o+'_'+label+'_public_controls' for o in ['hand','library','dig_tracked']]
 native.append({'id':'native-library-'+label,'file':'crates/engine/src/game/engine_resolution_choices.rs','arm_line':idx+1,'member_line':handoff+1,'first_reaching_branch':{'bottom':'Some(Bottom) enters chosen forward loop and move_to_library_position(false)','nth':'Some(NthFromTop { n }) computes saturating n-1, iterates chosen forward and calls move_to_library_at_index(index)','top':'Default arm with natural Some(Top) iterates chosen in reverse and calls move_to_library_at_index(Some(0))'}[label],'constructors':[{'file':'crates/engine/src/game/effects/put_on_top.rs','line':224,'branch':'collected_targets.is_empty(), expected > 0, extract_in_zone Hand/Library, eligible nonempty -> natural EffectZoneChoice','tests':['native_library_choice_hand_'+label+'_public_controls','native_library_choice_library_'+label+'_public_controls']},{'file':'crates/engine/src/game/effects/put_on_top.rs','line':279,'branch':'actual Dig SelectCards publishes unkept tracked Library pool; TrackedSet scan retains Library members; collected_targets.len() > expected > 0 -> natural EffectZoneChoice','tests':['native_library_choice_dig_tracked_'+label+'_public_controls']}],'authority':'Actual constructor eligible ids and actual source zone; handler exact-cardinality, eligible membership and actual-zone guards run before owner wrapper. Tests never inject pending choices or mutate zones during a choice.','storage':'Existing WaitingFor::EffectZoneChoice and normal pending continuation; actual public SelectCards enters handler.','binding_time':'After natural cast/Dig resolution, before selected placement. No Battlefield candidate survives capture filtering.','consumer':'Existing library mover emits native Hand/Library records. with_departure_member has no owned departure binding.','invalidation':'Owner/member scopes end synchronously; pending gain continuation resolves and normal priority returns.','serialized_impact':'Selected native records have absent trigger_suppression, empty co_departed; Hand changes incarnation once, Library reposition does not.','evidence_classification':'Public source-unaffected sibling; no wrapper-removal mutation kill claimed','tests':tests,'controls':'Both orders, Hush/no-Hush; exact eligible pool/full library vectors/event order; selected records exactly one each and nonselected none; empty/short/long/ineligible/unknown choices reject with full serialized state preserved; tracked out-of-pool same-zone and kept-card rejection; valid retry; observer +1 plus continuation +2 once; normal priority, no pending continuation, zero Spirits. Nth covers 1,3,99.','limitations':'Library-to-Library notifications and payoff are inherited compatibility, not a claim of actual zone change. No duplicate-selection rejection claimed. No stale-zone rejection fixture via fabricated mutation. No BeneathTop coverage claim.','source_manifest_sha256':key})
# Verify natural constructor source lines exactly, not stale positional guesses.
plines=(root/'crates/engine/src/game/effects/put_on_top.rs').read_text().splitlines(); constructor_lines=[i+1 for i,l in enumerate(plines) if 'state.waiting_for = WaitingFor::EffectZoneChoice {' in l];assert len(constructor_lines)==2
for r in native:
 for c,n in zip(r['constructors'],constructor_lines):c['line']=n
 r['test_lines']={t:next(i+1 for i,l in enumerate((root/'crates/engine/tests/integration/trigger_suppression_event_timing.rs').read_text().splitlines()) if 'fn '+t+'(' in l) for t in r['tests']}
dump(out/'native-library-public-map.json',{'source_manifest_sha256':key,'rows':native,'prior_evidence_disposition':'Existing Brainstorm CastSpell/SelectCards proves natural Hand Top order. Existing put_on_top unit Nth is direct populated-target resolver, not natural handler proof; Volcanic Spite prompt-only test does not prove a selected arm. Separate battlefield library leaf mutation stays separate.','focused_receipt':str(out/'focused-1/receipt.json')})
a=json.loads((old/'production-entry-callsite-map.json').read_text());a['source_manifest_sha256']=key;a['method']+=' Review fixes refresh all line locations, preserve all physical mappings, and attach exact native arm/public controls.'
for r in a['call_sites']:
 r['line']=remap(r['file'],r['line'])
 if 'unaffected native' in r['classification']:
  r['native_map_ids']=[n['id'] for n in native if r['api']=='with_departure_suppression' or r['line']==n['member_line']]
  assert r['native_map_ids']
  r['tests']=[t for n in native if n['id'] in r['native_map_ids'] for t in n['tests']]
dump(out/'production-entry-callsite-map.json',a)
a=json.loads((old/'typed-common-boundary-map.json').read_text());a['source_manifest_sha256']=key;a['review_fix_lineage']=str(frozen/'lineage.json');dump(out/'typed-common-boundary-map.json',a)
# Honest constructor categories: function return braces are not expressions; cfg(test) applies lexically, not from first occurrence to EOF.
a=json.loads((old/'manual-constructor-boundary-audit.json').read_text());a['source_manifest_sha256']=key;a['prior_literal_audit_method']=a['literal_audit_method'];a['literal_audit_method']='Full unchanged constructor syntax sweep plus manual expression/function-result discrimination and lexical cfg(test)/external-module classification. Corrects two prior return-signature false positives and test/production categories.'
constructors=[]
for r in a['constructors']:
 if (r['file'],r['line']) in [('crates/engine/src/game/game_object.rs',1498),('crates/engine/src/game/stack.rs',2493)]:
  a['non_constructor_hits'].append({'file':r['file'],'line':r['line'],'reason':'Function return signature opening brace, not a ZoneChangeRecord literal'});continue
 if Path(r['file']).name in ['casting_tests.rs','engine_exile_return_tests.rs','triggers_dedup_regression_tests.rs','triggers_ordering_parity_tests.rs','triggers_push_first_contract_tests.rs']:
  r['scope']='test';r['scope_basis']='External file included only by #[cfg(test)] #[path] module in casting.rs/engine.rs/triggers.rs, inspected at source'
 if r['file']=='crates/engine/src/game/game_object.rs' and r['line']==1499:
  r['scope']='production';r['scope_basis']='GameObject impl snapshot_for_zone_change; earlier cfg(test) annotates only _gameobject_partition_is_total, not this impl'
 if r['scope']=='production':
  r['category']={'filter.rs':'Synthetic LKI filter record with None; no event capture authority','stack.rs':'Synthetic token batching/probe record with None; no death capture authority','game_object.rs':'Real reusable snapshot constructor initializes None; owned emitted events acquire capture later'}[Path(r['file']).name]
 else:r['category']='Test-only record fixture/update; no production constructor reachability claim'
 constructors.append(r)
# Raw regex also sees a documentation example and two golden-string entries.
for f,n,reason in [('crates/engine/src/types/game_state.rs',835,'Documentation example, not executable literal'),('crates/engine/tests/integration/loop_shortcut.rs',65,'Two occurrences inside raw golden Debug string, not executable literals')]:
 a['non_constructor_hits'].append({'file':f,'line':n,'reason':reason,'occurrences':2 if n==65 else 1})
# The cfg(test) constructor spells its literal Self rather than ZoneChangeRecord.
self_lines=(root/'crates/engine/src/types/game_state.rs').read_text().splitlines()
constructors.append({'file':'crates/engine/src/types/game_state.rs','line':840,'syntax':'Self','body_sha256':sha(('\n'.join(self_lines[839:872])+'\n').encode()),'trigger_suppression_value':'None','struct_update':False,'scope':'test','category':'cfg(test) ZoneChangeRecord::test_minimal Self constructor; mechanical None default','scope_basis':'impl ZoneChangeRecord is cfg(test), source lines831-872'})
a['raw_regex_audit']=str(out/'complete-constructor-regex-hits.json')
a['constructors']=constructors;a['counts']={'constructors':len(constructors),'named_constructor_expressions':len(constructors)-1,'self_constructor_expressions':1,'raw_regex_occurrences':92,'non_constructor_occurrences':11,'non_constructor_hits':len(a['non_constructor_hits']),'scopes':dict(collections.Counter(r['scope'] for r in constructors))};a['scope_classification_note']='Source directory placement does not establish production scope. Exactly three production constructor expressions: filter LKI adapter, GameObject snapshot, stack token probe. All external test modules are test-only. None is mechanical initialization, not new capture authority.'
for f,v in a['changed_files'].items():
 v['sha256']=manifest[f]
 if f=='crates/engine/src/game/derived_views.rs':v['classification']='Test-only fixture adds mechanical None; no production behavior change'
dump(out/'manual-constructor-boundary-audit.json',a)
# Fresh complete raw search, preserving category distinctions above.
prior_sweep=json.loads((old/'final-source-audit-3/constructor-consumer-sweep.json').read_text()); patterns={'record_constructors':'ZoneChangeRecord {','selection_constructors':'DeferredSacrificeSelection {','component_consumers':'deferred_sacrificed_permanents','scope_consumers':'departure_suppression_scope','before_helper':'death_suppressed_before(','after_helper':'death_suppressed_after(','ordinary_adapter':'match_for_ordinary_collection(','active_suppression':'active_suppress_trigger_statics(','owner':'with_departure_suppression(','member':'with_departure_member(','resolver_barrier':'without_departure_member(','old_marker':'mark_simultaneous_departures(','old_stamp':'stamp_simultaneous_from_slice('}
sweep={k:[] for k in patterns}
for f in files:
 if f.endswith('.rs'):
  for n,l in enumerate((root/f).read_text().splitlines(),1):
   for k,p in patterns.items():
    if p in l:sweep[k].append({'file':f,'line':n,'text':l})
dump(out/'constructor-consumer-sweep.json',{'source_manifest_sha256':key,'searches':sweep,'method':'Fresh raw text sweep; constructor expressions and production/test semantics classified separately in manual-constructor-boundary-audit.json. Function signatures and call patterns are not automatically proof.'})
# Full CR gate, keeping every moved line, adding native adjacent block and correcting shorthand parsing.
a=json.loads((out/'cr-complete-draft.json').read_text());lines=(root/'crates/engine/src/game/engine_resolution_choices.rs').read_text().splitlines();n=next(i for i,l in enumerate(lines) if '// CR 115.1: Resolution-time selection for PutAtLibraryPosition' in l);a['annotations'].append({'file':'crates/engine/src/game/engine_resolution_choices.rs','line':n+1,'text':lines[n],'context':'\n'.join(lines[n:n+6]),'category':'affected adjacent native comment','rules':['115.1']})
rulelines=(root/'docs/MagicCompRules.txt').read_text().splitlines();a['rules'].pop('535',None)
for r in a['annotations']:
 r['rules']=[x for x in r['rules'] if x!='535']
 if '704.5a-c' in r['context']:r['rules']=sorted(set(r['rules']+['704.5b','704.5c']))
 r['semantic_assessment']='Verified full comment context against cited checked-in rule text and source. Mechanical pause/record plumbing implements the described authority; citations do not promote known deferred behavior.'
 if any(x in r['rules'] for x in ['310.7','310.8','704.5v','704.5w']):r['semantic_assessment']='Siege-only pending-trigger rule distinguished from unconditional non-Siege zero-defense rule. Source explicitly preserves inherited broader guard as compatibility limit, no behavior change claimed.'
for x in ['115.1','704.5b','704.5c','400.3','614.3']:
 a['rules'][x]=[l for l in rulelines if re.match(re.escape(x)+r'(?:\. | )',l)]
a['missing']=[];a['source_manifest_sha256']=key;a['rules_sha256']=h(root/'docs/MagicCompRules.txt');a['semantic_review']='Fresh executor read all full rule texts and all added/moved/adjacent annotation contexts. Five independent findings corrected, all remaining annotations retained after semantic verification. Range and slash shorthand expanded. Issue #535 excluded as an issue id, not a CR citation.';a['removed_inaccurate_annotations']=[{'file':'crates/engine/src/game/effects/change_zone.rs','prior_line':1560,'rule':'400.3','resolution':'Removed unrelated destination-ownership citation; source-zone plumbing text retained.'},{'file':'crates/engine/src/game/sba.rs','prior_line':189,'rule':'614.3 / 701.19b','resolution':'Use regeneration replacement 614.8 and replacement-choice 616.1; adjacent generic shield references also use614.8.'}];a['reviewed_annotation_count']=len(a['annotations']);a['moved_comment_exclusion']=False;dump(out/'cr-complete-audit.json',a)
(out/'cr-complete-audit.md').write_text('# Full CR annotation gate\n\nEvery added or moved CR-bearing diff line and the affected adjacent annotation regions are included. The source-zone citation was removed; regeneration, Roles, protector selection and the inherited broad zero-defense guard are corrected. The unchanged non-Siege guard remains an explicit compatibility limit. The full JSON contains every location, context, expanded reference, full rule text and semantic assessment.\n\n'+str(len(a['annotations']))+' annotations reviewed; no unresolved citation finding.\n')
dump(frozen/'receipt.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base':git('rev-parse','HEAD').strip(),'branch':git('branch','--show-current').strip(),'source_manifest_sha256':key,'source_archive':str(archive),'source_archive_sha256':h(archive),'source_files':len(files),'candidate_patch_sha256':h(frozen/'candidate.patch'),'review_fixes_patch_sha256':h(frozen/'review-fixes.patch'),'lineage_sha256':h(frozen/'lineage.json'),'cr_audit_sha256':h(out/'cr-complete-audit.json'),'focused_receipt_sha256':h(out/'focused-1/receipt.json'),'card_generation_receipt':str(out/'card-data-final/receipt.json'),'card_generation_status_at_freeze':'pending; final handoff binds completed receipt separately'})
print(json.dumps({'source':key,'changed_files':changed,'constructors':len(constructors),'scopes':a.get('counts'),'cr_annotations':len(a['annotations'])}))
