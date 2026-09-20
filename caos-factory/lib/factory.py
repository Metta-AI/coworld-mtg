"""The factory is a continuation program. This file never executes child work."""
import cas
from contracts import Bounds

ROOT_KEYS=("cohort","corpus","source","policy","llm","sample")

def state():
    p=cas.argument("state")
    return {x.name:x for x in p.iterdir()}

def advance(stage,refs,callback,values,literals=None):
    cas.run_then(stage,refs,callback,{"state":cas.tree(values,"state")},literals,catch=True)

def next_result(values,name):
    if (cas.ARGS/"error").exists():
        values["infrastructure-error"]=cas.argument("error")
        finish(values,"inconclusive","CAOS child failed; inspect the linked infrastructure error.")
        return False
    values[name]=cas.argument("result")
    return True

def finish(values,verdict,reason):
    plan=cas.read_receipt(values["plan"])["result"].get("value") if "plan" in values else None
    result={"verdict":verdict,"reason":reason,"automatic_publication":False,
        "component":plan["component"] if plan else None,
        "origin_issue_ids":plan["issue_ids"] if plan else [],
        "claim":"Bounded compatibility under declared assumptions; no rules-correctness proof.",
        "previously_inspected":True,"unseen_holdout":False}
    # Seal actual executed request trees as Git links, not merely IDs in JSON.
    # The final controller request also retains the whole factory definition.
    requests={}
    for key,path in values.items():
        cas.fetch(path)
        candidates=list(path.iterdir()) if key in ("baseline","candidate-observations") else [path]
        for candidate in candidates:
            cas.fetch(candidate)
            if not candidate.is_dir() or not (candidate/"receipt.json").exists():continue
            oid=cas.read_receipt(candidate)["request"]
            if oid not in requests:
                dest=cas.Path("/cas/sealed-request-"+oid)
                cas.command("get-hash",oid,str(dest));requests[oid]=dest
    record=cas.receipt("decision",result,values,outputs={"requests":cas.tree(requests),"controller-request":cas.ARGS})
    cas.emit(cas.commit(record,"Coworld factory epoch: "+verdict+"\n\n"+reason))

def start():
    values={k:cas.argument(k) for k in ROOT_KEYS}
    policy=cas.load(values["policy"]);bounds=Bounds.parse(policy["bounds"])
    if bounds.max_model_calls<4:raise ValueError("a complete attempted epoch needs allowance for four roles")
    advance("acquire",{k:values[k] for k in ("cohort","corpus")},"acquired",values)

def acquired():
    values=state()
    if not next_result(values,"acquisition"):return
    advance("vendor",{"source":values["source"]},"vendored",values)

def vendored():
    values=state()
    if not next_result(values,"dependencies"):return
    advance("build",{k:values[k] for k in ("source","dependencies","policy")},"baseline-built",values)

def baseline_built():
    values=state()
    if not next_result(values,"baseline-build"):return
    if not cas.read_receipt(values["baseline-build"])["result"]["passed"]:
        return finish(values,"inconclusive","Baseline build or tests failed.")
    launch_fits(values,values["source"],values["baseline-build"],"baseline-fitted")

def launch_fits(values,source,build,callback):
    acquired=values["acquisition"];cas.fetch(acquired)
    cases=cas.fetch(acquired/"cases")
    refs={"games":acquired/"games.csv","cards":acquired/"cards.csv","runtime":acquired/"runtime",
        "binary":build/"binary","target":source,"policy":values["policy"]}
    requests={p.name:cas.request_path("fit",{**refs,"case":p}) for p in sorted(cases.iterdir())}
    cas.fanout(requests,callback,{"state":cas.tree(values,"state")},cas.load(values["policy"])["bounds"]["concurrency"])

def baseline_fitted():
    values=state();values["baseline"]=cas.argument("children")
    advance("discover",{"observations":values["baseline"]},"discovered",values)

def discovered():
    values=state()
    if not next_result(values,"discovery"):return
    launch_role(values,"plan","planned")

def launch_role(values,role,callback):
    refs={k:values[k] for k in ("source","policy","discovery","llm","sample")}
    refs["evaluator"]=cas.ARGS/"modules"/"evaluate.py"
    for k in ("plan","candidate","comparison","prior-plan","prior-plan-review"):
        if k in values:refs[k]=values[k]
    if "candidate-build" in values:refs["build"]=values["candidate-build"]
    advance("role",refs,callback,values,{"role":role})

def valid_role(values,name):
    if not next_result(values,name):return None
    result=cas.read_receipt(values[name])["result"]
    if not result["valid"]:
        finish(values,"inconclusive","Model stage could not produce a valid result: "+name+" ("+result.get("error","unknown failure")+")")
        return None
    return result["value"]

def planned():
    values=state()
    if not next_result(values,"plan"):return
    result=cas.read_receipt(values["plan"])["result"]
    if not result["valid"]:
        # A malformed model proposal is feedback, not permission to coerce it.
        # This shares the one revision allowance with plan-review rejection.
        if result.get("failure_kind")=="invalid_response" and may_revise(values):
            values["prior-plan"]=values.pop("plan")
            return launch_role(values,"plan","planned")
        return finish(values,"inconclusive","Model stage could not produce a valid result: plan ("+result.get("error","unknown failure")+")")
    plan=result["value"]
    if plan["status"]=="no_safe_change":return finish(values,"no_change","Planner found no safe bounded change.")
    launch_role(values,"plan-review","plan-reviewed")

def may_revise(values):
    return "prior-plan" not in values and cas.load(values["policy"])["bounds"]["max_model_calls"]>=6

def plan_reviewed():
    values=state();review=valid_role(values,"plan-review")
    if review is None:return
    if not review["approve"]:
        if may_revise(values):
            values["prior-plan"]=values.pop("plan")
            values["prior-plan-review"]=values.pop("plan-review")
            return launch_role(values,"plan","planned")
        return finish(values,"rejected","Independent plan review rejected the proposed change.")
    launch_role(values,"implement","implemented")

def implemented():
    values=state();implementation=valid_role(values,"implementation")
    if implementation is None:return
    advance("candidate",{k:values[k] for k in ("source","implementation","plan","policy")},"candidate-created",values)

def candidate_created():
    values=state()
    if not next_result(values,"candidate"):return
    if not cas.read_receipt(values["candidate"])["result"]["valid"]:
        return finish(values,"rejected","Candidate edits did not apply under the frozen edit policy.")
    refs={k:values[k] for k in ("dependencies","policy")};refs["source"]=values["candidate"]/"source"
    advance("build",refs,"candidate-built",values)

def candidate_built():
    values=state()
    if not next_result(values,"candidate-build"):return
    if not cas.read_receipt(values["candidate-build"])["result"]["passed"]:
        return finish(values,"rejected","Candidate build or regression tests failed.")
    candidate=cas.fetch(values["candidate"])
    launch_fits(values,cas.fetch(candidate/"source"),values["candidate-build"],"candidate-fitted")

def candidate_fitted():
    values=state();values["candidate-observations"]=cas.argument("children")
    advance("compare",{"baseline":values["baseline"],"observations":values["candidate-observations"],"policy":values["policy"]},"compared",values)

def compared():
    values=state()
    if not next_result(values,"comparison"):return
    launch_role(values,"implementation-review","reviewed")

def reviewed():
    values=state();review=valid_role(values,"implementation-review")
    if review is None:return
    metrics=cas.read_receipt(values["comparison"])["result"]
    if not review["approve"]:return finish(values,"rejected","Independent implementation review rejected the candidate.")
    if not metrics["passed"]:return finish(values,"rejected","Candidate did not satisfy the frozen comparison policy.")
    finish(values,"accepted","Build/tests passed, no measured regression, at least one improvement, and both reviews approved.")

def dispatch():
    cas.command("run-request-then",str(cas.argument("in")))
