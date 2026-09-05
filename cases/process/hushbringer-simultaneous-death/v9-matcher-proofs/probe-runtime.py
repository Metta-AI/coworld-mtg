import support as r
import pathlib,os,threading,time,json,traceback
r.OUT=pathlib.Path(__file__).resolve().parent
D=r.OUT/'runtime-probe';D.mkdir()
ALLOW={'RUST_MIN_STACK','RUST_TEST_THREADS','RUST_BACKTRACE','RUST_LIB_BACKTRACE','LD_LIBRARY_PATH','DYLD_FALLBACK_LIBRARY_PATH','CARGO_MANIFEST_DIR','CARGO_MANIFEST_PATH','CARGO','CARGO_TARGET_DIR','CARGO_BUILD_JOBS','RUSTUP_HOME','CARGO_HOME','PATH','PWD','RTK_DISABLED','FORGE_TEST_FULL_DB','PHASE_TRIGGER_INDEX_AUDIT'}
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
try:
    r.verify(r.MANIFEST);r.snapshot(D,r.MANIFEST)
    watcher=threading.Thread(target=observe,daemon=True);watcher.start()
    result=r.command(D,'matrix',['cargo','test','-p','engine','--message-format=json','--test','integration','trigger_suppression_event_timing','--','--nocapture','--test-threads=1'],r.MANIFEST)
    stop.set();watcher.join(timeout=2)
    assert result['exit']==0 and '91 passed; 0 failed; 20 ignored' in result['test_results'][0]
    assert capture and capture[0]['actual_cwd']==str(r.ROOT/'crates/engine')
    assert capture[0]['allowlisted_environment']['RUST_MIN_STACK']=='16777216'
    r.save(D/'receipt.json',{'utc':r.utc(),'matrix':result,'actual_runtime':capture[0]})
except BaseException:
    traceback.print_exc();(D/'supervisor.exit').write_text('1\n');raise
else:(D/'supervisor.exit').write_text('0\n')
