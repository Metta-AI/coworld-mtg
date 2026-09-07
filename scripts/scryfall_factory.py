#!/usr/bin/env python3
"""Run source-derived classification experiments and record portable factory replays."""
from __future__ import annotations
import argparse
from collections import Counter
import json
import re
from pathlib import Path
import subprocess

from factory_replay import Replay, canonical, sha256, encode_json, decode_jsonl
import mana_library_oracle as oracle
import scryfall_source

CLAIM = "Phase's parsed activated-ability classification agrees with CR605.1a for the frozen, source-qualified grammar; runtime gameplay is outside this acceptance claim."
CONFIG_PROVIDER = "Coworld factory configuration"


def read_json(path):
    return json.loads(Path(path).read_bytes())


def import_source(replay, identity, provider, url, retrieved_at, description):
    replay.event("sources", "source_imported", source={
        "snapshot_id": identity, "provider": provider, "url": url,
        "retrieved_at": retrieved_at, "description": description})


def artifact_json(replay, identity):
    meta = replay.value["artifacts"][identity]
    data = (replay.directory / meta["path"]).read_bytes()
    value = json.loads(data)
    expected = sha256(data if meta["hash_mode"] == "bytes" else canonical(value))
    if expected != identity:
        raise ValueError("artifact corruption: " + identity)
    return value


def config(replay):
    events = [e["payload"]["source"] for e in replay.value["events"]
              if e["payload"]["kind"] == "source_imported"
              and e["payload"]["source"]["provider"] == CONFIG_PROVIDER]
    if len(events) != 1:
        raise ValueError("run must have exactly one immutable factory configuration")
    result = artifact_json(replay, events[0]["snapshot_id"])
    report = artifact_json(replay, result["discovery_report_id"])
    source_hash = sha256(Path(scryfall_source.__file__).read_bytes())
    if source_hash != report["producer"]["script_sha256"] or source_hash not in replay.value["artifacts"]:
        raise ValueError("source grammar dependency differs from the frozen discovery producer")
    evaluator_hash = sha256(Path(oracle.__file__).read_bytes())
    if evaluator_hash != result["evaluator_sha256"]:
        raise ValueError("installed evaluator differs from the evaluator frozen for this run")
    return result


def prepare(args):
    if not hasattr(oracle, "evaluate_card"):
        raise ValueError("freeze the complete independent evaluator before preparing a run")
    frozen = read_json(args.plan_dir / "plan.json")
    if frozen["status"] != "ready":
        raise ValueError("source-only plan is blocked: " + str(frozen["blocking_reasons"]))
    cases_bytes = (args.plan_dir / "cases.jsonl").read_bytes()
    if sha256(cases_bytes) != frozen["cases_sha256"]:
        raise ValueError("frozen case inventory changed")
    entries = [json.loads(line) for line in cases_bytes.splitlines()]
    snapshot = read_json(args.snapshot_dir / "source-manifest.json")
    report_bytes = (args.discovery_dir / "report.json").read_bytes()
    if sha256(report_bytes) != frozen["discovery_report_sha256"]:
        raise ValueError("discovery report changed")
    rules_bytes = (args.snapshot_dir / "rules.txt").read_bytes()
    if sha256(rules_bytes) != frozen["recipe"]["rules"]["sha256"]:
        raise ValueError("rules snapshot changed")
    if snapshot["artifacts"]["archive"]["sha256"] != frozen["source_archive_sha256"]:
        raise ValueError("plan refers to a different Scryfall archive")

    with Replay.create(args.runtime, args.output_dir, args.run_id, args.title,
                           "Phase Oracle parser", "https://github.com/nishu-builder/phase",
                           args.baseline_revision) as replay:
        when = snapshot["completed_at"]
        manifest_id = replay.artifact(snapshot)
        import_source(replay, manifest_id, "Scryfall acquisition receipt",
                      snapshot["bulk_descriptor"]["uri"], when,
                      "Exact bulk download identity, request receipts, source dates and archive hash. The compressed archive is retained outside this portable run.")
        records = []
        for entry in entries:
            data = (args.plan_dir / entry["raw_record_path"]).read_bytes()
            if sha256(data) != entry["raw_record_sha256"]:
                raise ValueError("raw source record changed")
            card = json.loads(data)
            if oracle.source_contracts(card) != entry["source_contract"]:
                raise ValueError("source grammar changed since the case cohort was frozen")
            records.append(card)
        records_id = replay.artifact(json.dumps({"records": records, "source_manifest_id": manifest_id,
                                     "archive_sha256": frozen["source_archive_sha256"]}, ensure_ascii=False,
                                     sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8"), raw=True)
        import_source(replay, records_id, "Scryfall Oracle Cards",
                      snapshot["bulk_descriptor"]["jsonl_download_uri"], when,
                      "Exact card fields selected mechanically from the saved bulk snapshot; these are card definitions, not observed human games.")
        rules_id = replay.artifact(rules_bytes, raw=True, media_type="text/plain")
        import_source(replay, rules_id, "Wizards Comprehensive Rules",
                      frozen["recipe"]["rules"]["url"], when,
                      "Pinned rules effective August 7, 2026. Classification scope: CR605.1a.")
        report_id = replay.artifact(report_bytes, raw=True)
        import_source(replay, report_id, "Whole-snapshot discovery census",
                      "urn:coworld:scryfall-discovery-v1", frozen["frozen_at"],
                      "Every source row was audited. Eligibility, exclusions and broad text matches are discovery evidence, not semantic verdicts.")
        dependency_id = replay.artifact(Path(scryfall_source.__file__).read_bytes(), raw=True, media_type="text/x-python")
        import_source(replay, dependency_id, "Frozen evaluator source dependency",
                      "urn:coworld:scryfall-source-module-v1", frozen["frozen_at"],
                      "Exact source grammar dependency bound by the discovery producer's script hash.")
        source_plan_id = replay.artifact(frozen)
        import_source(replay, source_plan_id, "Frozen source-only case recipe",
                      "urn:coworld:mana-classification-source-plan-v1", frozen["frozen_at"],
                      "Case qualification and development/holdout assignment were fixed before inspecting classifier outcomes.")
        cases = []
        candidates = {row["oracle_id"]: row for row in
                      map(json.loads, (args.discovery_dir / "candidates.jsonl").read_text().splitlines())}
        for entry, card in zip(entries, records):
            raw = (args.plan_dir / entry["raw_record_path"]).read_bytes()
            case_id = replay.artifact(raw, raw=True)
            replay.event("cases", "case_registered", case_id=case_id, title=card["name"],
                         derivation={"kind": "source_derived",
                                     "source_ids": [manifest_id, records_id],
                                     "source_records": [{"source_id": records_id, "record_id": card["oracle_id"]}],
                                     "recipe": "Frozen whole-snapshot text nomination and source-only grammar; parse the actual selected card record. No gameplay scenario is invented.",
                                     "seed": None})
            nomination = {"case_id": case_id, "role": entry["role"], "split": entry["split"],
                          "source_contract": entry["source_contract"],
                          "discovery": candidates.get(card["oracle_id"]),
                          "control_symbol": entry.get("control_symbol")}
            replay.feedback(case_id, [], nomination,
                            evaluator="Scryfall source nomination",
                            evaluator_version=frozen["producer"]["recipe_sha256"],
                            strength="weak", method="Frozen source grammar and broad text scan",
                            claim="Source text matches a discovery signal or the predeclared simple-mana control predicate.",
                            result="satisfied",
                            summary=f'{entry["origin"]}; {entry["split"]}; {entry["role"]}. This nomination does not establish an engine failure.')
            cases.append({**entry, "case_id": case_id, "name": card["name"]})
        plan = {"case_id": next(row["case_id"] for row in cases if row["role"] == "primary"),
                "regression_case_ids": [row["case_id"] for row in cases if row["role"] == "regression"],
                "holdout_case_ids": [row["case_id"] for row in cases if row["role"] == "holdout"]}
        plan_id = replay.artifact(plan)
        replay.event("gates", "acceptance_plan_frozen", plan_id=plan_id, plan=plan)
        evaluator_id = replay.artifact(Path(oracle.__file__).read_bytes(), raw=True, media_type="text/x-python")
        policy = {"kind": "source-aligned-mana-classification-v1", "scope": CLAIM,
                  "plan_id": plan_id, "source_plan_id": source_plan_id, "evaluator_sha256": evaluator_id,
                  "rules_sha256": rules_id, "repetitions": 2,
                  "requirements": ["repeatable strong baseline violation on primary",
                                   "repeatable strong candidate satisfaction on every frozen gate",
                                   "same frozen evaluator and source records",
                                   "candidate execution bound to exact change",
                                   "independent approving review"],
                  "limitations": ["The qualified library-moving cards all fell in development.",
                                  "Strong holdouts test preservation of genuine mana abilities.",
                                  "Unsupported discovered cards remain in the replay as inconclusive.",
                                  "This policy does not certify runtime game semantics."]}
        policy_id = replay.artifact(policy)
        configuration = {"cases": cases, "plan_id": plan_id, "policy_id": policy_id,
                         "evaluator_sha256": evaluator_id, "rules_sha256": rules_id,
                         "source_plan_id": source_plan_id, "discovery_report_id": report_id,
                         "source_manifest_id": manifest_id}
        configuration_id = replay.artifact(configuration)
        import_source(replay, configuration_id, CONFIG_PROVIDER,
                      "urn:coworld:scryfall-factory-v1", frozen["frozen_at"],
                      "Immutable adapter configuration, evaluator identity, policy, case roles and frozen gates.")
        replay.save()
        subprocess.run([str(args.runtime), "verify", str(replay.directory)], check=True)
        print(json.dumps({"run": str(replay.directory), "cases": len(cases), "plan_id": plan_id}))


def classify_status(output):
    if output.get("status") == "parsed":
        return "completed", None
    if output.get("status") == "inconclusive":
        return "inconclusive", output.get("detail")
    raise ValueError("unknown Oracle probe observation")


def evaluate_runs(case_id, card, runs, phase_revision, cfg, declared_revision=None):
    observations = [run["observation"] for run in runs]
    declared_revision = declared_revision or phase_revision
    repeatable = (len(runs) == 2 and all(run["status"] == "completed" for run in runs)
                  and all(item.get("phase_revision") == declared_revision for item in observations if item)
                  and observations[0] == observations[1])
    evaluations = [oracle.evaluate_card(card, item) for item in observations]
    # Domain evaluator deliberately uses pass/fail/inconclusive, distinct from
    # the replay's feedback envelope. It never sees the candidate patch.
    verdicts = [evaluation["verdict"] for evaluation in evaluations]
    result = {"pass": "satisfied", "fail": "violated"}.get(verdicts[0], "inconclusive") if repeatable and len(set(verdicts)) == 1 else "inconclusive"
    return {"case_id": case_id, "evaluator_sha256": cfg["evaluator_sha256"],
            "rules_sha256": cfg["rules_sha256"], "phase_revision": phase_revision,
            "evidence_ids": [run["evidence_id"] for run in runs], "repeatable": repeatable,
            "evaluations": evaluations, "result": result}


def execute(args):
    with Replay(args.run_dir) as replay:
        cfg = config(replay)
        change_id = args.change_id
        if args.phase == "baseline" and change_id:
            raise ValueError("baseline cannot carry a candidate change")
        if args.phase == "candidate" and not change_id:
            raise ValueError("candidate must bind to a previously proposed change")
        if change_id and not any(e["payload"]["kind"] == "change_proposed" and
                                 e["payload"]["change_id"] == change_id for e in replay.value["events"]):
            raise ValueError("candidate change has not been proposed in this replay")
        attestation = read_json(args.build_attestation)
        if (attestation["binary_sha256"] != sha256(args.worker.read_bytes()) or
                attestation["phase_revision"] != args.phase_revision):
            raise ValueError("build attestation differs from worker bytes or actual source revision")
        if args.phase == "baseline" and args.phase_revision != replay.value["target"]["baseline_revision"]:
            raise ValueError("baseline build differs from the target baseline")
        if change_id and (attestation.get("phase_base_revision") != replay.value["target"]["baseline_revision"] or
                          attestation.get("phase_patch_sha256") != change_id):
            raise ValueError("candidate source attestation must bind the exact baseline and proposed patch")
        declared_revision = attestation.get("declared_phase_revision", attestation["phase_revision"])
        build_id = replay.build("Phase Oracle parser", args.phase_revision, args.worker,
                                attestation["command"], attestation["environment"], attestation)
        selected = [case for case in cfg["cases"]
                    if args.phase == "candidate" or case["split"] == "development"]
        summary = Counter()
        for index, case in enumerate(selected):
            case_id = case["case_id"]
            card = artifact_json(replay, case_id)
            prefix = f'{args.phase}-{(change_id or build_id)[:12]}-{case_id[:12]}'
            existing_ids = {e["payload"]["execution_id"] for e in replay.value["events"]
                            if e["payload"]["kind"] == "execution_started"}
            if any(identity.startswith(prefix) for identity in existing_ids):
                raise ValueError("this stage already has executions; use a fresh run to retain a new attempt")
            runs = [replay.run_jsonl(execution_id=f"{prefix}-{repeat}", case_id=case_id,
                                    build_id=build_id, binary=args.worker, record=card,
                                    change_id=change_id, protocol="oracle-probe-jsonl-v1",
                                    arguments=lambda src, dst: ["oracle-probe", "--input", str(src), "--output", str(dst)],
                                    classify_status=classify_status) for repeat in range(2)]
            receipt = evaluate_runs(case_id, card, runs, args.phase_revision, cfg, declared_revision)
            result = receipt["result"]
            feedback_id = replay.feedback(
                case_id, [run["execution_id"] for run in runs], receipt,
                evaluator="Independent source-aligned CR605.1a grammar",
                evaluator_version=cfg["evaluator_sha256"], strength="strong",
                method="Exact source/AST alignment followed by classification comparison; two isolated worker processes.",
                claim=CLAIM, result=result,
                summary=f'{args.phase}: {result}; {case["role"]}; repeatable={receipt["repeatable"]}.')
            summary[result] += 1
            print(json.dumps({"index": index, "name": case["name"], "role": case["role"],
                              "result": result, "feedback_id": feedback_id}), flush=True)
        print(json.dumps({"phase": args.phase, "counts": summary}))
        subprocess.run([str(args.runtime), "verify", str(replay.directory)], check=True)


def strong_feedbacks(replay):
    return [e["payload"]["feedback"] for e in replay.value["events"]
            if e["payload"]["kind"] == "feedback_recorded"
            and e["payload"]["feedback"]["declared_strength"] == "strong"]


def verify_domain(replay, cfg):
    """Recompute this installed, trusted policy; never execute replay-supplied code."""
    cases = {case["case_id"]: case for case in cfg["cases"]}
    starts = {e["payload"]["execution_id"]: e["payload"] for e in replay.value["events"]
              if e["payload"]["kind"] == "execution_started"}
    finishes = {e["payload"]["execution_id"]: e["payload"] for e in replay.value["events"]
                if e["payload"]["kind"] == "execution_finished"}
    builds = {e["payload"]["build_id"]: e["payload"]["build"] for e in replay.value["events"]
              if e["payload"]["kind"] == "build_recorded"}
    policy = artifact_json(replay, cfg["policy_id"])
    if (policy["kind"] != "source-aligned-mana-classification-v1" or
            policy["evaluator_sha256"] != cfg["evaluator_sha256"] or
            policy["plan_id"] != cfg["plan_id"] or policy["scope"] != CLAIM or
            policy["rules_sha256"] != cfg["rules_sha256"] or policy["repetitions"] != 2):
        raise ValueError("policy does not match the installed bounded evaluator")
    for feedback in strong_feedbacks(replay):
        if (feedback["adapter"] != "opaque" or
                feedback["evaluator"] != "Independent source-aligned CR605.1a grammar" or
                feedback["evaluator_version"] != cfg["evaluator_sha256"] or
                feedback["bounded_claim"] != policy["scope"]):
            raise ValueError("feedback attribution differs from the frozen evaluator and claim")
        case_id = feedback["case_id"]
        card = artifact_json(replay, case_id)
        if oracle.source_contracts(card) != cases[case_id]["source_contract"]:
            raise ValueError("case differs from frozen source qualification")
        runs = []
        revisions = set()
        declarations = set()
        repeated_builds = set()
        for execution_id in feedback["execution_ids"]:
            started, finished = starts[execution_id], finishes[execution_id]
            if started["case_id"] != case_id:
                raise ValueError("execution belongs to a different case")
            repeated_builds.add(started["build_id"])
            build = builds[started["build_id"]]
            attestation = artifact_json(replay, build["attestation_id"])
            if (attestation["binary_sha256"] != build["binary_sha256"] or
                    attestation["phase_revision"] != build["source_revision"]):
                raise ValueError("attestation differs from recorded binary/source build")
            if started["change_id"] is not None and (
                    attestation.get("phase_base_revision") != replay.value["target"]["baseline_revision"] or
                    attestation.get("phase_patch_sha256") != started["change_id"]):
                raise ValueError("candidate attestation differs from exact change and baseline")
            declarations.add(attestation.get("declared_phase_revision", attestation["phase_revision"]))
            request = artifact_json(replay, started["request_id"])
            evidence = artifact_json(replay, finished["evidence_id"])
            if evidence.get("detail") == "worker interrupted":
                expected_status = "cancelled"
            elif evidence["timed_out"] or evidence["exit_code"] != 0:
                expected_status = "error"
            else:
                try:
                    expected_status, _ = classify_status(evidence["observation"])
                except (ValueError, TypeError, KeyError, AttributeError):
                    expected_status = "error"
            if finished["status"] != expected_status:
                raise ValueError("execution status contradicts its worker exit or observation")
            if request["protocol"] != "oracle-probe-jsonl-v1":
                raise ValueError("worker request uses an unsupported observation protocol")
            output_id = evidence.get("output_artifact_id")
            if "output_artifact_id" not in evidence:
                # Older recorded executions bind output by their unique NDJSON trace.
                outputs = [identity for identity in finished["trace_ids"]
                           if replay.value["artifacts"][identity]["media_type"] == "application/x-ndjson"]
                if len(outputs) > 1:
                    raise ValueError("legacy execution has ambiguous raw output traces")
                output_id = outputs[0] if outputs else None
            expected_observation = None
            if output_id is not None:
                if output_id not in finished["trace_ids"]:
                    raise ValueError("worker output artifact is not a retained execution trace")
                output_meta = replay.value["artifacts"][output_id]
                output_bytes = (replay.directory / output_meta["path"]).read_bytes()
                if output_meta["hash_mode"] != "bytes" or sha256(output_bytes) != output_id:
                    raise ValueError("worker output artifact must preserve exact raw bytes")
                if (not evidence["timed_out"] and evidence["exit_code"] == 0
                        and evidence.get("detail") != "worker interrupted"):
                    try:
                        expected_observation = decode_jsonl(output_bytes)
                    except (ValueError, TypeError):
                        pass
            if encode_json(expected_observation) != encode_json(evidence["observation"]):
                raise ValueError("worker observation differs from retained raw output")
            input_data = artifact_json(replay, request["input_sha256"])
            # Python equality conflates booleans and numbers; source fields keep their JSON types.
            if encode_json(input_data) != encode_json(card):
                raise ValueError("exact worker input differs from its case")
            if (request["build_id"] != started["build_id"] or request["case_id"] != case_id or
                    request["worker_sha256"] != build["binary_sha256"] or
                    evidence["worker_sha256"] != build["binary_sha256"] or
                    evidence["request_id"] != started["request_id"]):
                raise ValueError("worker request, build and evidence identity differ")
            revisions.add(build["source_revision"])
            if started["change_id"] is None and build["source_revision"] != replay.value["target"]["baseline_revision"]:
                raise ValueError("baseline source revision differs from target baseline")
            runs.append({"execution_id": execution_id, "evidence_id": finished["evidence_id"],
                         "observation": evidence["observation"], "status": finished["status"]})
        if len(revisions) != 1 or len(declarations) != 1 or len(repeated_builds) != 1:
            raise ValueError("repeated executions must use the same source and declared pin revisions")
        expected = evaluate_runs(case_id, card, runs, next(iter(revisions)), cfg, next(iter(declarations)))
        recorded = artifact_json(replay, feedback["feedback_id"])
        if expected != recorded or expected["result"] != feedback["result"]:
            raise ValueError("feedback does not match independently recomputed evidence")
    return starts


def propose(args):
    with Replay(args.run_dir) as replay:
        cfg = config(replay)
        verify_domain(replay, cfg)
        motivating = [f["feedback_id"] for f in strong_feedbacks(replay)
                      if f["result"] == "violated"]
        if not motivating:
            raise ValueError("no confirmed failure motivates this change")
        patch = args.patch.read_bytes()
        if not patch or b"diff --git " not in patch:
            raise ValueError("change must be an actual nonempty Git patch")
        change_id = replay.artifact(patch, raw=True, media_type="text/x-diff")
        if any(e["payload"]["kind"] == "change_proposed" and e["payload"]["change_id"] == change_id
               for e in replay.value["events"]):
            raise ValueError("this exact change has already been proposed")
        replay.event("changes", "change_proposed", validation_runtime=args.runtime, change_id=change_id,
                     description=args.description, base_revision=replay.value["target"]["baseline_revision"],
                     motivating_feedback_ids=motivating)
        subprocess.run([str(args.runtime), "verify", str(replay.directory)], check=True)
        print(json.dumps({"change_id": change_id}))


def decision_inputs(replay, cfg, change_id):
    starts = verify_domain(replay, cfg)
    plan = artifact_json(replay, cfg["plan_id"])
    by_case = {}
    baselines = []
    for feedback in strong_feedbacks(replay):
        changes = {starts[x]["change_id"] for x in feedback["execution_ids"]}
        if changes == {change_id}:
            if feedback["case_id"] in by_case:
                raise ValueError("ambiguous candidate feedback for a frozen case")
            by_case[feedback["case_id"]] = feedback
        elif changes == {None} and feedback["case_id"] == plan["case_id"]:
            baselines.append(feedback)
    if len(baselines) != 1:
        raise ValueError("exactly one measured baseline feedback is required")
    required = [plan["case_id"], *plan["regression_case_ids"], *plan["holdout_case_ids"]]
    candidate_builds = {starts[execution_id]["build_id"] for case_id in required if case_id in by_case
                        for execution_id in by_case[case_id]["execution_ids"]}
    if len(candidate_builds) != 1:
        raise ValueError("all frozen candidate gates must use one identical build")
    failures = [case_id for case_id in required if case_id not in by_case or by_case[case_id]["result"] != "satisfied"]
    if failures or baselines[0]["result"] != "violated":
        raise ValueError("frozen acceptance requirements failed: " + str(failures))
    return plan, baselines[0], by_case[plan["case_id"]], [by_case[x]["feedback_id"] for x in required[1:]]


def record_review(args):
    if not args.reviewer.strip() or not args.rationale.strip():
        raise ValueError("independent review requires a named reviewer and a substantive rationale")
    with Replay(args.run_dir) as replay:
        cfg = config(replay)
        _, baseline, candidate, _ = decision_inputs(replay, cfg, args.change_id)
        report_bytes = args.report.read_bytes()
        if not report_bytes.strip():
            raise ValueError("independent review must contain its findings and validation")
        report_id = replay.artifact(report_bytes, raw=True, media_type="text/plain")
        review = {"plan_id": cfg["plan_id"], "baseline_receipt_id": baseline["feedback_id"],
                  "candidate_receipt_id": candidate["feedback_id"], "reviewer": args.reviewer,
                  "rationale": args.rationale + " Full independent review artifact: " + report_id,
                  "decision": args.decision}
        review_id = replay.artifact(review)
        replay.event("review", "review_recorded", validation_runtime=args.runtime, review_id=review_id, review=review)
        subprocess.run([str(args.runtime), "verify", str(replay.directory)], check=True)
        print(json.dumps({"review_id": review_id, "report_id": report_id}))


def decide(args):
    with Replay(args.run_dir) as replay:
        cfg = config(replay)
        verify_domain(replay, cfg)
        changes = [e["payload"]["change_id"] for e in replay.value["events"]
                   if e["payload"]["kind"] == "change_proposed"]
        if args.change_id not in changes:
            raise ValueError("decision requires a recorded proposed change")
        if any(e["payload"]["kind"] == "decision_recorded" and
               e["payload"]["change_id"] == args.change_id for e in replay.value["events"]):
            raise ValueError("this change already has an immutable decision")
        try:
            _, baseline, candidate, gates = decision_inputs(replay, cfg, args.change_id)
        except ValueError as error:
            decision = {"kind": "rejected", "reasons": ["Frozen acceptance requirements were not satisfied: " + str(error)]}
        else:
            reviews = [e["payload"] for e in replay.value["events"]
                       if e["payload"]["kind"] == "review_recorded"
                       and e["payload"]["review_id"] == args.review_id]
            if len(reviews) != 1:
                raise ValueError("passing gates still require a recorded independent review")
            review = reviews[0]["review"]
            if (review["plan_id"] != cfg["plan_id"] or
                    review["baseline_receipt_id"] != baseline["feedback_id"] or
                    review["candidate_receipt_id"] != candidate["feedback_id"] or
                    not review["reviewer"].strip() or not review["rationale"].strip()):
                raise ValueError("review does not bind this exact plan and before/after evidence")
            if review["decision"] == "reject":
                decision = {"kind": "rejected", "reasons": ["Independent review rejected this change: " + review["rationale"]]}
            else:
                decision = {"kind": "accepted", "plan_id": cfg["plan_id"],
                            "baseline_receipt_id": baseline["feedback_id"],
                            "candidate_receipt_id": candidate["feedback_id"],
                            "gate_receipt_ids": gates, "review_id": args.review_id}
        decision_id = replay.artifact(decision)
        attestation = {"policy_id": cfg["policy_id"], "scope": CLAIM, "decision_id": decision_id,
                       "plan_id": cfg["plan_id"], "change_id": args.change_id}
        attestation_id = replay.artifact(attestation)
        replay.event("decisions", "decision_recorded", validation_runtime=args.runtime,
                     policy={"kind": "external", "policy_id": cfg["policy_id"], "scope": CLAIM,
                             "attestation_id": attestation_id},
                     decision_id=decision_id, change_id=args.change_id, plan_id=cfg["plan_id"], decision=decision)
        if decision["kind"] != "rejected" or not getattr(args, "continue_on_rejection", False):
            replay.finish()
        print(json.dumps({"decision_id": decision_id, "result": decision["kind"], "scope": CLAIM}))


def verify_run(args):
    subprocess.run([str(args.runtime), "verify", str(args.run_dir)], check=True)
    # A read-only view avoids acquiring a writer lock or reopening a terminal run.
    replay = object.__new__(Replay)
    replay.directory = args.run_dir.resolve()
    replay.value = read_json(replay.directory / "replay.json")
    cfg = config(replay)
    verify_domain(replay, cfg)
    for event in replay.value["events"]:
        if event["payload"]["kind"] == "decision_recorded":
            payload = event["payload"]
            if (payload["policy"]["policy_id"] != cfg["policy_id"] or
                    payload["policy"]["scope"] != CLAIM or payload["plan_id"] != cfg["plan_id"]):
                raise ValueError("decision does not use the run's frozen domain policy and plan")
            if payload["decision"]["kind"] == "accepted":
                _, baseline, candidate, gates = decision_inputs(replay, cfg, payload["change_id"])
                decision = payload["decision"]
                if (decision["plan_id"] != cfg["plan_id"] or
                        decision["baseline_receipt_id"] != baseline["feedback_id"] or
                        decision["candidate_receipt_id"] != candidate["feedback_id"] or
                        decision["gate_receipt_ids"] != gates):
                    raise ValueError("decision does not match recomputed target and gate feedback")
    print("Recomputed the installed source-aligned classification policy from recorded inputs and observations.")

def attest_case_build(args):
    """Adapt the existing independently checked build receipt without replacing it."""
    build_dir = args.build_dir.resolve()
    worker = build_dir / "worker"
    subprocess.run([str(worker), "case", "build-check", "--build", str(build_dir)], check=True)
    original_bytes = (build_dir / "build.json").read_bytes()
    original = json.loads(original_bytes)
    if sha256(worker.read_bytes()) != original["binary_sha256"]:
        raise ValueError("retained worker differs from the checked build receipt")
    source = (build_dir / "source/crates/phase-bridge/src/lib.rs").read_text()
    match = re.search(r'pub const PHASE_REVISION: &str = "([0-9a-f]{40})";', source)
    if not match:
        raise ValueError("build snapshot does not declare its Phase pin")
    phase = original["phase"]
    revision = phase["revision"]
    if phase["kind"] == "checkout" and not phase["worktree_clean"]:
        revision += "+patch:" + phase["patch_sha256"]
    record = {"kind": "coworld-oracle-probe-build-v1",
              "phase_revision": revision, "declared_phase_revision": match.group(1),
              "harness_revision": original["harness_revision"],
              "binary_sha256": original["binary_sha256"],
              "source_files": original["harness_source_files"],
              "command": original["command"], "environment": original["build_environment"],
              "compiler": original["compiler"],
              "original_build_sha256": sha256(original_bytes), "original_build": original}
    if phase["kind"] == "checkout":
        record.update(phase_base_revision=phase["base_revision"],
                      phase_patch_sha256=phase["patch_sha256"],
                      phase_source_files=phase["source_files"])
    with args.output.open("xb") as destination:
        destination.write(canonical(record) + b"\n")
    print(json.dumps({"attestation": str(args.output), "phase_revision": revision,
                      "declared_phase_revision": match.group(1)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    for name in ["snapshot-dir", "discovery-dir", "plan-dir", "output-dir", "runtime"]:
        prep.add_argument("--" + name, type=Path, required=True)
    prep.add_argument("--run-id", required=True)
    prep.add_argument("--title", default="Scryfall: mana abilities and library movement")
    prep.add_argument("--baseline-revision", required=True)
    run = commands.add_parser("execute")
    for name in ["run-dir", "runtime", "worker", "build-attestation"]:
        run.add_argument("--" + name, type=Path, required=True)
    run.add_argument("--phase", choices=["baseline", "candidate"], required=True)
    run.add_argument("--phase-revision", required=True)
    run.add_argument("--change-id")
    attestation = commands.add_parser("attest-build")
    attestation.add_argument("--build-dir", type=Path, required=True)
    attestation.add_argument("--output", type=Path, required=True)
    change = commands.add_parser("propose")
    change.add_argument("--patch", type=Path, required=True)
    change.add_argument("--description", required=True)
    review = commands.add_parser("review")
    review.add_argument("--report", type=Path, required=True)
    review.add_argument("--reviewer", required=True)
    review.add_argument("--rationale", required=True)
    review.add_argument("--decision", choices=["approve", "reject"], required=True)
    decision = commands.add_parser("decide")
    decision.add_argument("--review-id")
    decision.add_argument("--continue-on-rejection", action="store_true",
                          help="Keep a rejected run open for a distinct patch under the same frozen plan")
    verify = commands.add_parser("verify")
    for command in [change, review, decision, verify]:
        command.add_argument("--run-dir", type=Path, required=True)
        command.add_argument("--runtime", type=Path, required=True)
    for command in [review, decision]:
        command.add_argument("--change-id", required=True)
    args = parser.parse_args()
    {"prepare": prepare, "execute": execute, "propose": propose, "review": record_review,
     "decide": decide, "verify": verify_run, "attest-build": attest_case_build}[args.command](args)


if __name__ == "__main__":
    main()
