from pathlib import Path
import json,re,hashlib,datetime,subprocess
out=Path('/home/ubuntu/coworld-migration-20260904/hushbringer-v10-review-fixes');root=Path('/home/ubuntu/repos/phase-verifiable-loop');parent=out.parent
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,obj):p.write_text(json.dumps(obj,indent=2)+'\n')
source=json.loads((out/'frozen-source/source.json').read_text());key=h(out/'frozen-source/source.json');assert all(h(root/f)==v for f,v in source.items())
interim=json.loads((out/'interim-review-input-manifest.json').read_text());assert all(h(out/f)==v for f,v in interim.items())
old=json.loads((parent/'hushbringer-implementation-v10-manifest.json').read_text());assert all(h(parent/f)==v for f,v in old.items())
gates=json.loads((out/'final-gates/receipt.json').read_text());assert 'finished_utc' in gates and len(gates['results'])==11
for i,r in enumerate(gates['results']):
 assert r['exit']==(101 if i in [8,9] else 0),(i,r)
 assert r['source_manifest_sha256']==key and r['changed']==[]
 assert h(Path(r['log']))==r['log_sha256']

def counts(index):
 text=(out/f'final-gates/{index}.log').read_text()
 return [dict(zip(['passed','failed','ignored','measured','filtered'],map(int,m))) for m in re.findall(r'test result: (?:ok|FAILED)\. (\d+) passed; (\d+) failed; (\d+) ignored; (\d+) measured; (\d+) filtered out',text)]
expected={1:(196,0,20),3:(16586,0,7),4:(3172,0,22),5:(15,0,0),6:(0,0,7),7:(5,0,0),8:(2,18,0)}
verification={}
for i,want in expected.items():
 result=counts(i);assert result,i
 got=tuple(sum(r[k] for r in result) for k in ['passed','failed','ignored']);assert got==want,(i,got,want)
 verification[str(i)]={'summaries':result,'totals':dict(zip(['passed','failed','ignored'],got))}
old_fail_log=(parent/'hushbringer-v10-execution/final-gates-2/6.log').read_text();new_fail_log=(out/'final-gates/8.log').read_text()
# Rust's final failures list has one indented fully-qualified name per failing test.
failed=lambda t:sorted(set(re.findall(r'^    (trigger_suppression_event_timing::\S+)\s*$',t,re.M)))
assert len(failed(new_fail_log))==18 and failed(new_fail_log)==failed(old_fail_log)
clippy=(out/'final-gates/9.log').read_text();assert re.findall(r'^error\[(.*?)\]',clippy,re.M)==['E0004'];assert 'SetFullControl' in clippy and 'manabrew-compat' in clippy
card=json.loads((out/'card-data-final/receipt.json').read_text());assert card['exit']==0 and card['post_restore_changed']==[]
assert sorted(card['changed_by_generator'])==['crates/engine/data/known-tokens.toml','crates/engine/data/oracle-subtypes.json']
assert json.loads((out/'card-data-final/restored-source.json').read_text())==source
canon=json.loads((out/'canonical-build.json').read_text());assert canon['exit']==0 and canon['source_manifest_sha256']==key
integration=[a for a in canon['artifacts'] if a['cargo_artifact']['target']['name']=='integration'];assert len(integration)==1;integration=integration[0];assert h(Path(integration['cargo_artifact']['executable']))==integration['sha256']
status=subprocess.check_output(['git','status','--short'],cwd=root,text=True);(out/'final-git-status.txt').write_text(status)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()=='2dec6c88915db4697706234a7ba2fcedd97b1689'
summary={'source_manifest_sha256':key,'source_files_verified':len(source),'interim_sealed_files_verified':len(interim),'prior_sealed_artifacts_verified':len(old),'gates':verification,'desired_failure_names':failed(new_fail_log),'desired_failure_set_matches_prior_candidate':True,'workspace_clippy':'Known fixed-base manabrew-compat SetFullControl E0004 only; out of scope','card_generation':card,'canonical_integration':integration}
dump(out/'verification-summary.json',summary)
a=json.loads((out/'handoff-draft.json').read_text());a['status']='Complete frozen-source evidence handoff; one source citation remains outstanding. No clean CR gate, implementation acceptance, clean workspace-Clippy or desired-rules-complete claim.';a['verification']['final']={'module':'196 passed,20 ignored','engine_library':'16586 passed,7 ignored','full_integration':'3172 passed,22 ignored','bins':'15 passed','docs':'0 executed,7 ignored','cross_source_batch_behavior':'5 passed; no throughput claim','desired_diagnostics':'2 passed,18 failed; exact prior candidate failure set retained','engine_clippy':'passed --all-targets -D warnings','workspace_clippy':'known baseline SetFullControl E0004 only','format':'fmt --all --check passed, no source changes','card_data':'generation passed; known-tokens and oracle-subtypes exact pre-generation bytes restored with fresh writes before canonical build','canonical_integration_sha256':integration['sha256'],'receipts':['canonical-build.json','final-gates/receipt.json','card-data-final/receipt.json','verification-summary.json']};a['production_coverage_map']=[x.replace('manual-constructor-boundary-audit.json','manual-constructor-boundary-audit-final.json').replace('production-entry-callsite-map.json','production-entry-callsite-map-reviewed.json').replace('typed-common-boundary-map.json','typed-common-boundary-map-reviewed.json') for x in a['production_coverage_map']];a['maintainer_matrix']=a['maintainer_matrix'].replace('production-path-maintainer-map-v10.json and .md','production-path-maintainer-map-v10-reviewed.json and production-path-maintainer-map-v10-reviewed.md');a['final_map_corrections']='final-map-corrections.json explicitly supersedes stale interim native sibling statuses, All83 constructor reference, and older current-review metadata. All interim manifest-bound bytes remain unchanged.';a['authoritative_maps']=json.loads((out/'reviewed-map-selection.json').read_text())['authoritative_maps'];a['outstanding_review_findings']=json.loads((out/'reviewed-map-selection.json').read_text())['outstanding_findings'];a['cr_gate_passed']=False;a['implementation_ready_for_acceptance']=False;a['stop_items']=a['outstanding_review_findings'];a['cr_gate']='cr-reviewed-audit.json/md is authoritative:185 added/moved/adjacent annotations reviewed, original five groups fixed, but CR115.1 at engine_resolution_choices.rs:3528 remains incorrect. Prior cr-complete-audit row184 semantic acceptance is superseded. Frozen source was preserved at root instruction for a fresh fix executor after complete review.';a['canonical_immutable_copy']='canonical-integration';a['canonical_immutable_receipt']='canonical-integration-receipt.json';a['source_ownership']='Released to root after this sealed handoff. No source writes or builds remain; root owns Git after fresh full independent review. No commit or push performed.';a['finalized_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();dump(out/'handoff.json',a)
md='''The native public controls and five original CR groups are fixed, but the fresh review found one remaining source citation at engine_resolution_choices.rs:3528. This handoff preserves the frozen source and measured evidence for the next fresh fix cycle; it is not a clean implementation verdict. Production behavior is unchanged: this revision corrects comments in three source files and appends nine public integration tests (60 parameter cases). The prior 7,329 test lines remain byte-identical. No commit or push was made.

Source manifest: `'''+key+'''`. The full source/archive/diff and historical mutation lineage are bound in `frozen-source/receipt.json` and `frozen-source/lineage.json`. The 67 historical mutations retain their actual source/build identities; native private-zone tests make no wrapper-mutation kill claim.

The new natural choices cover Hand, direct Library, and the tracked Library pool produced by an actual Dig selection; Top, Bottom, and NthFromTop (1,3,99); both orders and Hush/no-Hush. They check exact library/event order, selected and nonselected records, absent suppression snapshots, full-state preservation on invalid choices, valid retry, observer/continuation payoff and settled priority. Library reposition notifications remain explicitly labeled compatibility behavior.

The authoritative cr-reviewed-audit.json checks185 added, moved and adjacent annotations, including verbatim moves, and explicitly retains the CR115.1 finding. CR608.2d governs this resolution-time choice; the source is unchanged. Prior cr-complete-audit row184 incorrectly accepted the citation and is superseded. The source-zone citation is removed; regeneration, Role, Battle protector and Siege/non-Siege zero-defense citations are corrected. The inherited broader non-Siege stack guard remains an explicit compatibility limit. All 51 call sites are mapped, and the complete constructor audit distinguishes 3 production and 79 test expressions (including Self) from signatures, documentation and raw golden strings.

Verification completed on EC2 using only the active checkout target. Focused controls: 9 pass. Full module: 196 pass,20 ignored. Engine library: 16,586 pass,7 ignored. Full integration: 3,172 pass,22 ignored. Binaries: 15 pass. Docs: 0 executed,7 ignored. Cross-source batching controls: 5 pass. Engine all-target Clippy and fmt check pass. Card generation passes, and both known generated source files were restored byte-for-byte with fresh writes before the final canonical build.

The 20 desired diagnostics remain unpromoted: 2 pass and the same 18 fail as the prior candidate. Workspace Clippy retains only the known fixed-base manabrew-compat SetFullControl E0004. No parser/card support or throughput claim was added. All prior rule limits and fixture distinctions are enumerated in `handoff.json` and remain in force.

No production expansion or re-plan is required. The remaining citation is handed back for a fresh executor after complete independent review; root instructed this executor to preserve the source and finish its evidence. `handoff.json` contains the complete structured executor return; `verification-summary.json` and the command receipts preserve exact results and binary identity. Source ownership is released to root for the fresh full independent review and subsequent Git work.
'''
(out/'handoff.md').write_text(md)
# Check the entire authoritative final map set before sealing.
selected=a['authoritative_maps'];assert all((out/f).exists() for f in selected.values())
entry=json.loads((out/selected['callsite_map']).read_text());native=json.loads((out/selected['native_library_map']).read_text());constructors=json.loads((out/selected['constructor_audit']).read_text());common=json.loads((out/selected['common_boundary_map']).read_text());matrix=json.loads((out/selected['maintainer_matrix']).read_text())
assert len(entry['call_sites'])==51 and entry['unmapped']==[] and len(entry['native_unaffected_siblings'])==3
assert len(matrix['rows'])==67 and len(matrix['unresolved_review_items'])==1 and matrix['unresolved_review_items'][0]['id']=='remaining-native-choice-cr-citation'
assert constructors['counts']['constructors']==82 and constructors['counts']['scopes']=={'test':79,'production':3}
assert constructors['counts']['named_constructor_expressions']==81 and constructors['counts']['self_constructor_expressions']==1
assert sum(r.get('occurrences',1) for r in constructors['non_constructor_hits'])==11
byid={r['id']:r for r in native['rows']}
for r in entry['native_unaffected_siblings']:
 assert r['tests']==byid[r['id']]['tests'] and r['first_branch']==byid[r['id']]['first_reaching_branch'] and r['test'] and r['status'].startswith('Required public')
for obj in [entry,common,matrix]:assert obj['authoritative_maps']==selected
assert 'All83' not in next(r for r in common['rows'] if r['id']=='manual-event-constructors')['production_entry']
ids={r['id'] for r in matrix['rows']}
assert all(set(r.get('physical_mutation_ids',[]))<=ids for r in entry['call_sites'])
assert (out/'focused-1/0.log').read_text().count('NATIVE_LIBRARY_CHOICE_EVIDENCE ')==60
consistent={'source_manifest_sha256':key,'authoritative_maps':{k:{'path':str(out/f),'sha256':h(out/f)} for k,f in selected.items()},'call_sites':51,'historical_mutations':67,'native_arms':3,'native_parameter_cases':60,'constructors':82,'production_constructors':3,'test_constructors':79,'named_constructor_expressions':81,'self_constructor_expressions':1,'raw_nonconstructor_occurrences':11,'outstanding_source_citation_findings':1,'stale_interim_fields_superseded':True,'interim_manifest_unchanged':True,'all_final_references_exist_and_consistent':True}
dump(out/'final-map-consistency-audit.json',consistent)
# Bind every local artifact. Receipts and source archives are exact bytes; old artifacts remain external immutable references.
manifest={str(p.relative_to(out)):h(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name not in ['manifest.json','receipt.json']}
# Include nested command/frozen/generation receipts, excluding only this outer receipt.
for p in sorted(out.rglob('receipt.json')):
 if p.parent!=out:manifest[str(p.relative_to(out))]=h(p)
dump(out/'manifest.json',dict(sorted(manifest.items())))
receipt={'utc':a['finalized_utc'],'status':'sealed executor evidence handoff; one source citation remains outstanding','outstanding_source_citation_findings':1,'source_manifest_sha256':key,'source_archive_sha256':json.loads((out/'frozen-source/receipt.json').read_text())['source_archive_sha256'],'handoff_json_sha256':h(out/'handoff.json'),'handoff_md_sha256':h(out/'handoff.md'),'manifest_sha256':h(out/'manifest.json'),'artifact_count':len(manifest),'canonical_integration_sha256':integration['sha256'],'verification_summary_sha256':h(out/'verification-summary.json'),'source_ownership':'released to root','commits_or_pushes':False};dump(out/'receipt.json',receipt)
for p in out.rglob('*'):
 if p.is_file():p.chmod(0o555 if p.name=='canonical-integration' else 0o444)
print(json.dumps(receipt,indent=2))
