"""Frozen acceptance logic; candidate code cannot edit this module or policy."""
from pathlib import Path
import difflib, json
import cas
from contracts import Edit, safe_relative

def apply_edits(source: Path, edits: list[dict], allowed: list[str]):
    changes=[]
    for item in edits:
        edit=Edit.parse(item);safe_relative(edit.path)
        if edit.path not in allowed:raise ValueError("edit outside frozen allowlist: "+edit.path)
        path=source/edit.path
        if path.is_symlink() or not path.resolve().is_relative_to(source.resolve()):raise ValueError("unsafe edit path")
        old=path.read_text()
        if old.count(edit.old)!=1:raise ValueError("edit does not match exactly once: "+edit.path)
        new=old.replace(edit.old,edit.new,1)
        # CAOS materializes immutable blobs read-only; this is our private copy.
        path.chmod(path.stat().st_mode | 0o200)
        path.write_text(new)
        changes.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile="a/"+edit.path,tofile="b/"+edit.path))
    return "".join(changes)

def candidate():
    source=cas.argument("source");implementation=cas.argument("implementation")
    root=cas.scratch("candidate")/"source";cas.copy_value(source,root)
    proposal=cas.read_receipt(implementation)["result"]
    if not proposal["valid"]:raise ValueError("invalid implementation")
    edits=proposal["value"]["edits"]
    try:
        diff=apply_edits(root,edits,cas.value("policy")["target"]["allowed_paths"])
        p=cas.scratch("diff")/"candidate.diff";p.write_text(diff)
        result={"valid":True,"summary":proposal["value"]["summary"],"base_source":cas.identity(source)}
        outputs={"source":cas.store(root),"edits.json":cas.json_value(edits),"candidate.diff":cas.store(p)}
    except (ValueError,OSError) as e:
        result={"valid":False,"error":str(e)};outputs={}
    cas.emit(cas.receipt("candidate",result,{"source":source,"implementation":implementation,"policy":cas.argument("policy"),"plan":cas.argument("plan")},outputs=outputs))

def compare_pair(before,after):
    reasons=[]
    def more(key):
        return type(before.get(key)) is int and type(after.get(key)) is int and after[key]>before[key]
    def less(key):
        return type(before.get(key)) is int and (type(after.get(key)) is not int or after[key]<before[key])
    if before["case_id"]!=after["case_id"]:reasons.append("case identity changed")
    for key in ("source_sha256","cards_mapping_sha256"):
        if before.get(key) and after.get(key) and before[key]!=after[key]:reasons.append(key+" changed")
    bc,ac=before.get("field_contracts",{}),after.get("field_contracts",{})
    for name,field in bc.items():
        other=ac.get(name)
        if other is None:reasons.append("source field omitted: "+name);continue
        if field.get("raw")!=other.get("raw"):reasons.append("source field altered: "+name)
        if field["disposition"]=="enforced" and any(field[k]!=other.get(k) for k in ("disposition","projection","expected")):
            reasons.append("enforced field contract changed: "+name)
    if not set(before["enforced_fields"])<=set(after["enforced_fields"]):reasons.append("lost enforced coverage")
    if less("fully_covered_milestones"):reasons.append("lost fully covered milestones")
    if before["status"]=="matched_supported_projection" and after["status"]!="matched_supported_projection":reasons.append("regressed compatible trajectory")
    if less("milestones_fitted"):reasons.append("lost compatible prefix")
    if after["execution"] not in ("completed",):reasons.append("candidate execution unresolved")
    # Wall-clock noise, changed labels, and removed errors never count as improvement.
    improved = not reasons and (
        more("fully_covered_milestones")
        or more("milestones_fitted")
        or (after["status"]==before["status"]=="matched_supported_projection" and
            type(before.get("nodes")) is int and type(after.get("nodes")) is int and 0<after["nodes"]<before["nodes"])
        or (after["status"]=="matched_supported_projection" and before["status"]!="matched_supported_projection")
    )
    return {"case_id":before["case_id"],"before":before["status"],"after":after["status"],
        "improved":bool(improved),"reasons":reasons,
        "nodes_before":before["nodes"],"nodes_after":after["nodes"],
        "assumptions_changed":before.get("assumptions")!=after.get("assumptions")}

def compare():
    baseline=cas.argument("baseline");candidate=cas.argument("observations")
    rows=[];before={p.name:p for p in baseline.iterdir()};after={p.name:p for p in candidate.iterdir()}
    reasons=[]
    if set(before)!=set(after):reasons.append("case set changed")
    for key in sorted(set(before)&set(after)):
        rows.append(compare_pair(cas.read_receipt(before[key])["result"],cas.read_receipt(after[key])["result"]))
    improved=sum(x["improved"] for x in rows)
    passed=not reasons and not any(x["reasons"] for x in rows) and improved>=cas.value("policy")["evaluation"]["minimum_improved_cases"]
    result={"passed":passed,"improved":improved,"cases":rows,"reasons":reasons,
        "previously_inspected":True,"unseen_holdout":False,
        "claim":"Measured bounded compatibility/progress only. Candidate-produced witnesses are not independently proof-checked."}
    cas.emit(cas.receipt("comparison",result,{"baseline":baseline,"observations":candidate,"policy":cas.argument("policy")}))
