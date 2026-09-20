#!/usr/bin/env python3
"""Project linked CAOS receipts into a public replay without exporting private inputs."""
import argparse, json, subprocess, shutil
from pathlib import Path

class Store:
    def __init__(self,path):self.path=path;self.cache={}
    def git(self,*args):
        return subprocess.check_output(["git","--git-dir",str(self.path),*args])
    def members(self,oid):
        if oid not in self.cache:
            if self.git("cat-file","-t",oid).strip()!=b"tree":return {}
            entries={}
            for entry in self.git("ls-tree","-z",oid).split(b"\0"):
                if not entry:continue
                meta,name=entry.split(b"\t",1);mode,kind,child=meta.split()
                entries[name.decode()]=(kind.decode(),child.decode())
            self.cache[oid]=entries
        return self.cache[oid]
    def at(self,oid,path):
        for name in path.split("/"):
            child=self.members(oid).get(name)
            if child is None:return None
            oid=child[1]
        return oid
    def blob(self,oid):return self.git("cat-file","blob",oid)
    def record(self,oid):
        child=self.at(oid,"receipt.json")
        if child is None:return None
        return json.loads(self.blob(child))

def export(store,root,out):
    out.mkdir(parents=True,exist_ok=True)
    nodes={};edges=[]
    def visit(oid):
        if oid in nodes:return
        record=store.record(oid)
        if record is None:return
        node={"id":oid,**record,"artifacts":{}}
        nodes[oid]=node
        for label,child in record["inputs"].items():
            targets=[child]
            if label in ("baseline","observations","candidate-observations"):
                targets=[v[1] for v in store.members(child).values()]
            for target in targets:
                if store.record(target):
                    visit(target);edges.append({"from":target,"to":oid,"label":label})
        for path in ("native/result.json","native/constraints.json","native/execution.json","native/stderr.txt","inputs/infrastructure-error","inputs/provider-error",
                     "candidate.diff","edits.json","build.log","test.log"):
            child=store.at(oid,path)
            if child is None:continue
            name=oid+"-"+path.replace("/","-")
            (out/name).write_bytes(store.blob(child));node["artifacts"][path]=name
        if record["kind"].startswith("model-"):
            child=store.at(oid,"inputs/response")
            if child:
                name=oid+"-model-call.json";(out/name).write_bytes(store.blob(child));node["artifacts"]["model-call.json"]=name
    visit(root)
    if root not in nodes:raise ValueError("root is not a factory receipt")
    # A leaf consumes an output object, not its producer's whole receipt/history.
    # Recover those true data edges by matching object identities.
    producers={}
    for oid,node in nodes.items():
        for name,(kind,child) in store.members(oid).items():
            if name not in ("receipt.json","inputs"):
                producers.setdefault(child,set()).add(oid)
                if name=="cases":
                    for _,case in store.members(child).values():producers.setdefault(case,set()).add(oid)
    edge_keys={(e["from"],e["to"],e["label"]) for e in edges}
    for oid,node in nodes.items():
        for label,child in node["inputs"].items():
            for producer in producers.get(child,()):
                key=(producer,oid,label)
                if producer!=oid and key not in edge_keys:
                    edges.append({"from":producer,"to":oid,"label":label});edge_keys.add(key)
    for label,variant in (("baseline","Baseline"),("candidate-observations","Candidate")):
        group=nodes[root]["inputs"].get(label)
        if group:
            for _,child in store.members(group).values():
                if child in nodes:nodes[child]["variant"]=variant
    for label,variant in (("baseline-build","Baseline"),("candidate-build","Candidate")):
        child=nodes[root]["inputs"].get(label)
        if child in nodes:nodes[child]["variant"]=variant
    data={"schema":"coworld/caos-replay@1","root":root,"nodes":list(nodes.values()),"edges":edges,
        "disclosure":"Linked execution receipts exported from CAOS. Corpus, binaries, source snapshots, prompts and credentials are omitted. Their object IDs remain in the receipts. The cohort was previously inspected; this is not an unseen holdout."}
    (out/"replay.json").write_text(json.dumps(data,indent=2))
    shutil.copy2(Path(__file__).with_name("viewer.html"),out/"index.html")
    return data

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--store",type=Path,required=True);p.add_argument("--root",required=True);p.add_argument("--output",type=Path,required=True)
    args=p.parse_args();data=export(Store(args.store),args.root,args.output)
    print(json.dumps({"nodes":len(data["nodes"]),"edges":len(data["edges"]),"root":args.root}))
