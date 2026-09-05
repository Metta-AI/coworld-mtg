import datetime, difflib, hashlib, json, os, pathlib, re, subprocess, sys, tarfile, time, traceback
ROOT=pathlib.Path('/home/ubuntu/repos/phase-hushbringer-mutations-r2-r3')
OUT=pathlib.Path(__file__).resolve().parent
FROZEN=OUT/'frozen'
MANIFEST=json.loads((FROZEN/'source.json').read_text())
ENV=os.environ.copy(); ENV.update(CARGO_TARGET_DIR=str(ROOT/'target'),CARGO_BUILD_JOBS='2',RTK_DISABLED='1',RUST_TEST_THREADS='1')
for k in ['RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','CARGO_BUILD_RUSTFLAGS','CARGO_PROFILE_DEV_DEBUG','CARGO_PROFILE_TEST_DEBUG','FORGE_TEST_FULL_DB']:
    ENV.pop(k,None)
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def source():return {p:sha(ROOT/p) for p in MANIFEST}
def verify(expected):
    actual=source();assert actual==expected,{p:(expected[p],actual[p]) for p in expected if expected[p]!=actual[p]}
    for p,v in json.loads((OUT/'runtime-inputs.json').read_text()).items():assert sha(ROOT/p)==v['sha256'],p

def snapshot(directory,expected):
    verify(expected);save(directory/'source.json',expected)
    save(directory/'source-mtimes.json',{p:(ROOT/p).stat().st_mtime_ns for p in expected})
    with tarfile.open(directory/'source.tar.gz','w:gz') as archive:
        for p in sorted(expected):archive.add(ROOT/p,arcname=p,recursive=False)
    return {'files':len(expected),'manifest_sha256':sha(directory/'source.json'),'archive_sha256':sha(directory/'source.tar.gz')}

def command(directory,label,args,expected):
    verify(expected)
    started=utc(); start_ns=time.time_ns(); log=directory/(label+'.log')
    meta={'utc_start':started,'cwd':str(ROOT),'target':ENV['CARGO_TARGET_DIR'],'argv':args,'env':{k:ENV.get(k) for k in ['CARGO_TARGET_DIR','CARGO_BUILD_JOBS','CARGO_PROFILE_DEV_DEBUG','CARGO_PROFILE_TEST_DEBUG','RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','CARGO_BUILD_RUSTFLAGS','RUSTC_WRAPPER','RUSTC_WORKSPACE_WRAPPER','RUST_TEST_THREADS','RUST_MIN_STACK','RTK_DISABLED','FORGE_TEST_FULL_DB','PHASE_TRIGGER_INDEX_AUDIT','PHASE_REPLACEMENT_INDEX_AUDIT','GATED_SETS','GATED_SETS_AS_OF']},'source_manifest_sha256':sha(directory/'source.json')}
    save(directory/(label+'.command.json'),meta)
    print(started,directory.name,label,'RUN',args,flush=True)
    with log.open('wb') as output:
        rc=subprocess.call(args,cwd=ROOT,env=ENV,stdout=output,stderr=subprocess.STDOUT)
    (directory/(label+'.exit')).write_text(str(rc)+'\n')
    verify(expected)
    artifacts=[]
    for line in log.read_text(errors='replace').splitlines():
        if not line.startswith('{'):continue
        try:j=json.loads(line)
        except json.JSONDecodeError:continue
        if j.get('reason')=='compiler-artifact' and j.get('target',{}).get('name') in ['engine','integration']:
            item={'artifact':j,'hashed_files':[]}
            for p in list(j.get('filenames',[]))+([j['executable']] if j.get('executable') else []):
                file=pathlib.Path(p)
                if file.is_file():item['hashed_files'].append({'path':p,'sha256':sha(file),'mtime_ns':file.stat().st_mtime_ns,'newer_than_command_start':file.stat().st_mtime_ns>=start_ns})
            artifacts.append(item)
    text=log.read_text(errors='replace')
    results=re.findall(r'test result: ([^\n]+)',text)
    meta.update(utc_end=utc(),exit=rc,log=str(log),log_sha256=sha(log),test_results=results,compiler_artifacts=artifacts,source_verified_after=True)
    save(directory/(label+'.receipt.json'),meta)
    print(utc(),directory.name,label,'EXIT',rc,'RESULT',results,flush=True)
    if args[1]=='test':
        assert results and not any('0 passed; 0 failed' in x for x in results),'zero or absent tests'
        assert 'could not compile' not in text,'compile failure'
        assert 'skipping:' not in text,'data unavailable'
        assert any(a['artifact'].get('executable') for a in artifacts),'no executable artifact'
    return meta
