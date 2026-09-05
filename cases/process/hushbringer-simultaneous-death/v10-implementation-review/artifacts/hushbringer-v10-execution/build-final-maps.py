import pathlib,json,hashlib,datetime,re
b=pathlib.Path('/home/ubuntu/coworld-migration-20260904');e=b/'hushbringer-v10-execution'
def load(p):return json.loads(pathlib.Path(p).read_text())
def h(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':str(p),'sha256':h(p)}
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
rows=load(e/'physical-seam-map-draft.json')['rows'];idx={r['id']:r for r in rows}
for r in rows:
 for k in ['status','transformation_dry_run','evidence_status']:r.pop(k,None)
 r['evidence']=[]
def attach(id,p,data,kind):
 r=idx[id];r['evidence'].append({'kind':kind,'artifact':ref(p),'row':data})
public=b/'hushbringer-v9-public-root-audit-final.json'
for x in load(public)['rows']:attach(x['id'],public,x,'original public runtime; fresh mutant/restored compilations')
# Keep imported source binding and every exact command/log/count/assertion; omit redundant compiler blocks only.
def shrink(x):
 if isinstance(x,list):return [shrink(v) for v in x]
 if isinstance(x,dict):return {k:shrink(v) for k,v in x.items() if k not in ['compiler_artifacts','compiler_artifact','fresh_engine_artifacts','fresh_engine_rebuilds','binary_binding']}
 return x
for n in ['hushbringer-v9-matcher-mutations/audited-results.json','hushbringer-v10-batched-mutations/audited-results.json']:
 p=b/n
 for x in load(p)['rows']:
  id=x['mutation']['row']['id'];attach(id,p,shrink(x),'public runtime; exact source-bound canonical reuse explicitly labeled per phase')
  if 'batched-mutations' in n:
   idx[id]['tests']=x['mutation']['row']['designated']
   idx[id]['independently_run_controls']=x['mutation']['row']['controls']
   idx[id]['fixture_map']=x['mutation']['row']['fixture_map']
libmap=b/'hushbringer-v9-library-mutations/production-path-maintainer-map-final.json'
for x in load(libmap)['rows']:
 r=idx[x['id']];r['independent_structural_map']=dict(x,artifact=ref(libmap))
 for old,new in [('selected_authority','selected_authority'),('binding_time','binding_time'),('storage','storage'),('consumers','consumer'),('invalidation','invalidation'),('serialized_surface','serialized_impact'),('first_branch','first_reaching_branch'),('hostile','hostile_and_sibling_controls'),('production_entry','production_entry')]:r[new]=x[old]
lib=b/'hushbringer-v9-library-mutations/original-nineteen-proof-index.json'
for x in load(lib)['rows']:attach(x['row']['id'],lib,x,'original library/SBA comparison, including three historical survivors')
supp=b/'hushbringer-v9-library-mutations/lexical-battle-v10-attempt-1/results.json'
for x in load(supp)['rows']:attach(x['id'],supp,x,'v10 private lexical or defensive battle exact runtime discriminator')
root=b/'hushbringer-v9-library-mutations/expanded-v10-root-attempt-1'
inv=b/'hushbringer-v9-library-mutations/expanded-v10-inventory.json'
for x in load(inv)['rows']:
 if x['id'] not in idx:
  side='before' if x['id'].startswith('before') else 'after';r=dict(x,evidence=[],evidence_classification='public runtime mutation',selected_authority='Authoritative Some(snapshot) selected '+side+' vector; live functioning suppression only when the optional history is absent.',binding_time='Snapshot captured at the actual completed departure; clause classification selects the side at matching. None alone consults present functioning statics.',storage='ZoneChangeRecord.trigger_suppression: Option<TriggerSuppressionSnapshot>; canonical enum vectors.',consumer='death_suppressed_'+side+' -> zone_change_clause_matches -> ordinary/delayed collection and exact public payoff.',invalidation='Serialized event authority is immutable; later actions and another incarnation cannot replace it. No ongoing cache is introduced.',serialized_impact='Some(empty), Some(Dies), asymmetric sides and None remain distinct through serde; helper does not rewrite the record.',first_reaching_branch='Actual '+side+'-timed clause on a real creature departure, followed by later source arrival/departure so live authority disagrees with captured history.',hostile_and_sibling_controls='Independent unchanged-world no-Hush Oracle Wrath plus both contradictory historical/live worlds.',source_lineage='Tests and production are exactly those in released v10 manifest3016; final appended Battle controls do not modify these bytes.')
  rows.append(r);idx[r['id']]=r
 p=root/x['id']/'outcome.json'
 if p.exists():attach(x['id'],p,load(p),'expanded v10 public per-order/per-control comparison')
 else:idx[x['id']]['pending']='root outcome not yet present'
# Five exact R2/R3 seams preserve old matching semantics while repairing fixture authority.
p=b/'hushbringer-v9-r2-r3-mutations/audited-results.json'
meta={
'R2-resolver-barrier':('resolve_ability_chain resolver wrapper','Public two-target ChangeZone replacement tail -> child explicit SelfRef Sacrifice of the same live incarnation; parent owns Y only.','Top explicit None member barrier, selected parent candidates and actual child/parent event keys.','At independent resolver-chain entry before any callback can consume a member binding.','Serde-skipped lexical binding stack plus final event-local snapshot/peers.','with_departure_leaf and claim_departure_event; public X-None/Y-singleton assertions.','Barrier pops at synchronous return; no ancestor lookup through None.','Only actually owned event history persists; no lexical token serialized.','Redirect-only no-departure and existing nested independent-cause control; both exact same-incarnation orders.','Remove only resolver entry wrapper, keeping resolver body and owner/member implementation.'),
'R3-original-entry-exit-lki':('filter original-entry exit-LKI gate','Public entry trigger responds with typed temporary +2/+2 then bounce; original entered incarnation no longer on Battlefield.','Original entry event and matching exit LKI, including effective3/3, against live2/2 source.','Entry records incarnation; exit records its actual evaluated characteristics before cleanup.','Existing event snapshot/exit LKI and original-incarnation association.','object-condition power comparison at trigger resolution.','After departure do not read reset live1/1; unrelated incarnation cannot replace original exit history.','Existing event/LKI serialization unchanged.','Existing departed/bounced/reentered conditions and public baseline+1 control.','Revert only original-entry exit-LKI fallback; unchanged test source.'),
'R3-original-entry-incarnation':('filter original-entry incarnation gate','Same public entry-trigger response followed by actual leave and same-ID reentry with a new incarnation.','Original entered incarnation exit3/3, not new live1/1 sharing ObjectId.','Bind entry incarnation at trigger creation and resolve against its own later exit.','Existing entry/exit LKI and ObjectId plus incarnation.','object-condition power comparison.','New incarnation is not evidence for the original entry.','No new schema in this seam.','Original-entry departed/bounced siblings and exact public reentry+1.','Revert only original-incarnation guard; unchanged test source.'),
'R3-bounce-exit-controller':('filter parent-target exit controller','Real control spell makes P0 controller of P1-owned creature, then public bounce followed by conditional draw.','Effective controller at exit P0, not reset owner P1 after bounce.','Capture evaluated controller before battlefield departure.','Existing exit LKI in parent-target context.','Conditional bounce follow-up Draw.','Zone reset cannot alter historical controller.','Existing LKI surface unchanged.','No-theft and existing bounce target-controller tests.','Revert only use of exit controller for parent-target condition.'),
'R3-oversimplify-exit-controller':('filter per-controller exit power','Real theft spell followed by real Oracle Oversimplify; actual exile and per-player Fractal creation.','Each departed creature effective controller and power at exit.','Evaluate typed control effect before exile; retain exit history after owner reset.','Existing event/LKI and per-player iteration context.','Oversimplify EventContext power sum and Fractal counters.','Later live owner/controller reset cannot rebucket departed power.','No new schema in this seam.','No-theft7/3 executes first; theft expects5/5, mutant first P0 is7 versus5; later P1 assertion unexecuted.','Revert only per-controller exit-LKI authority for power summation.')}
for x in load(p)['seams']:
 m=meta[x['id']];r={'id':x['id'],'file':x['file'],'physical_seam':m[0],'production_entry':m[1],'selected_authority':m[2],'binding_time':m[3],'storage':m[4],'consumer':m[5],'invalidation':m[6],'serialized_impact':m[7],'hostile_and_sibling_controls':m[8],'description':m[9],'first_reaching_branch':m[1],'evidence_classification':'public runtime mutation with retained original lower-level test siblings','evidence':[]}
 tests=[]
 for ph in x['phases']:
  for t in ph['tests']:
   cmd=t['command']; pos=cmd.index('--lib')+1 if '--lib' in cmd else cmd.index('--test')+2
   if cmd[pos] not in tests:tests.append(cmd[pos])
 r['tests']=tests;r['exact_transformation_receipt']=ref(b/'hushbringer-v9-r2-r3-mutations'/(r['id']+'-mutation.json'));r['source_lineage']='Frozen v9; old source/test associations retained. V10 only appends reviewed tests.';rows.append(r);idx[r['id']]=r;attach(r['id'],p,shrink(x),'five-seam original public/lower-level baseline/mutant/restored fresh compile comparisons')
# Specialized authority descriptions must not inherit generic matcher text.
idx['before-live-subject-authority'].update(selected_authority='Effective functioning static source/controller/condition/ability plus live pre-departure subject attachment and combat relations.',binding_time='Owner entry, after one before-world layer evaluation and before any member leaves.',storage='Per-candidate typed before outcomes captured in owner frame; eventual event snapshot.before.',consumer='outcomes_for_live_subject -> finish_departure_suppression -> before-selected trigger clauses.',invalidation='Subject relation is bound before departure; later detach/combat cleanup cannot replace it.',first_reaching_branch='Public attachment-relative suppression and actual combat-dependent suppression positively match only the live pre-departure relation.',serialized_impact='Captured enum outcomes only; no live relation graph copied.')
idx['haunt-adapter'].update(selected_authority='Established exiled Haunt source -> haunted ObjectId link, actual creature death and event before suppression.',binding_time='Source/link setup precedes death; suppression chosen from completed departure before history at matching.',consumer='Dedicated match_haunt matcher -> ordinary trigger registration and exact exiled-source payoff.',first_reaching_branch='Real Haunt link with source in Exile and haunted creature actually departing; surviving Hush directly discriminates adapter.',hostile_and_sibling_controls='No-Hush exact payoff; missing/other link; sequential both orders; simultaneous Wrath both insertion orders.')
idx['unattach-adapter'].update(selected_authority='Actual previously attached source/subject relation and death-caused Unattach event with departure before history.',binding_time='Relation and suppression before death; matching follows native detach emission.',consumer='Dedicated death-caused Unattach branch -> exact triggered payoff.',hostile_and_sibling_controls='Native detach for nondeath remains unchanged; no-Hush and surviving/co-dying Hush cases prove matching.')
branches={
'before-clause-gate':'TriggerMode ChangesZone/ChangesZoneAll or LeavesBattlefield selects zone matching; actual ZoneChanged; nonempty clauses take precedence over scalar origin_zones/origin. Matching origin/destination/valid_card plus actual Battlefield->Graveyard reaches OriginConstraint::Equals(Battlefield) and the before predicate.',
'any-clause-after-to-before':'Actual ZoneChanged and matching ChangesZone clause reaches Battlefield->Graveyard with OriginConstraint::Any; surviving observer is not SelfRef destination-functioning source, so !self_arrival selects after.',
'ambiguous-origin-before-misclassification':'ChangesZone ordinary adapter supplies Some(live active slice); nonempty complementary OneOf clause or scalar origin_zones passes matches_from and reaches OneOf/NotEquals arm after actual Battlefield->Graveyard. Co-dying Hush absent at collection permits exact payoff.',
'ambiguous-origin-after-approximation':'Same OneOf/NotEquals dispatch, but real subject-first death retains Dies after history while later Hush departure makes ordinary live slice empty before collection; this specifically distinguishes current live from captured after.',
'delayed-ambiguous-live-gate':'Registered WhenNextEvent/WheneverEvent registry invokes match_changes_zone with None compatibility context; actual ZoneChanged then OneOf/NotEquals arm sees None and preserves ungated delayed matching. Surviving Hush is the discriminator.',
'ordinary-adapter':'collect_matching_triggers_inner passes source/functioning/zone checks, then calls ordinary adapter; TriggerMode::ChangesZone routes to contextual matcher with Some(active). Actual matching ambiguous creature death beside surviving Hush is filtered before registration.',
'batched-adapter':'A matching noncreature N event passes the outer ordinary gate and trig_def.batched=true enters matching_batched_trigger_events. Each candidate passes the ETB-only filter, then ChangesZone adapter supplies Some(active) to OneOf(Battlefield); surviving Hush excludes creature C. Exact native singleton N/countSome(1) becomes C+N/countSome(2) under only inner-adapter removal.',
'ordinary-global-death-gate':'collect_pending_triggers outer event prefilter is ETB-only. Actual Battlefield->Graveyard must reach destination-functioning self ChangesZone Any clause rather than be globally discarded; source_id==record.object_id, SelfRef, and trigger_zones contains Graveyard.',
'batched-global-death-gate':'Source is dying card functioning in Graveyard with batched=true, Any origin, SelfRef, exact event/source identity. Outer ordinary Any self-arrival gate passes; matching_batched_trigger_events inner ETB-only filter must retain the death event. Broad inner death gate removes it and yields zero versus one registration.',
'self-arrival-exception':'Actual ChangesZone Battlefield->Graveyard with Any origin passes shape/destination/filter checks; all three self-arrival predicates are true (same source ObjectId, SelfRef filter, trigger functions in destination). Any exempts this occurrence; Equals(Battlefield) sibling still uses before.',
'component-binding-distinct-invocation':'Natural WaitingFor::SacrificeForCost -> handle_sacrifice_for_cost selected valid sacrifice cost; a separate invocation begins after prior queue items and assigns component=u64(queue.len()) before appending. Same-valued cost/filter cannot merge invocations.',
'component-serde-drop':'Naturally paused pending_cast with nonempty deferred_sacrificed_permanents serializes each DeferredSacrificedPermanent.component; replay must preserve Some(component) rather than recreate missing None provenance.',
'inline-migration-preflight':'Public action boundary first authenticates actor, classifies action, then non-OutOfBandPreference and non-exempt inline PayCost/continuation action must validate pending components before dispatch. Only serialized provenance is removed in the hostile fixture.',
'concession-preflight-exception':'After public actor authorization, matches!(action, Concede{..}) bypasses only pending-component metadata validation. Actual concession remains subject to normal actor/seat gates and reaches elimination despite malformed saved payment provenance.',
'independent-debug-preflight-exceptions':'After actor authorization, Debug/GrantDebugPermission/RevokeDebugPermission match explicit metadata-preflight exclusions. Downstream debug permission and host authorization remain authoritative; permitted actions proceed, unauthorized twins remain rejected.',
}
for id,branch in branches.items():idx[id]['first_reaching_branch']=branch
# Attach exact reached assertion snippets from the actual imported logs, keeping panic limits visible.
for r in rows:
 failures=[]
 for ev in r['evidence']:
  x=ev['row']
  if 'verified' in x:
   wanted=x.get('declared_failed_tests',[])
   for fail in x['verified']['mutant'].get('semantic_failures',[]):
    if any(fail['test'].endswith(t) for t in wanted):failures.append({'test':fail['test'],'excerpt':fail['excerpt'][:950],'source':'original public mutant'})
  for ph in x.get('phases',[]) if isinstance(x.get('phases'),list) else []:
   if ph.get('phase')=='mutant':
    for cmd in ph.get('commands',ph.get('tests',[])):
     context=cmd.get('failure_context',cmd.get('failure_contexts'))
     if context:failures.append({'command':cmd.get('argv',cmd.get('command')),'excerpt':context,'source':'exact independently invoked mutant'})
  if isinstance(x.get('mutant'),list):
   directory=pathlib.Path(ev['artifact']['path']).parent
   if directory.name.endswith('attempt-1'):directory=directory/r['id']
   for i,cmd in enumerate(x['mutant']):
    if cmd['exit']:
     log=directory/'mutant'/(str(i)+'.log')
     if log.exists():
      text=log.read_text();at=text.find('panicked at');excerpt=text[max(0,text.rfind("thread '",0,at)):at+750] if at>=0 else text[-750:]
      failures.append({'test':cmd.get('case',{}).get('test'),'excerpt':excerpt,'log':str(log),'log_sha256':h(log),'source':'v10 independent invocation'})
 if r.get('independent_structural_map'):
  m=r['independent_structural_map'];r['semantic_assertion_summary']=m.get('v10_actual_assertion',m['assertion_mapping'])
 else:r['semantic_assertion_summary']='Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.'
 r['reached_assertions']=failures
 r['restore_evidence_note']='Each imported evidence row retains baseline and restored exact source/command/log/count associations. Original30 and fiveR2/R3 compiled restorations; later matcher/library/root supplemental comparisons explicitly used preserved canonical artifacts only after full identity checks. See per-phase execution method, never infer fresh compilation from a direct run.'
 if r['id']=='added-mid-leaf-flush':
  p=e.parent/'hushbringer-v9-mid-leaf-focused/receipt.json';r['focused_followup']=ref(p);r['limitation']='Full mutant matrix reached target Creature-record failure then later resolver reverse stack overflow; full matrix did not complete. Focused follow-up independently failed target and passed all4controls, with all5baseline/restored passes.'
assert len(rows)==67 and len(idx)==67
for r in rows:
 r['status']='measured; source-bound evidence attached' if r['evidence'] and 'pending' not in r else 'pending final root outcome'
 r['production_entry']=r.get('production_entry',r['file']+'::'+', '.join(dict.fromkeys(o.get('function','') for o in r.get('operations',[]))))
classes={'public':sum(r['evidence_classification'].startswith('public runtime') for r in rows),'private':sum(r['evidence_classification'].startswith('private') for r in rows),'defensive':sum(r['evidence_classification'].startswith('lower-level') for r in rows)}
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'executor handoff: all67 distinct mutations measured; native-arm/annotation review gaps remain, no implementation-complete claim','final_source_manifest_sha256':'885baf9780651ece1b38291acbcfa2ab2cb766defd3fe49671ace1ca40a73d0b','root_final_audit':ref(b/'hushbringer-v9-library-mutations/expanded-v10-root-attempt-1/root-archive-audit.json'),'distinct_mutations':len(rows),'classifications':classes,'imported_hash_audit':ref(e/'imported-evidence-audit.json'),'proof_source_manifest_sha256':'3016d5db7d54e3be126e7e83b74e4080d11b52a8bb3ba2bc0da09ef601e1d0f2','rows':rows}
dump(e/'production-path-maintainer-map-v10.json',result)
# Human matrix exposes physical seam and semantic discriminator; full JSON carries exact operations, per-phase receipts and contexts.
md=['# Physical production paths and maintainer simulation','', 'This map retains each comparison’s actual source and compilation method. It does not turn private contracts into public producer proofs. The linked JSON carries exact transformations, runtime counts, assertion excerpts, complete source/archive identities and restored commands for every row.','',f"Distinct seams: {len(rows)}; classifications: {classes}.",'']
for r in rows:
 md += ['## '+r['id'],'',r['evidence_classification']+'.','',f"Physical source: `{r['file']}`. Entry: {r['production_entry']}",'',f"First branch: {r['first_reaching_branch']}",'',f"Authority: {r['selected_authority']} Binding: {r['binding_time']}",'',f"Storage: {r['storage']} Consumer: {r['consumer']}",'',f"Invalidation: {r['invalidation']} Serialization: {r['serialized_impact']}",'',f"Hostile/sibling controls: {r['hostile_and_sibling_controls']}",'',f"Exact mutation: {r.get('description',r.get('claim','see exact operation in JSON'))}",'']
 md += ['Actual assertion: '+r['semantic_assertion_summary'], '', 'Tests: '+', '.join('`'+(t.get('test','') if isinstance(t,dict) else t)+'`' for t in r.get('tests',[])), '']
 for a in r['reached_assertions'][:4]:
  md += ['```text', (a['excerpt'] if isinstance(a['excerpt'],str) else json.dumps(a['excerpt'],indent=2))[:1200], '```', '']
 for ev in r['evidence']:
  md += ['- '+ev['kind']+': `'+ev['artifact']['path']+'` SHA `'+ev['artifact']['sha256']+'`.']
 if r.get('pending'):md+=['',r['pending']]
 md+=['']
(e/'production-path-maintainer-map-v10.md').write_text('\n'.join(md)+'\n')
print('rows',len(rows),'classes',classes,'pending',[r['id'] for r in rows if r.get('pending')]);print('JSON SHA',h(e/'production-path-maintainer-map-v10.json'))
