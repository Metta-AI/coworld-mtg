import pathlib,json,hashlib,subprocess,datetime,copy
R=pathlib.Path("/home/ubuntu/repos/coworld-mtg");P=pathlib.Path("/home/ubuntu/repos/phase-verifiable-loop");O=pathlib.Path(__file__).parent;E=O.parent
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
read=lambda p:json.loads(pathlib.Path(p).read_text())
def normalized(x):
 x=copy.deepcopy(x)
 if x.get("origin",{}).get("kind","authored")=="authored":x.pop("origin",None)
 x.setdefault("guards",[])
 for c in x["scenario"]["cards"]:c.setdefault("tapped",False);c.setdefault("plus_one_counters",0)
 for op in x["scenario"]["operations"]:
  if op["kind"]=="cast":op.setdefault("x",None)
 return x
base=R/"tmp/verifiable-loop/isolated-baseline-build";checker=R/"tmp/verifiable-loop/attributed-baseline-build";b=read(base/"build.json");c=read(checker/"build.json")
assert sha(base/"worker")==b["binary_sha256"]=="e4e8cb9d6024592745a0da533bcd86001c8115184a1ddcf0163c1f3f04494d98"
assert sha(checker/"worker")==c["binary_sha256"]=="f9faf4b72b5f3df0342290a0ee30ac3207c799c6032ec2679090fc37bc656dd1"
assert b["harness_source_files"]==c["harness_source_files"]
for name,h in b["harness_source_files"].items():
 for root in [R,base/"source",checker/"source"]:assert sha(root/name)==h,(root,name)
assert sha(R/"scripts/build-case-worker.py")==b["builder_sha256"]=="6a96deecaf9ad7355731d698678675b22e12f4b3e1a5b5dcc2ec9d59ab40ebb7"
planpath=R/"tmp/verifiable-loop/hushbringer-acceptance-plan.json";plan=read(planpath)
assert sha(planpath)=="62273bd941f13b5d1587b1f098c7db4a61cd39c5f96fb0a2bd61db32c631a715"
assert digest(plan)=="a7805de648da28015f0f68f8e94e8edc1770eba15ab75b355563cd27ad451c2f"
assert len(plan["regression_case_ids"])==7 and len(plan["holdout_case_ids"])==2
assert len(set([plan["case_id"]]+plan["regression_case_ids"]+plan["holdout_case_ids"]))==10
cases=[]
for f in sorted((R/"cases/cards").glob("*.json")):
 case=normalized(read(f));id=digest(case);assert id in [plan["case_id"]]+plan["regression_case_ids"]+plan["holdout_case_ids"]
 cases.append(dict(path=str(f),raw_sha256=sha(f),typed_case_id=id,classification="target" if id==plan["case_id"] else "regression" if id in plan["regression_case_ids"] else "holdout",case=case))
assert len(cases)==10
corpus=R/"cases/corpus/corpus.json";assert sha(corpus)=="8b7151e61d99082ba22c39ee5dc56e798e339e44387af5834f6b3c1982dfbb3c"
sourcepath=E/"hushbringer-v10-citation-fix/frozen-source/source.json";source=read(sourcepath)
for f,h in source.items():assert sha(P/f)==h
head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=P,text=True).strip();assert head=="fa0ebfe88db224ebd32624bb96ef033d338c2d8c"
assert not subprocess.check_output(["git","status","--porcelain","--untracked-files=normal"],cwd=P)
assert subprocess.check_output(["git","rev-parse","HEAD^"],cwd=P,text=True).strip()=="2dec6c88915db4697706234a7ba2fcedd97b1689"
review=E/"hushbringer-review-v10-final/review-report.json";assert sha(review)=="be29698badceaa2add9f90213642feb4e91d6682535b79a97f61f712d5d6a7a2"
for f,h in read(review.parent/"manifest.json").items():assert sha(review.parent/f)==h
v=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),frozen_plan_raw_sha256=sha(planpath),frozen_plan_typed_id=digest(plan),plan=plan,cases=cases,corpus_sha256=sha(corpus),baseline_worker_sha256=sha(base/"worker"),checker_sha256=sha(checker/"worker"),baseline_build_sha256=sha(base/"build.json"),checker_build_sha256=sha(checker/"build.json"),harness_source_files=b["harness_source_files"],harness_files_verified_in_all_three_locations=39,phase_committed_revision=head,reviewed_phase_source_manifest_sha256=sha(sourcepath),reviewed_phase_source_files_verified=2051,phase_worktree_clean=True,implementation_review_sha256=sha(review),implementation_review_manifest_sha256=sha(review.parent/"manifest.json"),builder_sha256=sha(R/"scripts/build-case-worker.py"),cargo_launcher_sha256=sha(R/"scripts/cargo.sh"),comparison_script_sha256=sha(R/"scripts/compare-case-workers.py"),final_worker_launcher_sha256=sha(E/"build-final-committed-worker.py"),assessment="Frozen checker/adapter/core acceptance contract reviewed. Workers receive scenario and corpus only; expected values stay coordinator-side. Receipts require exact two-run equality, complete ordered operation checkpoints, exact guard outcomes, same frozen corpus/checker, disjoint planned gates and distinct workers. Approval binds exact plan/receipt hashes. Candidate build and comparison remain pending; no approval written.")
(O/"preaudit.json").write_text(json.dumps(v,indent=2)+"\n")
print("preaudit PASS:39 frozen harness files;2051 exact committed Phase files;10 frozen case IDs; independent approval still pending")
for c in cases:print(c["classification"],c["typed_case_id"],c["case"]["title"])
