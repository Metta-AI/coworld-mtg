from pathlib import Path
import json,hashlib,importlib.util,datetime,traceback
a=Path('/home/ubuntu/coworld-migration-20260904')
d=a/'hushbringer-v9-execution'
c=Path('/home/ubuntu/repos/phase-hushbringer-mutations')
o=a/'hushbringer-v9-mid-leaf-focused'
o.mkdir(exist_ok=False)
spec=importlib.util.spec_from_file_location('m',d/'mutation-tools.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
manifest=json.loads((d/'frozen-candidate-v9/source.json').read_text())
assert all(m.hash_file(c/f)==h for f,h in manifest.items())
row=next(r for r in json.loads((d/'mutation-inventory-v9.json').read_text())['rows'] if r['id']=='added-mid-leaf-flush')
path=c/row['file'];original=path.read_bytes()
names=['first_departing_granter_preserves_later_member_types_and_trigger','two_target_destroy_owns_one_event_in_both_target_orders','oracle_wrath_hush_first_suppresses_simultaneous_traveler_death','oracle_wrath_traveler_first_suppresses_simultaneous_traveler_death','oracle_wrath_without_hush_creates_exactly_one_spirit']
report={'utc_started':datetime.datetime.now(datetime.timezone.utc).isoformat(),'row':row,'tests':names,'source_manifest_sha256':m.hash_file(d/'frozen-candidate-v9/source.json'),'qualification':'Original full mutant matrix observed intended Creature-record assertion then collateral R2 stack-overflow abort. These separate target/control invocations measure their complete results. Original full restored 91/20 passed.','phases':{}}
def run_phase(phase):
    receipts=[]
    for i,name in enumerate(names):
        command=['cargo','test','-p','engine','--message-format=json','--test','integration','trigger_suppression_event_timing::'+name,'--','--exact','--nocapture']
        out=o/(phase+'-'+str(i))
        r=m.run_command(c,out,command,manifest)
        log=(out/'command.log').read_text(errors='replace')
        receipts.append({'test':name,'receipt':str(out/'receipt.json'),'receipt_sha256':m.hash_file(out/'receipt.json'),'exit':r['exit'],'summary':[s for s in log.splitlines() if s.startswith('test result:')],'log_sha256':r['log_sha256']})
        print(phase,name,r['exit'],flush=True)
    report['phases'][phase]=receipts
    (o/'progress.json').write_text(json.dumps(report,indent=2)+'\n')
try:
    run_phase('baseline')
    path.write_text(m.transform(original.decode(),row['operations']))
    run_phase('mutant')
finally:
    path.write_bytes(original)
    assert all(m.hash_file(c/f)==h for f,h in manifest.items())
    run_phase('restored')
for phase,receipts in report['phases'].items():
    for i,r in enumerate(receipts):
        expected=101 if phase=='mutant' and i==0 else 0
        assert r['exit']==expected,(phase,i,r)
        needle='0 passed; 1 failed; 0 ignored;' if expected else '1 passed; 0 failed; 0 ignored;'
        assert any(needle in s for s in r['summary']),(phase,i,r)
        raw=json.loads(Path(r['receipt']).read_text())
        assert raw['changed_during_run']==[]
        if i==0 and phase in ['mutant','restored']:
            assert any(x['target']['name']=='integration' and x['fresh'] is False for x in raw['artifacts'])
report['utc_finished']=datetime.datetime.now(datetime.timezone.utc).isoformat()
report['source_restored']=all(m.hash_file(c/f)==h for f,h in manifest.items())
report['status']='Target semantic failure with four completed positive controls, all five baseline/restored pass; fresh mutant and restored integration compilation.'
(o/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
print('COMPLETE',m.hash_file(o/'receipt.json'),flush=True)
