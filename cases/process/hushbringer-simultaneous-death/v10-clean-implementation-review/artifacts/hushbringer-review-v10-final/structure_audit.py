import pathlib,json,re,hashlib,subprocess,collections
R=pathlib.Path("/home/ubuntu/repos/phase-verifiable-loop");P=pathlib.Path("/home/ubuntu/coworld-migration-20260904/hushbringer-v10-citation-fix");O=P.parent/"hushbringer-review-v10-final"
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(n,d):(O/n).write_text(json.dumps(d,indent=2)+"\n")
ca=json.loads((P/"constructor-audit.json").read_text());expected=collections.Counter((x["file"],x["line"]) for x in ca["constructors"] if x["file"]!="crates/engine/src/types/game_state.rs")
for x in ca["non_constructor_hits"]:expected[x["file"],x["line"]]+=x.get("occurrences",1)
found=collections.Counter()
for f in (R/"crates/engine").rglob("*.rs"):
 for m in re.finditer(r"\bZoneChangeRecord\s*\{",f.read_text()):found[str(f.relative_to(R)),f.read_text()[:m.start()].count("\n")+1]+=1
assert found==expected,(found-expected,expected-found)
constructors=[]
for row in ca["constructors"]:
 text=(R/row["file"]).read_text();start=sum(len(l) for l in text.splitlines(True)[:row["line"]-1]);fragment=text[start:];m=re.search(r"(?:ZoneChangeRecord|Self)\s*\{",fragment);assert m
 # Record lexical body excluding the constructor name, allowing nested Rust expressions.
 body=fragment[m.end()-1:];depth=0
 for i,c in enumerate(body):
  if c=="{":depth+=1
  elif c=="}":
   depth-=1
   if depth==0:body=body[:i+1];break
 assert ("trigger_suppression:" in body) or ".." in body,row
 constructors.append(dict(file=row["file"],line=row["line"],scope=row["scope"],actual_body_sha256=hashlib.sha256(body.encode()).hexdigest(),body=body))
mapd=json.loads((P/"production-entry-callsite-map.json").read_text());api=r"\b(with_departure_suppression|with_departure_member|with_departure_leaf|without_departure_member)\s*\(";calls=[]
for f in (R/"crates/engine/src").rglob("*.rs"):
 tx=f.read_text();tx=re.split(r"#\[cfg\(test\)\]\s*mod ",tx)[0]
 for m in re.finditer(api,tx):
  line=tx[:m.start()].count("\n")+1
  if re.search(r"\bfn\s*$",tx[max(0,m.start()-8):m.start()]):continue
  calls.append((str(f.relative_to(R)),line,m.group(1)))
expected_calls={(x["file"],x["line"],x["api"]) for x in mapd["call_sites"]}
assert set(calls)==expected_calls,(set(calls)-expected_calls,expected_calls-set(calls))
for x in mapd["call_sites"]:assert (R/x["file"]).read_text().splitlines()[x["line"]-1].strip()==x["source_line"]
B=pathlib.Path("/home/ubuntu/repos/coworld-mtg/tmp/verifiable-loop/isolated-baseline-build");b=json.loads((B/"build.json").read_text());checked=[]
for f,h in b["harness_source_files"].items():
 actual=sha(B/"source"/f);assert actual==h,(f,actual,h);checked.append(dict(path=str(B/"source"/f),sha256=actual))
assert sha(B/"worker")==b["binary_sha256"]
save("structure-audit.json",{"record_raw_hits":sum(found.values()),"actual_constructors":len(constructors),"production_constructors":3,"test_constructors":79,"record_constructors":constructors,"physical_callsites":len(calls),"callsites":mapd["call_sites"],"manual_review_note":"Declaration/impl, return signature and raw string occurrences were excluded explicitly; cfg(test) external modules classified from includes. All three production constructor expressions default to unavailable None; struct-update fixtures inherit their fixture default. All 51 physical owner/member/leaf/barrier callsites found independently and reconciled."})
save("original-runtime/source-provenance.json",{"build_receipt_sha256":sha(B/"build.json"),"worker_sha256":sha(B/"worker"),"baseline_phase_revision":b["phase"]["revision"],"harness_source_files_verified":checked,"fresh_compilation":False})
print("structure",len(constructors),len(calls),"baseline files",len(checked))
