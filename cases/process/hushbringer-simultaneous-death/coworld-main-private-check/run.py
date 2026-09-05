from pathlib import Path
import subprocess,os,json,hashlib,datetime
b=Path(__file__).resolve().parent
r=Path("/home/ubuntu/repos/coworld-mtg-publish")
env=dict(os.environ)
env.update(PATH="/home/ubuntu/.cargo/bin:"+env["PATH"],CARGO_BUILD_JOBS="1",CARGO_PROFILE_DEV_DEBUG="0",CARGO_PROFILE_TEST_DEBUG="0",CARGO_INCREMENTAL="0",CARGO_TARGET_DIR=str(r/"target"))
commands=[["scripts/cargo.sh","test","--workspace","--locked","--features","private-corpus-tests"],["npm","run","test:e2e"]]
before=subprocess.check_output(["git","diff","--binary","HEAD"],cwd=r)
assert not before
receipt={"started":datetime.datetime.now(datetime.timezone.utc).isoformat(),"checkout":str(r),"head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=r,text=True).strip(),"phase_revision":json.loads((r/"phase-source.json").read_text())["revision"],"corpus_manifest_sha256":hashlib.sha256((r/".private/corpus/manifest.json").read_bytes()).hexdigest(),"build_environment":{k:v for k,v in env.items() if k.startswith(("CARGO_PROFILE_","CARGO_BUILD_JOBS","CARGO_INCREMENTAL","CARGO_TARGET_DIR"))},"commands":[]}
for i,cmd in enumerate(commands):
 started=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (b/f"{i}.log").open("w") as log:
  p=subprocess.run(cmd,cwd=r,env=env,stdout=log,stderr=subprocess.STDOUT)
 receipt["commands"].append({"command":cmd,"started":started,"finished":datetime.datetime.now(datetime.timezone.utc).isoformat(),"exit":p.returncode,"log":f"{i}.log","log_sha256":hashlib.sha256((b/f"{i}.log").read_bytes()).hexdigest()})
 (b/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
receipt["finished"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
receipt["tracked_diff_unchanged"]=subprocess.check_output(["git","diff","--binary","HEAD"],cwd=r)==before
(b/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
(b/"done").write_text("complete\n")
