import json,hashlib,pathlib,re,subprocess,tarfile,datetime
R=pathlib.Path("/home/ubuntu/repos/phase-verifiable-loop")
P=pathlib.Path("/home/ubuntu/coworld-migration-20260904/hushbringer-v10-citation-fix")
O=pathlib.Path(__file__).parent
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest()
def write(n,d): (O/n).write_text(json.dumps(d,indent=2)+"\n")
s=json.loads((P/"frozen-source/source.json").read_text()); oldp=P.parent/"hushbringer-v10-review-fixes/frozen-source/source.json"; old=json.loads(oldp.read_text())
assert sha(P/"frozen-source/source.json")=="ee906941362b78f3ad170fc733a4ca34ee28fcd571f7fafe14f3c900e7204847"
assert sha(R/"docs/MagicCompRules.txt")=="4381ad1b39ab2c05f7d03633a20f711ed37277074d3266dcba5f38cbb527423f"
assert all(sha(R/f)==h for f,h in s.items())
changed=[f for f in s if s[f]!=old[f]]; assert changed==["crates/engine/src/game/engine_resolution_choices.rs"]
lineage=json.loads((P/"frozen-source/lineage.json").read_text())
with tarfile.open(lineage["prior_source_archive"]) as t:
 for f,h in old.items():
  try: data=t.extractfile(f).read()
  except KeyError: data=t.extractfile("./"+f).read()
  assert hashlib.sha256(data).hexdigest()==h
  if f in changed:
   now=(R/f).read_bytes(); assert now.replace(b"// CR 608.2d: Resolution-time selection for PutAtLibraryPosition",b"// CR 115.1: Resolution-time selection for PutAtLibraryPosition")==data
files=subprocess.check_output(["git","diff","--name-only","HEAD"],cwd=R,text=True).splitlines()+subprocess.check_output(["git","ls-files","--others","--exclude-standard"],cwd=R,text=True).splitlines()
assert len(files)==30
write("source-audit.json",{"utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"source_sha256":sha(P/"frozen-source/source.json"),"files":len(s),"live_files_match":True,"changed_vs_fdc9":changed,"unchanged_vs_fdc9":2050,"inverse_citation_restores_prior_full_file":True,"prior_archive_files_verified":len(old),"base":subprocess.check_output(["git","rev-parse","HEAD"],cwd=R,text=True).strip(),"branch":subprocess.check_output(["git","branch","--show-current"],cwd=R,text=True).strip(),"changed_files":{f:sha(R/f) for f in files},"patch_sha256":sha(P/"frozen-source/candidate.patch"),"rules_sha256":sha(R/"docs/MagicCompRules.txt")})
# Reconstruct the entire candidate patch, including new modules, independent of supplied freeze.
diff=subprocess.check_output(["git","diff","HEAD","--binary"],cwd=R)
for f in subprocess.check_output(["git","ls-files","--others","--exclude-standard"],cwd=R,text=True).splitlines():
 result=subprocess.run(["git","diff","--no-index","--binary","--","/dev/null",f],cwd=R,stdout=subprocess.PIPE); diff+=result.stdout
(O/"live-candidate.patch").write_bytes(diff)
# Authoritative maps, fully parsed, all referenced artifacts rehashed (historical mutable target refs classified separately).
selected=json.loads((P/"reviewed-map-selection.json").read_text())["authoritative_maps"]
inputs={k:P/v for k,v in selected.items()}; inputs["handoff"]=P/"handoff.json"
refs={}
def walk(v):
 if isinstance(v,dict):
  if isinstance(v.get("path"),str) and v["path"].startswith("/") and re.fullmatch("[a-f0-9]{64}",str(v.get("sha256",""))): refs.setdefault(v["path"],set()).add(v["sha256"])
  for x in v.values(): walk(x)
 elif isinstance(v,list):
  for x in v: walk(x)
for f in inputs.values(): walk(json.loads(f.read_text()))
checks=[]
for p,hs in sorted(refs.items()):
 q=pathlib.Path(p); actual=sha(q) if q.is_file() else None
 checks.append({"path":p,"expected":sorted(hs),"actual":actual,"matches":actual in hs,"classification":"mutable-target-historical-reference" if "/target/" in p else "immutable-evidence"})
write("evidence-rehash.json",{"inputs":{str(f):sha(f) for f in inputs.values()},"refs":checks})
# No author semantic verdict is copied: record exact source comment context and local rules independently.
patch=(P/"frozen-source/candidate.patch").read_text().splitlines(); ann=[]; f=None; n=0
for l in patch:
 if l.startswith("+++ b/"): f=l[6:]
 elif l.startswith("@@"):
  m=re.search(r"\+(\d+)",l); n=int(m.group(1))-1
 elif l.startswith("+"):
  n+=1
  if re.search(r"CR \d{3}",l): ann.append({"file":f,"line":n,"text":l[1:]})
 elif l.startswith(" "): n+=1
rules=(R/"docs/MagicCompRules.txt").read_text()
for a in ann:
 lines=(R/a["file"]).read_text().splitlines(); assert lines[a["line"]-1]==a["text"]
 a["context"]="\n".join(lines[max(0,a["line"]-2):a["line"]+5]); a["rules"]={}
 for rule in re.findall(r"CR (\d{3}(?:\.\d+[a-z]?)?)",a["text"]):
  found=re.findall(r"^"+re.escape(rule)+r"\.?(?: |\t).*?(?=\n\s*\n|\Z)",rules,re.M|re.S)
  a["rules"][rule]=found
write("cr-source-audit.json",ann)
# Non-repeated semantic fields from every row; evidence is separately fully retained and hashed above.
m=json.loads((P/"production-path-maintainer-map.json").read_text()); seen={}; summaries=[]
for r in m["rows"]:
 d={}
 for k in ["id","file","operations","physical_seam","production_entry","first_reaching_branch","selected_authority","binding_time","storage","consumer","invalidation","serialized_impact","hostile_and_sibling_controls","tests","evidence_classification","reached_assertions","independent_structural_map","fixture_map"]:
  if k in r:
   sig=json.dumps(r[k],sort_keys=True)
   if k not in ["id","file","tests"] and (k,sig) in seen:d[k]="same as "+seen[k,sig]
   else:d[k]=r[k];seen[k,sig]=r["id"]
 summaries.append(d)
write("maintainer-review-input.json",summaries)
print(json.dumps({"source_files":len(s),"changed":len(files),"annotation_rows":len(ann),"reference_count":len(checks),"mismatches":[c for c in checks if not c["matches"]],"matrix_rows":len(summaries)}))
