import run as runner
r=runner.r
import pathlib,json,os,time,subprocess,difflib,traceback

def auxiliary():
    inputs=json.loads((r.OUT/'build-inputs.json').read_text());observed={}
    for group in ['compiler_tools','generated_outputs']:
        observed[group]={}
        for path,value in inputs[group].items():
            actual=r.sha(path);assert actual==value['sha256'],path
            observed[group][path]={'sha256':actual,'mtime_ns':pathlib.Path(path).stat().st_mtime_ns}
    assert r.sha(r.OUT/'generated-build-outputs.tar.gz')==inputs['generated_archive_sha256']
    return {'utc':r.utc(),'build_inputs_sha256':r.sha(r.OUT/'build-inputs.json'),'observed':observed}

def phase(row,kind,expected,canonical):
    before=auxiliary();results,binary=runner.phase(row,kind,expected,canonical)
    directory=r.OUT/(row['id']+'-runtime-'+kind)
    record=json.loads((directory/'receipt.json').read_text())
    record.update(auxiliary_before=before,auxiliary_after=auxiliary(),driver_sha256=r.sha(__file__),runner_sha256=r.sha(r.OUT/'run.py'),support_sha256=r.sha(r.OUT/'support.py'),case_map_sha256=r.sha(r.OUT/'case-map.json'))
    r.save(directory/'receipt.json',record);return results,binary

def main():
    assert (r.OUT/'canonical.exit').read_text().strip()=='0'
    confirmed=json.loads((r.OUT/'canonical-runtime-confirmed/receipt.json').read_text());assert all(x['exit']==0 for x in confirmed['results'])
    complete=json.loads((r.OUT/'canonical-complete.json').read_text());assert complete['case_map_sha256']==r.sha(r.OUT/'case-map.json') and complete['runtime_context_sha256']==r.sha(r.OUT/'runtime-context.json')
    binding=json.loads((r.OUT/'runtime-probe/binary.json').read_text());canonical=(pathlib.Path(binding['path']),binding)
    assert r.sha(canonical[0])==binding['sha256']
    rows=[]
    for row in runner.ROWS:
        r.verify(r.MANIFEST);before,_=phase(row,'before',r.MANIFEST,canonical);assert all(x['exit']==0 for x in before)
        job=r.OUT/row['id'];job.mkdir();path=r.ROOT/row['file'];original=runner.ORIGINAL[row['file']];error=None;summary=None
        try:
            path.write_text(runner.transform(original.decode(),row['operations']))
            args=['cargo','fmt','--all'];r.save(job/'format-preparation.command.json',{'argv':args,'cwd':str(r.ROOT),'utc':r.utc(),'source_before_sha256':r.sha(path)})
            with (job/'format-preparation.log').open('wb') as stream:rc=subprocess.call(args,cwd=r.ROOT,env=r.ENV,stdout=stream,stderr=subprocess.STDOUT)
            (job/'format-preparation.exit').write_text(str(rc)+'\n');assert rc==0
            expected=r.source();changes=[name for name in r.MANIFEST if expected[name]!=r.MANIFEST[name]];assert changes==[row['file']],changes
            patch=''.join(difflib.unified_diff(original.decode().splitlines(True),path.read_text().splitlines(True),fromfile='a/'+row['file'],tofile='b/'+row['file']));(job/'mutation.patch').write_text(patch)
            r.save(job/'mutation.json',{'row':row,'original_sha256':r.MANIFEST[row['file']],'mutant_sha256':r.sha(path),'patch_sha256':r.sha(job/'mutation.patch'),'source_mtime_ns':path.stat().st_mtime_ns,'driver_sha256':r.sha(__file__),'runner_sha256':r.sha(r.OUT/'run.py'),'support_sha256':r.sha(r.OUT/'support.py')})
            mutant,_=phase(row,'mutant',expected,canonical)
            exact={x['argv'][1]:x for x in mutant[1:]};assert set(exact)==set(row['tests'])
            designated=[];controls=[]
            for name in row['designated']:
                record=exact[name];log=pathlib.Path(record['log']).read_text();is_assertion=record['exit']==101 and 'panicked at ' in log and 'assertion' in log
                designated.append({'name':name,'exit':record['exit'],'reached_assertion':is_assertion,'log':record['log'],'log_sha256':record['log_sha256']})
            for name in row['controls']:controls.append({'name':name,'exit':exact[name]['exit'],'log':exact[name]['log'],'log_sha256':exact[name]['log_sha256']})
            success=all(x['reached_assertion'] for x in designated) and all(x['exit']==0 for x in controls)
            summary={'id':row['id'],'outcome':'both designated orders reached assertions; all named controls passed' if success else 'unresolved discrimination or named control outcome','matrix_counts':runner.counts(mutant[0],runner.TOTAL,runner.IGNORED),'designated':designated,'controls':controls,'complete_discrimination':success}
        except BaseException:
            error=traceback.format_exc();(job/'attempt-error.txt').write_text(error)
        finally:
            mutated_mtime=path.stat().st_mtime_ns;started=time.time_ns();path.write_bytes(original);stamp=time.time_ns();os.utime(path,ns=(stamp,stamp))
            other_changes=[name for name in r.MANIFEST if r.sha(r.ROOT/name)!=r.MANIFEST[name]]
            for name in other_changes:
                p=r.ROOT/name;p.write_bytes(runner.ORIGINAL[name]);now=time.time_ns();os.utime(p,ns=(now,now))
            r.verify(r.MANIFEST);assert path.stat().st_mtime_ns>=started and path.stat().st_mtime_ns>mutated_mtime
            r.save(job/'restoration.json',{'utc':r.utc(),'file':row['file'],'restored_sha256':r.sha(path),'original_sha256':r.MANIFEST[row['file']],'mutated_mtime_ns':mutated_mtime,'restored_mtime_ns':path.stat().st_mtime_ns,'fresh_mtime':True,'all2051_verified':True,'unexpected_other_restores':other_changes,'method':'exact candidate bytes freshly written; same matrix and exact filters rerun using preserved canonical executable; no restoration compilation claimed'})
            restored,_=phase(row,'restored',r.MANIFEST,canonical);assert all(x['exit']==0 for x in restored)
        if error:raise RuntimeError(error)
        assert summary is not None;summary.update(utc=r.utc(),restored=True);r.save(job/'result.json',summary);rows.append(summary);r.save(r.OUT/'progress.json',rows);print('ROW COMPLETE',json.dumps(summary),flush=True)
    r.verify(r.MANIFEST);r.save(r.OUT/'two-complete.json',{'utc':r.utc(),'rows':rows,'all_source_restored':True,'all_discriminated':all(x['complete_discrimination'] for x in rows),'repair_approval':False})
if __name__=='__main__':
    try:main()
    except BaseException:
        traceback.print_exc();(r.OUT/'mutations.exit').write_text('1\n');raise
    else:(r.OUT/'mutations.exit').write_text('0\n')
