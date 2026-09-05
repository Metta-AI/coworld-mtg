from pathlib import Path
import json,tarfile,hashlib,importlib.util,subprocess,difflib,datetime,sys
D=Path('/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution')
C=Path('/home/ubuntu/repos/phase-hushbringer-mutations')
spec=importlib.util.spec_from_file_location('mutation_tools',D/'mutation-tools.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
manifest=json.loads((D/'frozen-candidate-v9/source.json').read_text())
with tarfile.open(D/'frozen-candidate-v9/source.tar.gz') as tar:
    canonical={f:tar.extractfile(f).read() for f in manifest}
def verify():
    assert all(m.hash_file(C/f)==h for f,h in manifest.items())
def command(kind):
    if kind=='public' or kind=='sba-library':
        return ['cargo','test','-p','engine','--message-format=json','--test','integration','trigger_suppression_event_timing','--','--nocapture']
    filt={'component-library':'deferred_component_','scope-library':'departure_scope_','schema-library':'zone_change_suppression_preserves_missing_empty_and_captured_history'}[kind]
    return ['cargo','test','-p','engine','--message-format=json','--lib',filt,'--','--nocapture']
out=D/'mutations-1';out.mkdir(exist_ok=True)
verify()
warm=out/'warm-candidate-public'
if not (warm/'receipt.json').exists():
    r=m.run_command(C,warm,command('public'),manifest)
    assert r['exit']==0 and not r['changed_during_run'],r
rows=json.loads((D/'mutation-inventory-v9.json').read_text())['rows']
if len(sys.argv)>1:
    ids=set(sys.argv[1:]);rows=[r for r in rows if r['id'] in ids]
else:
    rows=[r for r in rows if r['kind']=='public']
for row in rows:
    job=out/row['id']
    if job.exists():continue
    verify()
    job.mkdir()
    (job/'definition.json').write_text(json.dumps(row,indent=2)+'\n')
    path=C/row['file'];old=canonical[row['file']].decode()
    new=m.transform(old,row['operations'])
    assert old!=new
    patch=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+row['file'],tofile='b/'+row['file']))
    (job/'mutation.patch').write_text(patch)
    path.write_text(new)
    r=m.run_command(C,job/'mutant',command(row['kind']),manifest)
    log=(job/'mutant/command.log').read_text(errors='replace')
    failures=[line for line in log.splitlines() if " panicked at " in line]
    summary=[line for line in log.splitlines() if line.startswith('test result:')]
    compiled=any(a['executable'] and a['fresh']==False for a in r['artifacts'])
    outcome='runtime failure' if r['exit']==101 and failures and compiled else 'survived' if r['exit']==0 else 'invalid attempt'
    path.write_bytes(canonical[row['file']]) # Fresh mtime prevents reuse of mutant binary.
    verify()
    restored=m.run_command(C,job/'restored',command(row['kind']),manifest)
    result=dict(id=row['id'],outcome=outcome,mutant_exit=r['exit'],restore_exit=restored['exit'],compiled=compiled,failures=failures,summary=summary,finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (job/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    assert restored['exit']==0 and not restored['changed_during_run'],restored
print('all requested rows completed',flush=True)
