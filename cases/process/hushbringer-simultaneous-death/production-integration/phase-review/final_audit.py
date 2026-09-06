from pathlib import Path
import hashlib,json,re,subprocess,os,datetime
b=Path('/home/ubuntu/coworld-migration-20260904');o=b/'phase-main-integration-review';v=b/'phase-main-integration';r=Path('/home/ubuntu/repos/phase-hushbringer-publish')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=r)
checkpoint=o/'source-review-receipt.json';assert sha(checkpoint)=='f7cb10b90aaf8b3c09510e8689f28a8440f7512e8cf2c8616e9663a033317e26'
prior=json.loads(checkpoint.read_text())
for name,h in prior['artifacts'].items():assert sha(o/name)==h,name
source_review=json.loads((o/'source-review.json').read_text())
assert sha(v/'verify.py')==source_review['inputs'][str(v/'verify.py')]
receipt=json.loads((v/'verification-receipt.json').read_text());assert receipt['status']=='passed' and receipt['source_unchanged'] is True;assert (v/'verified').read_text()=='complete\n'
expected_commands=[['cargo','clippy','--workspace','--all-targets','--locked','--','-D','warnings'],['cargo','test','-p','engine','--locked'],['bash','scripts/gen-card-data.sh']]
assert len(receipt['commands'])==len(expected_commands)
for c,expected in zip(receipt['commands'],expected_commands):
 assert c['command']==expected and c['exit']==0,c
 assert sha(Path(c['log']))==c['log_sha256'],c['log']
assert receipt['source_manifest_sha256']==sha(v/'source.json')=='e028b74adbe94b2157054eee622a691ab90cdb8bc26cbd7361d5d33e17a87406'
manifest=json.loads((v/'source.json').read_text())
for path,h in manifest.items():assert sha(r/path)==h,path
assert git('rev-parse','HEAD').decode().strip()=='1cf344efe83c871a362bf04e8444e820124c21f8';assert git('rev-parse','MERGE_HEAD').decode().strip()=='fa0ebfe88db224ebd32624bb96ef033d338c2d8c'
index=git('ls-files','--stage');assert hashlib.sha256(index).hexdigest()==json.loads((o/'independent-preservation-audit.json').read_text())['index_entries_sha256']
assert not git('diff','--name-only') and not git('ls-files','-u')
root={}
for entry in git('ls-files','--stage','-z').split(b'\0')[:-1]:
 header,path=entry.split(b'\t',1);mode,oid,stage=header.split();assert stage==b'0';parts=path.split(b'/');d=root
 for part in parts[:-1]:d=d.setdefault(part,{})
 d[parts[-1]]=(mode,oid)
def tree(d):
 data=b''
 for name,value in sorted(d.items(),key=lambda kv:kv[0]+(b'/' if isinstance(kv[1],dict) else b'')):
  mode,oid=(b'40000',tree(value)) if isinstance(value,dict) else value
  data+=mode+b' '+name+b'\0'+bytes.fromhex(oid.decode())
 return hashlib.sha1(b'tree '+str(len(data)).encode()+b'\0'+data).hexdigest().encode()
tree_id=tree(root).decode();assert tree_id=='7cdb208cc3187341e478c577cdc775ed6a66a5dc'
for path in ['.agents/skills','.codex/skills']:assert (r/path).is_symlink() and str((r/path).readlink()).encode()==git('show',':'+path)
clippy=(v/'verification-0.log').read_text();assert 'Checking manabrew-compat' in clippy and 'Finished `dev` profile' in clippy
blocks=re.split(r'^\s*(?:Running|Doc-tests) ',(v/'verification-1.log').read_text(),flags=re.M)[1:];assert len(blocks)==5
expected_counts=[(16592,7),(6,0),(9,0),(3176,22),(0,7)];summaries=[];rows_by_block=[]
for block,(passed,ignored) in zip(blocks,expected_counts):
 rows=re.findall(r'^test (.+?) \.\.\. (ok|ignored)(?:,.*)?$',block,re.M);assert len(rows)==passed+ignored
 assert sum(s=='ok' for _,s in rows)==passed;assert sum(s=='ignored' for _,s in rows)==ignored
 assert f'test result: ok. {passed} passed; 0 failed; {ignored} ignored; 0 measured; 0 filtered out;' in block
 assert len({n for n,_ in rows})==len(rows)
 rows_by_block.append(dict(rows));summaries.append({'suite':block.splitlines()[0],'passed':passed,'ignored':ignored,'failed':0,'measured':0,'filtered_out':0,'individual_result_rows_reconciled':True})
old=b/'hushbringer-v10-execution/final-gates-2';oldreceipt=json.loads((old/'receipt.json').read_text());ignored_comparisons=[]
for oldindex,newindex in [(1,0),(2,3),(4,4)]:
 oldlog=old/f'{oldindex}.log';assert sha(oldlog)==oldreceipt['results'][oldindex]['log_sha256']
 names=set(re.findall(r'^test (.+?) \.\.\. ignored(?:,.*)?$',oldlog.read_text(),re.M));new={n for n,s in rows_by_block[newindex].items() if s=='ignored'};assert names==new
 ignored_comparisons.append({'suite':summaries[newindex]['suite'],'historical_log':str(oldlog),'historical_log_sha256':sha(oldlog),'names':sorted(new),'exact_same_ignored_names':True})
integration=rows_by_block[3];suppression={n:s for n,s in integration.items() if n.startswith('trigger_suppression_event_timing::')};assert list(suppression.values()).count('ok')==196;assert list(suppression.values()).count('ignored')==20
focused=['casting_affordability_action_consistency::targeted_auto_cast_enters_mana_payment_for_costed_tap_mana_ability','casting_affordability_action_consistency::targeted_cast_with_no_payable_mandatory_cost_branch_is_not_offered','kozilek_broken_reality_manifest_from_hands::kozilek_cast_trigger_manifests_two_from_each_targeted_players_hand','scroll_of_fate_manifest_from_hand::scroll_of_fate_activated_ability_manifests_a_chosen_noncreature_hand_card','power_up_keyword::marvel_boy_triggers_only_on_power_up_activation']
for name in focused:assert integration[name]=='ok'
generator=(v/'verification-2.log').read_text()
for needle in ['Generated 2870 token presets','Faces indexed: 35802','OK: 35802 cards parsed','Generated client/public/card-data.json']:assert needle in generator,needle
carddata=r/'client/public/card-data.json';assert len(json.loads(carddata.read_text()))==35802
restored=receipt['generated_tracked_files_restored'];assert {x['path'] for x in restored}=={'crates/engine/data/known-tokens.toml','crates/engine/data/oracle-subtypes.json'}
for item in restored:assert sha(r/item['path'])==item['before']==manifest[item['path']];assert item['generated']!=item['before']
identity=json.loads((o/'evidence-identity-audit.json').read_text())
for name,h in identity['files'].items():assert sha(Path(identity['base_directory'])/name)==h,name
env=dict(os.environ);env['PATH']='/home/ubuntu/.cargo/bin:'+env['PATH'];checks=[]
for name,command in [('final-format-check.log',['cargo','fmt','--all','--check']),('final-diff-check.log',['git','diff','--cached','--check'])]:
 with (o/name).open('x') as log:proc=subprocess.run(command,cwd=r,env=env,stdout=log,stderr=subprocess.STDOUT)
 assert proc.returncode==0,(name,proc.returncode);checks.append({'command':command,'exit':proc.returncode,'log':str(o/name),'log_sha256':sha(o/name)})
for path,h in manifest.items():assert sha(r/path)==h,path
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'/root/hushbringer_main_integration_review','findings':[],'source_tree':tree_id,'source_files_reverified':len(manifest),'source_manifest_sha256':sha(v/'source.json'),'source_unchanged':True,'index_unchanged_from_checkpoint':True,'checkpoint_receipt_sha256':sha(checkpoint),'checkpoint_artifacts_rehashed':len(prior['artifacts']),'verification_receipt_sha256':sha(v/'verification-receipt.json'),'verification_script_sha256':sha(v/'verify.py'),'verification_commands':receipt['commands'],'full_individual_test_rows_reconciled':summaries,'ignored_names_comparison':ignored_comparisons,'suppression_suite':{'passed':196,'ignored':20},'upstream_boundary_tests_passed':focused,'card_generation':{'indexed_records':35802,'token_presets_log':2870,'current_card_data_sha256':sha(carddata),'indexed_records_independently_counted':True,'generated_inputs_restored_and_rehashed':restored,'generated_intermediate_hashes':'Recorded by the root verifier; superseded generated input bytes are not independently rehashed here. Restored current bytes independently match the original source manifest.'},'independent_noncompiling_checks':checks,'original_fixed_experiment_binaries_and_plan_rehashed':True,'source_only_checkpoint_preserved':True,'extra_compilation':False}
(o/'final-gate-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['ignored_names_comparison','verification_commands','card_generation']},indent=2))
