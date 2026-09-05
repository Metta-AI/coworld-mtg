import datetime, difflib, hashlib, json, os, pathlib, re, subprocess, sys, tarfile, time, traceback
ROOT=pathlib.Path('/home/ubuntu/repos/phase-hushbringer-mutations-r2-r3')
OUT=pathlib.Path('/home/ubuntu/coworld-migration-20260904/hushbringer-v9-r2-r3-mutations')
FROZEN=pathlib.Path('/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/frozen-candidate-v9')
MANIFEST=json.loads((FROZEN/'source.json').read_text())
SPEC=json.loads(pathlib.Path('/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/proposed-independent-r2-r3-mutations.json').read_text())
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
    meta={'utc_start':started,'cwd':str(ROOT),'target':ENV['CARGO_TARGET_DIR'],'argv':args,'env':{k:v for k,v in ENV.items() if k.startswith(('CARGO_','RUST','FORGE_'))},'source_manifest_sha256':sha(directory/'source.json')}
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

def tests(seam):
    mapping={'bounce_followup_does_not_draw_when_caster_did_not_control_parent_target':'bounce_followup_skips_draw_when_opponent_controlled_parent_target'}
    for name in seam['tests']:
        name=mapping.get(name,name)
        if name.startswith('zone_change_object_condition_'):
            yield ['--lib'],'game::triggers::tests::'+name
        elif name.startswith('bounce_followup_'):
            yield ['--lib'],'game::effects::tests::'+name
        elif name.startswith('oversimplify_per_player_fractal_counters_'):
            yield ['--test','integration'],'oversimplify_per_player_fractal::'+name
        else:yield ['--test','integration'],'trigger_suppression_event_timing::'+name

def run_phase(seam,phase,expected):
    directory=OUT/(seam['id']+'-'+phase);directory.mkdir()
    snap=snapshot(directory,expected)
    results=[command(directory,'fmt',['cargo','fmt','--all','--check'],expected)]
    assert results[0]['exit']==0,'format failure'
    for i,(target,name) in enumerate(tests(seam)):
        results.append(command(directory,str(i),['cargo','test','-p','engine','--message-format=json']+target+[name,'--','--exact','--nocapture','--test-threads=1'],expected))
    save(directory/'receipt.json',{'seam':seam,'phase':phase,'snapshot':snap,'results':results})
    return results

def main():
    mode=sys.argv[1]
    if mode=='controls':
        verify(MANIFEST)
        for seam in SPEC['seams']:
            results=run_phase(seam,'before',MANIFEST)
            assert all(r['exit']==0 for r in results),seam['id']
        save(OUT/'controls-complete.json',{'utc':utc(),'verified':True})
    else:raise ValueError(mode)
if __name__=='__main__':
    try:main()
    except BaseException:
        traceback.print_exc();(OUT/('supervisor-'+sys.argv[1]+'.exit')).write_text('1\n');raise
    else:(OUT/('supervisor-'+sys.argv[1]+'.exit')).write_text('0\n')
