from pathlib import Path
import datetime,hashlib,json,os,subprocess
work=Path('/home/ubuntu/repos/phase-hushbringer-baseline-tests');out=Path('/home/ubuntu/coworld-migration-20260904')
assert subprocess.check_output(['git','diff','HEAD','--','crates/engine/src','Cargo.toml','Cargo.lock'],cwd=work)==b''
env=dict(os.environ,PATH='/home/ubuntu/.cargo/bin:'+os.environ['PATH'],CARGO_BUILD_JOBS='2',CARGO_TARGET_DIR=str(work/'target'))
rows=[]
for label,query in [('lki','game::triggers::tests::zone_change_object_condition_'),('bounce','game::effects::tests::bounce_followup_draws_when_caster_controlled_parent_target')]:
    command=['cargo','test','-p','engine','--lib',query,'--','--nocapture','--test-threads=2']
    logpath=out/f'hushbringer-root-baseline-library-v7-{label}.log'
    with logpath.open('x') as log: result=subprocess.run(command,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT)
    (out/f'hushbringer-root-baseline-library-v7-{label}.exit').write_text(str(result.returncode)+'\n')
    rows.append({'command':command,'command_exit':result.returncode,'log':str(logpath),'log_sha256':hashlib.sha256(logpath.read_bytes()).hexdigest()})
assert subprocess.check_output(['git','diff','HEAD','--','crates/engine/src','Cargo.toml','Cargo.lock'],cwd=work)==b''
(out/'hushbringer-root-baseline-library-v7-receipt.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=work,text=True).strip(),'production_diff_empty':True,'target':str(work/'target'),'results':rows},indent=2)+'\n')
