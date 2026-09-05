import support as r
import json,pathlib,os,re,subprocess,tarfile,hashlib,difflib,time,traceback,shutil
r.OUT=pathlib.Path(__file__).resolve().parent
RUNTIME=json.loads((r.OUT/'runtime-context.json').read_text())
DIRECT_CWD=pathlib.Path(RUNTIME['actual_cwd'])
DIRECT_ENV=r.ENV.copy()
for key in list(DIRECT_ENV):
    if key in RUNTIME['allowlist'] or key.startswith(('CARGO_PKG_','CARGO_BIN_EXE_')):DIRECT_ENV.pop(key)
DIRECT_ENV.update(RUNTIME['allowlisted_environment'])
CONFIG=json.loads((r.OUT/'case-map.json').read_text())
ROWS=CONFIG['rows']
MATRIX=CONFIG['matrix_filter']
TOTAL=CONFIG['matrix_passed']
IGNORED=CONFIG['matrix_ignored']
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
        counts(matrix,TOTAL,IGNORED);exe,binding=preserve(directory,matrix)
    else:
        exe,binding=canonical
        matrix=direct(directory,'matrix',exe,[MATRIX,'--nocapture','--test-threads=1'],expected,binding);counts(matrix,TOTAL,IGNORED)
    results=[matrix]
    for i,name in enumerate(row['tests']):
        record=direct(directory,str(i),exe,[name,'--exact','--nocapture','--test-threads=1'],expected,binding);counts(record,1,0);results.append(record)
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
