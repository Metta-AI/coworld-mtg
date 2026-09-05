import pathlib,json,hashlib,subprocess,os,re,datetime
O=pathlib.Path(__file__).parent;prior=json.loads((O/"candidate-runtime/receipt.json").read_text());env=os.environ.copy();env.update(prior["environment"]);out=O/"r3-runtime";out.mkdir(exist_ok=True)
rows=[]
for test in ["original_entry_lki_public_responses_preserve_original_condition","original_entry_lki_public_same_id_reentry_preserves_original_condition","original_entry_lki_public_unpumped_entry_does_not_trigger"]:
 cmd=[prior["executable"],"trigger_suppression_event_timing::"+test,"--exact","--nocapture","--test-threads=1"]
 r=subprocess.run(cmd,cwd=prior["cwd"],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(out/(test+".log")).write_bytes(r.stdout);text=r.stdout.decode();assert r.returncode==0;assert re.search(r"test result: ok\. 1 passed; 0 failed; 0 ignored;",text)
 rows.append(dict(test=test,command=cmd,exit=r.returncode,passed=1,ignored=0,log_sha256=hashlib.sha256(r.stdout).hexdigest()))
receipt=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),purpose="Independently validate actual current R3 entry-LKI fixtures while correcting stale authoritative map description",fresh_compilation=False,compiled_source_manifest_sha256=prior["compiled_source_manifest_sha256"],reviewed_source_manifest_sha256=prior["reviewed_source_manifest_sha256"],executable=prior["executable"],executable_sha256=prior["executable_sha256"],cwd=prior["cwd"],environment=prior["environment"],runtime_loader=prior["loader"],results=rows)
(out/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n");print("three R3 exact tests passed, zero ignored; preserved fdc9 binary")
