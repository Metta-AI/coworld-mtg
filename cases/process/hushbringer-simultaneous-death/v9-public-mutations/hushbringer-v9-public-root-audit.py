from pathlib import Path
import json, hashlib, tarfile, importlib.util, datetime, re
a=Path('/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution')
out=a/'mutations-1'
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
canonical=json.loads((a/'frozen-candidate-v9/source.json').read_text())
spec=importlib.util.spec_from_file_location('mutation_tools',a/'mutation-tools.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tarfile.open(a/'frozen-candidate-v9/source.tar.gz') as t:
    source={f:t.extractfile(f).read() for f in canonical}
rows=[r for r in json.loads((a/'mutation-inventory-v9.json').read_text())['rows'] if r['kind']=='public']
results=[]; pending=[]; released=[]
for row in rows:
    job=out/row['id']
    if (job/'released.json').exists(): released.append(row['id']);continue
    if not (job/'result.json').exists(): pending.append(row['id']);continue
    result=json.loads((job/'result.json').read_text())
    expected=canonical.copy()
    expected[row['file']]=hashlib.sha256(m.transform(source[row['file']].decode(),row['operations']).encode()).hexdigest()
    observed={}
    for phase,wanted,status in [('mutant',expected,101),('restored',canonical,0)]:
        d=job/phase;r=json.loads((d/'receipt.json').read_text())
        assert r['exit']==status and not r['changed_during_run'],(row['id'],phase)
        assert r['source_manifest_sha256']==sha(d/'source.json')
        assert r['source_archive_sha256']==sha(d/'source.tar.gz')
        assert r['log_sha256']==sha(d/'command.log')
        assert json.loads((d/'source.json').read_text())==wanted,(row['id'],phase,'source')
        with tarfile.open(d/'source.tar.gz') as t:
            assert set(t.getnames())==set(wanted)
            for f,h in wanted.items(): assert hashlib.sha256(t.extractfile(f).read()).hexdigest()==h,(row['id'],phase,f)
        artifacts=[x for x in r['artifacts'] if x['target']['name']=='integration' and x['target']['kind']==['test']]
        assert len(artifacts)==1 and artifacts[0]['fresh'] is False and artifacts[0]['executable_sha256']
        log=(d/'command.log').read_text(errors='replace')
        summaries=[x for x in log.splitlines() if x.startswith('test result:')]
        if phase=='restored': assert any('91 passed; 0 failed; 20 ignored;' in x for x in summaries)
        panics=re.findall(r"thread '([^']+)'[^\n]*panicked at ([^\n]+)",log)
        semantic=[]
        for name,location in panics:
            lines=log.splitlines()
            start=next(i for i,s in enumerate(lines) if "thread '"+name+"'" in s and 'panicked at ' in s)
            semantic.append({'test':name,'location':location,'excerpt':'\n'.join(lines[start:start+6])})
        observed[phase]={'receipt_sha256':sha(d/'receipt.json'),'source_manifest_sha256':r['source_manifest_sha256'],'source_archive_sha256':r['source_archive_sha256'],'log_sha256':r['log_sha256'],'integration_executable_sha256':artifacts[0]['executable_sha256'],'fresh_compile':True,'exit':r['exit'],'summaries':summaries,'semantic_failures':semantic}
    declared=[n for n in row['tests'] if any(n in x['test'] for x in observed['mutant']['semantic_failures'])]
    assert declared,(row['id'],'no designated test failed')
    results.append({'id':row['id'],'file':row['file'],'declared_tests':row['tests'],'declared_failed_tests':declared,'mutation_patch_sha256':sha(job/'mutation.patch'),'result_sha256':sha(job/'result.json'),'verified':observed})
audit={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_manifest_sha256':sha(a/'frozen-candidate-v9/source.json'),'completed_count':len(results),'pending':pending,'released_not_counted':released,'scope':'Root mechanical source/archive/receipt/compiler/test-name verification. Semantic excerpts retained for independent implementation review; not implementation approval or acceptance. All mutations and restorations freshly compiled in this original supervisor.','rows':results}
dest=Path('/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit.json')
dest.write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps({'completed':len(results),'pending':pending,'released_count':len(released),'audit_sha256':sha(dest)}))
