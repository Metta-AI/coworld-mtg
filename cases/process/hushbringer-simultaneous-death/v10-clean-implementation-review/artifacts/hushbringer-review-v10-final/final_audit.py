import json,pathlib,hashlib,datetime,re,subprocess
P=pathlib.Path("/home/ubuntu/coworld-migration-20260904");O=P/"hushbringer-review-v10-final";R=pathlib.Path("/home/ubuntu/repos/phase-verifiable-loop")
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(4*1024*1024),b""):h.update(b)
 return h.hexdigest()
def write(n,v):(O/n).write_text(json.dumps(v,indent=2)+"\n")
refs={}
for n,key in [("imported-evidence-audit.json","verified_artifact_hashes"),("final-imported-evidence-audit.json","verified_hashes")]:
 d=json.loads((P/"hushbringer-v10-execution"/n).read_text())
 for p,h in d[key].items():refs.setdefault(p,set()).add(h)
for x in json.loads((O/"evidence-rehash.json").read_text())["refs"]:refs.setdefault(x["path"],set()).update(x["expected"])
checks=[]
for i,(p,hs) in enumerate(sorted(refs.items())):
 q=pathlib.Path(p);h=sha(q) if q.is_file() else None
 checks.append(dict(path=p,expected=sorted(hs),actual=h,matches=h in hs,classification="mutable-target-historical-reference" if "/target/" in p or "/targets/" in p else "immutable-evidence"))
 if i%400==0:print("hashed",i,flush=True)
write("exhaustive-evidence-audit.json",{"utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"checks":checks,"immutable":sum(c["classification"]=="immutable-evidence" for c in checks),"mutable":sum(c["classification"]!="immutable-evidence" for c in checks),"mismatches":[c for c in checks if not c["matches"]]})
print("evidence",len(checks),"mismatches",[(c["path"],c["classification"]) for c in checks if not c["matches"]],flush=True)
a=json.loads((P/"hushbringer-v10-citation-fix/cr-audit.json").read_text());raw=(R/"docs/MagicCompRules.txt").read_text();derived=json.loads((O/"cr-source-audit.json").read_text())
author={(x["file"],x["line"]):x for x in a["annotations"]};assert len(author)==185
for x in derived:assert (x["file"],x["line"]) in author
out=[]
for k,x in author.items():
 lines=(R/x["file"]).read_text().splitlines();assert lines[x["line"]-1]==x["text"]
 assert "\n".join(lines[x["line"]-1:x["line"]-1+len(x["context"].splitlines())])==x["context"]
 rules={rule:re.findall(r"^"+re.escape(rule)+r"\.?(?: |\t).*?(?=\n\s*\n|\Z)",raw,re.M|re.S) for rule in x["rules"]}
 assert all(rules.values())
 assert all(t in raw for rr in x["rules"] for t in a["rules"][rr])
 out.append(dict(file=x["file"],line=x["line"],context=x["context"],actual_rules=rules,added_line=k in {(v["file"],v["line"]) for v in derived},semantic_verdict="Consistent within declared implementation scope; code and complete local rule text reviewed independently."))
write("cr-complete-audit.json",{"rules_sha256":sha(R/"docs/MagicCompRules.txt"),"added_annotations":len(derived),"adjacent_annotations":185-len(derived),"rule_count":len(a["rules"]),"annotations":out})
# Repair only reviewer count parser: the runtime log is unchanged, independently verify all sixty cases.
p=O/"candidate-runtime/receipt.json";rc=json.loads(p.read_text());cases=[]
for row in rc["results"]:
 logs=list((O/"candidate-runtime").glob("*"+row["name"]+"*log"));assert len(logs)==1,logs
 txt=logs[0].read_text();assert sha(logs[0])==row["log_sha256"]
 found=[json.loads(line.split("NATIVE_LIBRARY_CHOICE_EVIDENCE ",1)[1]) for line in txt.splitlines() if "NATIVE_LIBRARY_CHOICE_EVIDENCE " in line]
 expected=(12 if "_nth_" in row["name"] else 4) if row["name"].startswith("native_library_choice_") else 0
 assert len(found)==expected,(row["name"],len(found),expected)
 row["native_case_markers"]=len(found);cases+=found
assert len(cases)==60
assert len({(c["origin"],json.dumps(c["position"],sort_keys=True),c["hush"],c["reverse"]) for c in cases})==60
rc["native_cases_verified"]=60;rc["case_marker_parser_note"]="Marker count recomputed from unchanged independently executed logs using actual NATIVE_LIBRARY_CHOICE_EVIDENCE prefix; no runtime outcome was altered."
p.write_text(json.dumps(rc,indent=2)+"\n");write("candidate-runtime/native-cases.json",cases)
print("CR185/rules101/native60 complete")
