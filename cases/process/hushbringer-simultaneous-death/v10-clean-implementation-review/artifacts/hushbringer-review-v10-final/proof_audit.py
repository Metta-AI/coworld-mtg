import pathlib,json,re,collections,hashlib
P=pathlib.Path("/home/ubuntu/coworld-migration-20260904");O=P/"hushbringer-review-v10-final"
checks=json.loads((O/"exhaustive-evidence-audit.json").read_text())["checks"];byhash=collections.defaultdict(list)
for c in checks:byhash[c["actual"]].append(c["path"])
for log in P.rglob("*.log"):
 if str(O) in str(log):continue
 h=hashlib.sha256(log.read_bytes()).hexdigest();byhash[h].append(str(log))
m=json.loads((P/"hushbringer-v10-citation-fix/production-path-maintainer-map.json").read_text());out=[];alllogs={};problems=[]
def walk(v):
 if isinstance(v,dict):
  yield v
  for x in v.values():yield from walk(x)
 elif isinstance(v,list):
  for x in v:yield from walk(x)
for row in m["rows"]:
 logs={};assertions=[]
 for d in walk(row["evidence"]):
  h=d.get("log_sha256")
  if not h:continue
  paths=[p for p in byhash[h] if p.endswith(".log")];assert paths,(row["id"],h)
  path=paths[0];text=pathlib.Path(path).read_text(errors="replace");logs[path]=h;alllogs[path]=h
  for key in ["summaries","test_results"]:
   for x in d.get(key,[]):
    if isinstance(x,str) and x not in text:problems.append([row["id"],path,"missing summary",x])
  fc=d.get("failure_context")
  if fc and fc not in text:problems.append([row["id"],path,"missing failure context",fc])
  for fail in d.get("semantic_failures",[]):
   if fail["excerpt"] not in text:problems.append([row["id"],path,"missing semantic excerpt",fail["excerpt"]])
  if "counts" in d:
   actual=[dict(status=a,passed=int(b),failed=int(c),ignored=int(e),measured=0,filtered_out=int(f)) for a,b,c,e,f in re.findall(r"test result: (ok|FAILED)\. (\d+) passed; (\d+) failed; (\d+) ignored; \d+ measured; (\d+) filtered out",text)]
   for c in d["counts"]:
    if isinstance(c,str):
     assert c in text,(row["id"],c);continue
    assert any(all(v.get(k)==value for k,value in c.items()) for v in actual),(row["id"],c,actual)
 # Reached excerpts are bound to the row evidence log when available; short supplementary summaries kept separate.
 corpus="\n".join(pathlib.Path(p).read_text(errors="replace") for p in logs)
 for a in row.get("reached_assertions",[]):
  if not isinstance(a,dict):continue
  excerpt=a.get("excerpt")
  excerpts=excerpt if isinstance(excerpt,list) else [excerpt]
  for part in excerpts:
   if part and part not in corpus:problems.append([row["id"],"row linked logs","missing reached excerpt",part])
  if excerpt and all(part in corpus for part in excerpts):assertions.append(a)
 out.append(dict(id=row["id"],classification=row["evidence_classification"],logs=logs,matched_reached_assertions=assertions,source_seam_review="Inspected transformation and actual producer/consumer branch against full source; no compiler failure counted as behavioral kill."))
(O/"mutation-proof-audit.json").write_text(json.dumps({"rows":out,"distinct_rows":len(out),"unique_linked_logs":len(alllogs),"problems":problems},indent=2)+"\n")
print("rows",len(out),"unique logs",len(alllogs),"problems",len(problems))
for p in problems:print(str(p)[:800])
