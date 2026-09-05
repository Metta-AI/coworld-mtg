import support as r
import pathlib,os,threading,time,json,traceback,subprocess,re,shutil,tarfile
CONFIG=json.loads((r.OUT/'case-map.json').read_text())
D=r.OUT/'runtime-probe'
ALLOW={'RUST_MIN_STACK','RUST_TEST_THREADS','RUST_BACKTRACE','RUST_LIB_BACKTRACE','LD_LIBRARY_PATH','DYLD_FALLBACK_LIBRARY_PATH','LD_PRELOAD','LD_AUDIT','CARGO_MANIFEST_DIR','CARGO_MANIFEST_PATH','CARGO','CARGO_TARGET_DIR','CARGO_BUILD_JOBS','RUSTUP_HOME','CARGO_HOME','PATH','PWD','RTK_DISABLED','FORGE_TEST_FULL_DB','PHASE_TRIGGER_INDEX_AUDIT','PHASE_REPLACEMENT_INDEX_AUDIT','GATED_SETS','GATED_SETS_AS_OF','RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','CARGO_BUILD_RUSTFLAGS','RUSTC_WRAPPER','RUSTC_WORKSPACE_WRAPPER'}
stop=threading.Event();capture=[]
def observe():
    while not stop.is_set():
        for p in pathlib.Path('/proc').iterdir():
            if not p.name.isdecimal():continue
            try:
                exe=os.readlink(p/'exe')
                if not exe.startswith(str(r.ROOT/'target/debug/deps/integration-')):continue
                status=(p/'status').read_text();ppid=next(x.split()[1] for x in status.splitlines() if x.startswith('PPid:'))
                parent_exe=os.readlink('/proc/'+ppid+'/exe')
                if not parent_exe.endswith('/cargo'):continue
                values={}
                for item in (p/'environ').read_bytes().split(b'\0'):
                    if b'=' not in item:continue
                    k,v=item.split(b'=',1);key=k.decode()
                    if key in ALLOW or key.startswith(('CARGO_PKG_','CARGO_BIN_EXE_')):values[key]=v.decode()
                record={'utc':r.utc(),'pid':int(p.name),'parent_pid':int(ppid),'parent_executable':parent_exe,'executable':exe,'executable_sha256':r.sha(exe),'actual_cwd':os.readlink(p/'cwd'),'argv':(p/'cmdline').read_bytes().decode().split('\0')[:-1],'allowlisted_environment':values,'allowlist':sorted(ALLOW),'additional_safe_prefixes':['CARGO_PKG_','CARGO_BIN_EXE_'],'source_manifest_sha256':r.sha(D/'source.json')}
                r.save(D/'actual-cargo-runtime.json',record);capture.append(record);return
            except (FileNotFoundError,ProcessLookupError,PermissionError):continue
        time.sleep(.03)

def main():
    D.mkdir();r.verify(r.MANIFEST)
    tools={};versions={}
    for name in ['cargo','rustc']:
        path=pathlib.Path(subprocess.check_output(['rustup','which',name],cwd=r.ROOT,env=r.ENV,text=True).strip());tools[str(path)]={'sha256':r.sha(path),'mtime_ns':path.stat().st_mtime_ns};versions[name]=subprocess.check_output([str(path),'-Vv'],cwd=r.ROOT,env=r.ENV,text=True)
        if name=='rustc':
            for lib in (path.parent.parent/'lib').glob('librustc_driver-*.so'):tools[str(lib)]={'sha256':r.sha(lib),'mtime_ns':lib.stat().st_mtime_ns}
    r.save(r.OUT/'compiler-toolchain-before.json',{'utc':r.utc(),'tools':tools,'versions':versions,'source_inputs':{p:r.MANIFEST[p] for p in ['Cargo.lock','rust-toolchain.toml','.cargo/config.toml','crates/engine/build.rs','crates/engine/data/known-tokens.toml']}})
    r.snapshot(D,r.MANIFEST);fmt=r.command(D,'fmt',['cargo','fmt','--all','--check'],r.MANIFEST);assert fmt['exit']==0
    watcher=threading.Thread(target=observe,daemon=True);watcher.start()
    result=r.command(D,'matrix',['cargo','test','-p','engine','--message-format=json','--test','integration',CONFIG['matrix_filter'],'--','--nocapture','--test-threads=1'],r.MANIFEST)
    stop.set();watcher.join(timeout=2)
    assert result['exit']==0 and len(result['test_results'])==1
    m=re.search(r'(\d+) passed; (\d+) failed; (\d+) ignored;',result['test_results'][0]);assert m and tuple(map(int,m.groups()))==(CONFIG['matrix_passed'],0,CONFIG['matrix_ignored'])
    assert capture and capture[0]['actual_cwd']==str(r.ROOT/'crates/engine')
    assert capture[0]['allowlisted_environment']['RUST_MIN_STACK']=='16777216'
    fresh_engine=[a for a in result['compiler_artifacts'] if a['artifact']['target']['name']=='engine' and not a['artifact']['fresh']];assert fresh_engine
    for a in fresh_engine:assert any(f['newer_than_command_start'] for f in a['hashed_files'])
    integration=[a for a in result['compiler_artifacts'] if a['artifact']['target']['name']=='integration' and a['artifact'].get('executable')];assert len(integration)==1
    artifact=integration[0];assert artifact['artifact']['fresh'] is False and any(f['newer_than_command_start'] for f in artifact['hashed_files'])
    old=pathlib.Path(artifact['artifact']['executable']);exe=D/'integration-executable';shutil.copyfile(old,exe);exe.chmod(0o755)
    binding={'path':str(exe),'sha256':r.sha(exe),'source_manifest_sha256':r.sha(D/'source.json'),'source_archive_sha256':r.sha(D/'source.tar.gz'),'cargo_command_receipt':str(D/'matrix.receipt.json'),'cargo_command_receipt_sha256':r.sha(D/'matrix.receipt.json'),'compiler_artifact':artifact,'fresh_engine_artifacts':fresh_engine,'runtime_manifest_sha256':r.sha(r.OUT/'runtime-inputs.json'),'compiler_toolchain_before_sha256':r.sha(r.OUT/'compiler-toolchain-before.json')}
    assert binding['sha256']==capture[0]['executable_sha256']==r.sha(old);r.save(D/'binary.json',binding)
    ctx=capture[0];env=r.ENV.copy();env.update(ctx['allowlisted_environment'])
    args=['ldd',str(exe)];proc=subprocess.run(args,cwd=ctx['actual_cwd'],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(D/'ldd.log').write_text(proc.stdout);assert proc.returncode==0
    libs={}
    for line in proc.stdout.splitlines():
        m=re.search(r'(?:=>\s+)?(/[^\s]+)',line)
        if m:
            path=pathlib.Path(m.group(1));assert path.is_file();libs[str(path)]={'resolved':str(path.resolve()),'sha256':r.sha(path)}
    assert libs
    ctx.update(dynamic_libraries=libs,canonical_binary_binding=str(D/'binary.json'),ldd={'argv':args,'exit':proc.returncode,'log_sha256':r.sha(D/'ldd.log')});r.save(r.OUT/'runtime-context.json',ctx)
    builds=[];generated={}
    for line in pathlib.Path(result['log']).read_text().splitlines():
        if not line.startswith('{'):continue
        try:j=json.loads(line)
        except json.JSONDecodeError:continue
        if j.get('reason')!='build-script-executed':continue
        builds.append(j)
        for path in sorted(pathlib.Path(j['out_dir']).rglob('*')):
            if path.is_file():generated[str(path)]={'sha256':r.sha(path),'mtime_ns':path.stat().st_mtime_ns,'bytes':path.stat().st_size,'package_id':j['package_id']}
    with tarfile.open(r.OUT/'generated-build-outputs.tar.gz','w:gz') as archive:
        for path in generated:archive.add(path,arcname=str(pathlib.Path(path).relative_to(r.ROOT)),recursive=False)
    for path,record in tools.items():assert r.sha(path)==record['sha256']
    r.save(r.OUT/'build-inputs.json',{'utc':r.utc(),'timing':'Compiler tools recorded before canonical compile and rechecked after; generated outputs recorded immediately after canonical compile and before every mutation. Source build inputs are included in every complete source archive.','compiler_tools':tools,'generated_outputs':generated,'build_script_records':builds,'generated_archive_sha256':r.sha(r.OUT/'generated-build-outputs.tar.gz'),'canonical_compile_receipt_sha256':r.sha(D/'matrix.receipt.json')})
    r.save(D/'receipt.json',{'utc':r.utc(),'fmt':fmt,'matrix':result,'actual_runtime':ctx,'binary_binding':binding})
    import run as runner
    named=sorted({name for row in CONFIG['rows'] for name in row['tests']})
    results,_=runner.phase({'id':'canonical','tests':named},'confirmed',r.MANIFEST,(exe,binding));assert all(x['exit']==0 for x in results)
    r.save(r.OUT/'canonical-complete.json',{'utc':r.utc(),'case_map_sha256':r.sha(r.OUT/'case-map.json'),'runtime_context_sha256':r.sha(r.OUT/'runtime-context.json'),'binary_binding':binding,'fresh_cargo_matrix_passed':CONFIG['matrix_passed'],'ignored':CONFIG['matrix_ignored'],'confirmed_exact_filter_count':len(named),'all_source_and_runtime_verified':True})
if __name__=='__main__':
    try:main()
    except BaseException:
        stop.set();traceback.print_exc();(r.OUT/'canonical.exit').write_text('1\n');raise
    else:(r.OUT/'canonical.exit').write_text('0\n')
