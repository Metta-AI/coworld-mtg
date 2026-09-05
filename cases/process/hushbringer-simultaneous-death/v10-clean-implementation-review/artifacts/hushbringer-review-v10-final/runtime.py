import pathlib,json,hashlib,subprocess,re,os,datetime,copy
O=pathlib.Path(__file__).parent; ROOT=pathlib.Path("/home/ubuntu/repos/phase-verifiable-loop"); C=pathlib.Path("/home/ubuntu/repos/coworld-mtg")
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+"\n")
def loader(bin,env,out):
 data=subprocess.check_output(["/usr/bin/ldd",str(bin)],env=env,text=True);(out/"ldd.txt").write_text(data)
 libs=[]
 for path in re.findall(r"(/[^\s()]+)",data):
  p=pathlib.Path(path)
  if p.is_file(): libs.append({"path":path,"realpath":str(p.resolve()),"sha256":sha(p)})
 return libs
base=C/"tmp/verifiable-loop/isolated-baseline-build"; worker=base/"worker"
assert sha(worker)=="e4e8cb9d6024592745a0da533bcd86001c8115184a1ddcf0163c1f3f04494d98"
p=O/"original-runtime";p.mkdir(exist_ok=True)
corpus=C/"cases/corpus/corpus.json";assert sha(corpus)=="8b7151e61d99082ba22c39ee5dc56e798e339e44387af5834f6b3c1982dfbb3c";(p/"corpus.json").write_bytes(corpus.read_bytes())
scenario=json.loads((C/"cases/cards/hushbringer-simultaneous-death.json").read_text())["scenario"]
env={"PATH":"/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin","LANG":"C.UTF-8","LC_ALL":"C.UTF-8","RUST_MIN_STACK":"16777216"}
results=[]
for name in ["hush-first","traveler-first","no-hush"]:
 s=copy.deepcopy(scenario)
 if name=="traveler-first": s["cards"][0],s["cards"][1]=s["cards"][1],s["cards"][0]
 if name=="no-hush":s["cards"]=[x for x in s["cards"] if x["label"]!="hush"]
 req={"protocol":"coworld-improvement-v1","corpus_path":str(p/"corpus.json"),"corpus_sha256":sha(corpus),"scenario":s}
 request=p/(name+"-request.json"); output=p/(name+"-execution.json");write(request,req)
 cmd=[str(worker),"case","execute","--request",str(request),"--output",str(output)]
 run=subprocess.run(cmd,cwd=base/"source",env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);log=p/(name+".log");log.write_text(run.stdout);assert run.returncode==0,run.stdout
 data=json.loads(output.read_text());obs=data["outcome"]["observation"];objects=obs["objects"];count=sum(x["name"]=="Spirit" and x["zone"]=="battlefield" for x in objects)
 assert data["binary_sha256"]==sha(worker);assert data["declared_phase_revision"]=="2dec6c88915db4697706234a7ba2fcedd97b1689";assert count==1
 labels=["traveler","wrath"]+([] if name=="no-hush" else ["hush"])
 assert all(next(x for x in objects if x["object_id"]==obs["labels"][l])["zone"]=="graveyard" for l in labels)
 results.append({"name":name,"command":cmd,"exit":run.returncode,"spirit_count":count,"graveyard_guards":True,"request_sha256":sha(request),"execution_sha256":sha(output),"log_sha256":sha(log)})
write(p/"receipt.json",{"utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"method":"Independent direct original binary execution; no new compilation","worker_sha256":sha(worker),"build_receipt_sha256":sha(base/"build.json"),"cwd":str(base/"source"),"environment":env,"loader":loader(worker,env,p),"results":results})
# Candidate source is comment-only successor. This is direct fdc9 binary execution, never a claimed new compilation.
p=O/"candidate-runtime";p.mkdir(exist_ok=True);prior=O.parent/"hushbringer-v10-review-fixes";bin=prior/"canonical-integration";assert sha(bin)=="d4cd42e9718570a16acedb3d44c90e0d9f2b3ffcba9841da132baedfde0ea9bf"
build=json.loads((prior/"canonical-integration-receipt.json").read_text());env.update(build["env_overlay"]);env["CARGO_MANIFEST_DIR"]=str(ROOT/"crates/engine");env["CARGO_MANIFEST_PATH"]=str(ROOT/"crates/engine/Cargo.toml");env["RUSTUP_TOOLCHAIN"]="nightly-2026-04-19-x86_64-unknown-linux-gnu"
toolchain=pathlib.Path("/home/ubuntu/.rustup/toolchains")/env["RUSTUP_TOOLCHAIN"];env["LD_LIBRARY_PATH"]=":".join([str(ROOT/"target/debug"),str(ROOT/"target/debug/deps"),str(toolchain/"lib/rustlib/x86_64-unknown-linux-gnu/lib"),str(toolchain/"lib")])
names=["oracle_wrath_hush_first_suppresses_simultaneous_traveler_death","oracle_wrath_traveler_first_suppresses_simultaneous_traveler_death","oracle_wrath_without_hush_creates_exactly_one_spirit"]+[f"native_library_choice_{source}_{pos}_public_controls" for source in ["hand","library","dig_tracked"] for pos in ["top","bottom","nth"]]
results=[]
for name in names:
 cmd=[str(bin),"trigger_suppression_event_timing::"+name,"--exact","--nocapture","--test-threads=1"]
 run=subprocess.run(cmd,cwd=ROOT/"crates/engine",env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);log=p/(name+".log");log.write_text(run.stdout)
 assert run.returncode==0,run.stdout
 m=re.search(r"test result: ok\. (\d+) passed; (\d+) failed; (\d+) ignored;",run.stdout);assert m and m.groups()==("1","0","0"),run.stdout
 cases=len(re.findall(r"NATIVE_LIBRARY_CHOICE_CASE",run.stdout))
 results.append({"name":name,"command":cmd,"exit":0,"selected":1,"passed":1,"ignored":0,"native_case_markers":cases,"log_sha256":sha(log)})
write(p/"receipt.json",{"utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"method":"Independent direct execution of preserved canonical fdc9 artifact; exact citation-only successor lineage recorded separately","fresh_compilation":False,"compiled_source_manifest_sha256":build["source_manifest_sha256"],"reviewed_source_manifest_sha256":"ee906941362b78f3ad170fc733a4ca34ee28fcd571f7fafe14f3c900e7204847","build_receipt_sha256":sha(prior/"canonical-build.json"),"canonical_receipt_sha256":sha(prior/"canonical-integration-receipt.json"),"executable":str(bin),"executable_sha256":sha(bin),"cwd":str(ROOT/"crates/engine"),"environment":env,"loader":loader(bin,env,p),"results":results})
print(json.dumps({"original":[[x["name"],x["spirit_count"]] for x in json.loads((O/"original-runtime/receipt.json").read_text())["results"]],"candidate_passed":len(results),"native_case_markers":sum(x["native_case_markers"] for x in results)}))
