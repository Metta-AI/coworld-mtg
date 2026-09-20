"""MTG adapter: verified frozen acquisition, case derivation, and native fitting."""
from pathlib import Path
import csv, io, json, os, resource, subprocess
import cas
from contracts import Bounds

def acquire():
    cohort, corpus = cas.argument("cohort", True), cas.argument("corpus", True)
    manifest = cas.load(cohort / "cohort.json")
    games, cards = cohort / "games.csv", cohort / "cards.csv"
    # Never label this a fresh download; these are exact retained source bytes.
    assert cas.sha(games) == manifest["replay"]["sha256"]
    assert cas.sha(cards) == manifest["mapping"]["sha256"]
    original = cas.load(corpus / "original-manifest.json")
    export = corpus / "card-data.json"
    assert cas.sha(export) == original["artifacts"]["phase_card_data"]["sha256"]
    relocated = json.loads(json.dumps(original))
    relocated["artifacts"]["phase_card_data"]["stored_path"] = "card-data.json"
    relocated["manifest_id"] = ""
    relocated["manifest_id"] = cas.digest(relocated)
    runtime = cas.tree({"manifest.json": cas.json_value(relocated), "card-data.json": export}, "corpus")
    rows = list(csv.DictReader(io.StringIO(games.read_text())))
    assert len(rows) == len(manifest["cases"]) == manifest["replay"]["rows"]
    cases = {}
    for i, declared in enumerate(manifest["cases"]):
        assert declared["game_index"] == i
        cases[declared["case_id"]] = cas.json_value({
            "schema":"coworld/caos-case@1", **declared,
            "source_csv_sha256": cas.sha(games), "mapping_sha256":cas.sha(cards),
            "metadata": {k:rows[i].get(k) for k in ("num_mulligans","opp_num_mulligans","on_play","opening_hand")},
            "seed":i,
        })
    cas.emit(cas.receipt("acquisition", {
        "cases": len(cases), "acquisition":"rehash retained real 17Lands cohort; no new HTTP acquisition",
        "attribution":manifest["source"]["attribution"],
        "original_manifest_id":original["manifest_id"], "relocated_manifest_id":relocated["manifest_id"],
        "previously_inspected":True, "unseen_holdout":False,
    }, {"cohort":cohort,"corpus":corpus}, outputs={
        "cases":cas.tree(cases), "runtime":runtime, "games.csv":games, "cards.csv":cards,
    }))

def summary(result, constraints):
    fields = (constraints or {}).get("fields",[])
    return {
        "status":result["status"],
        "nodes":result.get("nodes"),
        "milestones_fitted":result.get("milestones_fitted"),
        "milestones_total":result.get("milestones_total",len((constraints or {}).get("milestones",[]))),
        "fully_covered_milestones":result.get("fully_covered_milestones"),
        "enforced_fields": sorted(f["column"] for f in fields if f["disposition"]=="enforced"),
        "field_contracts": {f["column"]:{k:f.get(k) for k in ("raw","disposition","projection","expected")} for f in fields},
        "assumptions":result.get("assumptions", (constraints or {}).get("assumptions",[])),
        "issues":result.get("issues",[]),
        "input_sha256":result.get("input_sha256"),
        "source_sha256":result.get("source_sha256"),
        "cards_mapping_sha256":result.get("cards_mapping_sha256"),
        "phase_revision":result.get("phase_revision"),
        "search":result.get("search"),
    }

def fit():
    names = ("case", "games", "cards", "runtime", "binary", "policy", "target")
    refs = {k:cas.argument(k) for k in names}
    case, policy = cas.load(refs["case"]),cas.load(refs["policy"])
    bounds = Bounds.parse(policy["bounds"])
    cas.fetch(refs["runtime"],True)
    executable = cas.scratch("binary")/"worker"
    cas.copy_value(refs["binary"], executable)
    executable.chmod(0o755)
    out = cas.scratch("fit")
    argv = [str(executable),"fit17lands",
        "--manifest-uri",str(refs["runtime"]/"manifest.json"),
        "--replay-data",str(refs["games"]),"--replay-sha256",case["source_csv_sha256"],
        "--cards-csv",str(refs["cards"]),"--cards-csv-sha256",case["mapping_sha256"],
        "--game-index",str(case["game_index"]), "--turn-pairs",str(bounds.turn_pairs),
        "--nodes",str(bounds.nodes),"--max-actions",str(bounds.max_actions),
        "--opponent-filler","Plains","--output-dir",str(out)]
    def limits():
        resource.setrlimit(resource.RLIMIT_AS,(bounds.memory_bytes,bounds.memory_bytes))
        os.setsid()
    import signal, time
    start = time.monotonic()
    with (out/"stdout.txt").open("w") as stdout, (out/"stderr.txt").open("w") as stderr:
        p = subprocess.Popen(argv,stdout=stdout,stderr=stderr,preexec_fn=limits)
        try:
            code=p.wait(timeout=bounds.deadline_seconds)
            status = "completed" if code==0 else "process_failure"
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGKILL); p.wait()
            code=None;status="external_deadline"
    elapsed = time.monotonic()-start
    constraints=json.loads((out/"constraints.json").read_text()) if (out/"constraints.json").exists() else {}
    raw=json.loads((out/"result.json").read_text()) if (out/"result.json").exists() and code==0 else {
        "status":status, "issues":[{"kind":status,"detail":"Native process did not return a completed fit.", "source_columns":[]}],
    }
    sem=summary(raw,constraints)
    sem.update({"case_id":case["case_id"],"game_index":case["game_index"],"execution":status})
    # Operational timing is retained but never an acceptance score.
    (out/"execution.json").write_bytes(cas.canonical({"argv":argv,"exit_code":code,"elapsed_seconds":elapsed,"deadline_seconds":bounds.deadline_seconds}))
    cas.emit(cas.receipt("fit", sem,refs,outputs={
        "semantic.json":cas.json_value(sem), "native":cas.store(out),
    }))

def discover():
    observations=cas.argument("observations")
    groups={}
    for path in sorted(observations.iterdir()):
        record=cas.read_receipt(path); result=record["result"]
        issues = result["issues"]
        if result["status"]=="matched_supported_projection" and result["fully_covered_milestones"] < result["milestones_total"]:
            issues=[*issues,{"kind":"partial_projection","detail":"Witness covers only the supported projection.","source_columns":[]}]
        for issue in issues:
            key=cas.digest({k:issue.get(k) for k in ("kind","detail","source_columns")})
            group=groups.setdefault(key,{"id":key,"kind":issue["kind"],"detail":issue["detail"],"source_columns":issue.get("source_columns",[]),"origins":[]})
            group["origins"].append({"case_id":result["case_id"],"observation":cas.identity(path),"request":record["request"]})
    issues=sorted(groups.values(),key=lambda x:(-len(x["origins"]),x["id"]))
    counts={}
    for path in observations.iterdir():
        status=cas.read_receipt(path)["result"]["status"];counts[status]=counts.get(status,0)+1
    cas.emit(cas.receipt("discovery",{"counts":counts,"issues":issues},
        {"observations":observations},outputs={"issues.json":cas.json_value(issues)}))
