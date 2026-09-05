import support as r
import json,pathlib,os,re,subprocess,tarfile,hashlib,difflib,time,traceback,shutil
r.OUT=pathlib.Path(__file__).resolve().parent
RUNTIME=json.loads((r.OUT/'runtime-context.json').read_text())
DIRECT_CWD=pathlib.Path(RUNTIME['actual_cwd'])
DIRECT_ENV=r.ENV.copy()
for key in list(DIRECT_ENV):
    if key in RUNTIME['allowlist'] or key.startswith(('CARGO_PKG_','CARGO_BIN_EXE_')):DIRECT_ENV.pop(key)
DIRECT_ENV.update(RUNTIME['allowlisted_environment'])
ROWS=json.loads((r.OUT/'spec.json').read_text())['rows']
HELD={'batched-adapter','batched-global-death-gate'}
MATRIX='trigger_suppression_event_timing'
with tarfile.open(r.FROZEN/'source.tar.gz','r:gz') as tar:
    ORIGINAL={name:tar.extractfile(name).read() for name in r.MANIFEST}

def counts(record,total,ignored):
    assert len(record['test_results'])==1,record
    m=re.search(r'(\d+) passed; (\d+) failed; (\d+) ignored;',record['test_results'][0]);assert m,record
    p,f,i=map(int,m.groups());assert p+f==total and i==ignored,(p,f,i,total,ignored)
    assert record['exit']==(101 if f else 0),record
    return {'passed':p,'failed':f,'ignored':i}

def direct(directory,label,exe,arguments,expected,binding):
    r.verify(expected); assert r.sha(exe)==binding['sha256']
    assert all(r.sha(p)==v['sha256'] for p,v in RUNTIME['dynamic_libraries'].items())
    start=r.utc();args=[str(exe)]+arguments;log=directory/(label+'.log')
    meta={'utc_start':start,'cwd':str(DIRECT_CWD),'target':str(r.ROOT/'target'),'argv':args,'env':RUNTIME['allowlisted_environment'],'runtime_context_sha256':r.sha(r.OUT/'runtime-context.json'),'source_manifest_sha256':r.sha(directory/'source.json'),'binary_binding':binding,'compilation':'none; direct execution of preserved binary, provenance recorded in binary_binding'}
    r.save(directory/(label+'.command.json'),meta);print(start,directory.name,label,'RUN',args,flush=True)
    with log.open('wb') as stream:rc=subprocess.call(args,cwd=DIRECT_CWD,env=DIRECT_ENV,stdout=stream,stderr=subprocess.STDOUT)
    (directory/(label+'.exit')).write_text(str(rc)+'\n');r.verify(expected);assert r.sha(exe)==binding['sha256']
    txt=log.read_text(errors='replace');results=re.findall(r'test result: ([^\n]+)',txt)
    assert 'skipping:' not in txt and results
    meta.update(utc_end=r.utc(),exit=rc,log=str(log),log_sha256=r.sha(log),test_results=results,source_verified_after=True)
    r.save(directory/(label+'.receipt.json'),meta);print(r.utc(),directory.name,label,'EXIT',rc,'RESULT',results,flush=True);return meta

def require_fresh(record):
    rebuilt=[]
    for item in record['compiler_artifacts']:
        a=item['artifact']
        if a['target']['name']=='engine' and not a['fresh']:
            assert any(f['newer_than_command_start'] for f in item['hashed_files']);rebuilt.append(item)
    assert rebuilt,'no freshly compiled engine artifact'
    return rebuilt

def preserve(directory,record):
    artifacts=[a for a in record['compiler_artifacts'] if a['artifact']['target']['name']=='integration' and a['artifact'].get('executable')]
    assert len(artifacts)==1;artifact=artifacts[0];a=artifact['artifact'];assert a['fresh'] is False
    old=pathlib.Path(a['executable']);exe=directory/'integration-executable';shutil.copyfile(old,exe);exe.chmod(0o755)
    binding={'path':str(exe),'sha256':r.sha(exe),'source_manifest_sha256':r.sha(directory/'source.json'),'source_archive_sha256':r.sha(directory/'source.tar.gz'),'cargo_command_receipt':str(directory/'matrix.receipt.json'),'cargo_command_receipt_sha256':r.sha(directory/'matrix.receipt.json'),'compiler_artifact':artifact,'fresh_engine_artifacts':require_fresh(record),'runtime_manifest_sha256':r.sha(r.OUT/'runtime-inputs.json')}
    assert r.sha(old)==binding['sha256'];r.save(directory/'binary.json',binding);return exe,binding

def phase(row,phase,expected,canonical=None):
    directory=r.OUT/(row['id']+'-runtime-'+phase);directory.mkdir();snap=r.snapshot(directory,expected)
    fmt=r.command(directory,'fmt',['cargo','fmt','--all','--check'],expected);assert fmt['exit']==0
    if phase in ['baseline','mutant']:
        matrix=r.command(directory,'matrix',['cargo','test','-p','engine','--message-format=json','--test','integration',MATRIX,'--','--nocapture','--test-threads=1'],expected)
        counts(matrix,91,20);exe,binding=preserve(directory,matrix)
    else:
        exe,binding=canonical
        matrix=direct(directory,'matrix',exe,[MATRIX,'--nocapture','--test-threads=1'],expected,binding);counts(matrix,91,20)
    results=[matrix]
    for i,name in enumerate(row['tests']):
        record=direct(directory,str(i),exe,['trigger_suppression_event_timing::'+name,'--exact','--nocapture','--test-threads=1'],expected,binding);counts(record,1,0);results.append(record)
    r.save(directory/'receipt.json',{'id':row['id'],'phase':phase,'snapshot':snap,'fmt':fmt,'results':results,'execution_method':'fresh Cargo compile plus preserved-mutant executable' if phase in ['baseline','mutant'] else 'reused preserved canonical executable after full source/runtime verification','binary_binding':binding})
    return results,(exe,binding)

def transform(text,operations):
    for op in operations:
        assert op['kind']=='replace'
        match=re.search(r'(?m)^(?:pub(?:\([^)]*\))? )?fn '+re.escape(op['function'])+r'\(',text);assert match,op
        start=match.start();end=text.index('\n}',start)+2;block=text[start:end]
        assert block.count(op['old'])==1,(op['function'],block.count(op['old']))
        text=text[:start]+block.replace(op['old'],op['new'],1)+text[end:]
    return text

def main():
    r.verify(r.MANIFEST)
    assert r.sha(r.OUT/'spec.json')=='dee6a9f52c59bf2dd621861ec8e6f7afbedf1465b1eb687776b1683210f52ec4'
    # Canonical source and freshly compiled binary were bound by the runtime probe.
    r.verify(r.MANIFEST)
    selected=[row for row in ROWS if row['id'] not in HELD]
    baseline={'id':'canonical','tests':sorted({name for row in ROWS for name in row['tests']})}
    binding=json.loads((r.OUT/'runtime-probe/binary.json').read_text())
    canonical=(pathlib.Path(binding['path']),binding)
    assert r.sha(canonical[0])==binding['sha256']
    results,canonical=phase(baseline,'confirmed',r.MANIFEST,canonical);assert all(x['exit']==0 for x in results)
    completed=[]
    for row in selected:
        r.verify(r.MANIFEST);before,_=phase(row,'before',r.MANIFEST,canonical);assert all(x['exit']==0 for x in before)
        job=r.OUT/row['id'];job.mkdir();path=r.ROOT/row['file'];original=ORIGINAL[row['file']]
        error=None
        try:
            path.write_text(transform(original.decode(),row['operations']))
            fmt_args=['cargo','fmt','--all'];r.save(job/'format-preparation.command.json',{'argv':fmt_args,'cwd':str(r.ROOT),'utc':r.utc()})
            with (job/'format-preparation.log').open('wb') as log:rc=subprocess.call(fmt_args,cwd=r.ROOT,env=r.ENV,stdout=log,stderr=subprocess.STDOUT)
            (job/'format-preparation.exit').write_text(str(rc)+'\n');assert rc==0
            expected=r.source();changed=[p for p in r.MANIFEST if expected[p]!=r.MANIFEST[p]];assert changed==[row['file']],changed
            patch=''.join(difflib.unified_diff(original.decode().splitlines(True),path.read_text().splitlines(True),fromfile='a/'+row['file'],tofile='b/'+row['file']));(job/'mutation.patch').write_text(patch)
            r.save(job/'mutation.json',{'row':row,'original_sha256':r.MANIFEST[row['file']],'mutant_sha256':r.sha(path),'patch_sha256':r.sha(job/'mutation.patch'),'driver_sha256':r.sha(__file__),'support_sha256':r.sha(r.OUT/'support.py'),'source_mtime_ns':path.stat().st_mtime_ns})
            mutant,_=phase(row,'mutant',expected)
            named_failures=[]
            for rec in mutant[1:]:
                if rec['exit']==101:
                    txt=pathlib.Path(rec['log']).read_text();assert 'panicked at ' in txt and 'assertion' in txt,'not assertion discrimination'
                    named_failures.append(rec['argv'][1])
            outcome='intended assertion failure' if named_failures else 'survived named tests; unresolved'
            summary={'id':row['id'],'outcome':outcome,'matrix_counts':counts(mutant[0],91,20),'named_exits':[x['exit'] for x in mutant[1:]],'named_failing_assertions':named_failures}
        except BaseException:
            error=traceback.format_exc();(job/'attempt-error.txt').write_text(error)
        finally:
            mutated_mtime=path.stat().st_mtime_ns;restore_start=time.time_ns();path.write_bytes(original);assert path.stat().st_mtime_ns>=restore_start and path.stat().st_mtime_ns>mutated_mtime;r.verify(r.MANIFEST)
            r.save(job/'restoration.json',{'utc':r.utc(),'file':row['file'],'original_sha256':r.MANIFEST[row['file']],'restored_sha256':r.sha(path),'mutated_mtime_ns':mutated_mtime,'restored_mtime_ns':path.stat().st_mtime_ns,'all2051_verified':True,'fresh_mtime':True,'method':'candidate bytes restored; same filters rerun on preserved canonical binary; no restoration compilation claimed'})
            restored,_=phase(row,'restored',r.MANIFEST,canonical);assert all(x['exit']==0 for x in restored)
        if error:raise RuntimeError(error)
        summary.update(utc=r.utc(),restored=True);r.save(job/'result.json',summary);completed.append(summary);r.save(r.OUT/'progress.json',completed);print('ROW COMPLETE',json.dumps(summary),flush=True)
    r.verify(r.MANIFEST);r.save(r.OUT/'nine-complete.json',{'utc':r.utc(),'rows':completed,'held':sorted(HELD),'all_source_restored':True})
if __name__=='__main__':
    try:main()
    except BaseException:
        traceback.print_exc();(r.OUT/'supervisor.exit').write_text('1\n');raise
    else:(r.OUT/'supervisor.exit').write_text('0\n')
