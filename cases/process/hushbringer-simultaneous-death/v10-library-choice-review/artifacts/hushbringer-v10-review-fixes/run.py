import datetime, hashlib, json, os, pathlib, subprocess, sys, tarfile
cfg=json.loads(pathlib.Path(sys.argv[1]).read_text());root=pathlib.Path(cfg["checkout"]);out=pathlib.Path(cfg["output"]);out.mkdir(exist_ok=False)
env=dict(os.environ,PATH="/home/ubuntu/.cargo/bin:"+os.environ["PATH"],CARGO_BUILD_JOBS="1",CARGO_TARGET_DIR=str(root/"target"),RUST_MIN_STACK="16777216",RTK_DISABLED="1")
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(set(f for f in subprocess.check_output(["git","ls-files","--cached","--others","--exclude-standard","crates","Cargo.toml","Cargo.lock","rust-toolchain.toml",".cargo"],cwd=root,env=env,text=True).splitlines() if (root/f).is_file()))
def manifest(): return {f:h(root/f) for f in files}
archive_root=pathlib.Path("/home/ubuntu/coworld-migration-20260904/hushbringer-v10-review-fixes/source-archives");archive_root.mkdir(exist_ok=True)
def archive_source(before):
 key=hashlib.sha256((json.dumps(before,indent=2)+"\n").encode()).hexdigest();path=archive_root/(key+".tar.gz")
 if not path.exists():
  with tarfile.open(path,"w:gz") as tar:
   for f in files:tar.add(root/f,arcname=f,recursive=False)
 return {"path":str(path),"sha256":h(path),"manifest_sha256":key}
receipt={"config":cfg,"utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"target":env["CARGO_TARGET_DIR"],"env":{k:env[k] for k in ["PATH","CARGO_BUILD_JOBS","CARGO_TARGET_DIR","RUST_MIN_STACK","RTK_DISABLED"]},"results":[]}
for index,command in enumerate(cfg["commands"]):
 before=manifest();(out/f"{index}-source.json").write_text(json.dumps(before,indent=2)+"\n");source_archive=archive_source(before)
 with (out/f"{index}.log").open("wb") as stream:result=subprocess.run(command,cwd=root,env=env,stdout=stream,stderr=subprocess.STDOUT)
 after=manifest();(out/f"{index}-after-source.json").write_text(json.dumps(after,indent=2)+"\n")
 receipt["results"].append({"command":command,"exit":result.returncode,"log":str(out/f"{index}.log"),"log_sha256":h(out/f"{index}.log"),"source_manifest_sha256":h(out/f"{index}-source.json"),"source_archive":source_archive,"changed":[f for f in files if before[f]!=after[f]]})
 (out/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
 if result.returncode and cfg.get("stop_on_failure",True): break
receipt["finished_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat();(out/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n");(out/"done").write_text("done\n")
