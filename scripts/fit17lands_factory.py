#!/usr/bin/env python3
"""Run recorded-game discovery and attribute later changes to its retained issues.

This adapter nominates issues; it does not certify MTG rules or automatically
accept patches. FactoryReplay owns execution, provenance and lifecycle.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

from factory_replay import Replay, canonical, encode_json, sha256
from seventeenlands_coverage import strict_json, csv_records
from seventeenlands_factory import artifact_bytes, artifact_json, payloads

PROGRAM = "coworld-mtg-harness/fit17lands"
REPOSITORY = "https://github.com/Metta-AI/coworld-mtg.git"
CONFIG = "17Lands trajectory discovery configuration"
REPORT = "17Lands trajectory discovery report"
COMPARISON = "17Lands trajectory discovery comparison"
PROPOSAL = "17Lands trajectory repair attribution"
VERIFIER_UPDATE = "17Lands compatible verification update"
# This published predecessor has identical decoding, report and issue-identity
# semantics. The reader upgrade adds rejection of invalid provenance only.
COMPATIBLE_RECORDING_ADAPTERS = {
    "42ac3393c467f165896de7d2bac46de08662cdc8c4ecd1ecbb641e259995ca2f",
}
SCHEMA = "coworld/17lands-discovery-report@1"
COMPARISON_SCHEMA = "coworld/17lands-discovery-comparison@1"
CLAIM = ("Report whether a legal trajectory was found for the enforced observations under the recorded "
         "reconstruction and bounds. Missing coverage, failure and exhausted search remain issue candidates.")
FIT_STATUSES = {"input_issue", "matched_supported_projection", "budget_exhausted",
                "unsupported_boundary", "no_witness_under_assumptions"}
COMPONENTS = {
    "input_mapping": "identity", "runtime_identity_gap": "identity",
    "unsupported_input": "reconstruction", "runtime_setup": "reconstruction",
    "unsupported_projection": "observation_adapter", "projection_contradiction": "observation_adapter",
    "unsupported_boundary": "observation_adapter", "budget_exhausted": "search",
    "no_witness_under_assumptions": "investigation", "offered_action_failure": "engine",
    "invariant_failure": "engine", "worker_execution": "execution",
}
LIMITATIONS = [
    "Observational discovery supplies candidates for investigation, not automatic rules diagnoses.",
    "Named-card projection and one reconstructed hidden setup do not establish full game compatibility.",
    "A disappearing issue can reflect changed observation semantics, search or reconstruction; review those changes.",
    "Build provenance is caller-attested. Hashes bind recorded bytes, not independent compilation.",
]


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    return strict_json(Path(path).read_bytes())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def source(replay, identity, provider, description, url="urn:coworld:17lands-guided-fitting", when=None):
    replay.event("sources", "source_imported", source={
        "snapshot_id": identity, "provider": provider, "url": url,
        "retrieved_at": when or now(), "description": description + " Timestamp records import into this run; upstream acquisition time is recorded separately when known."})


def sources(replay, provider):
    return [p["source"]["snapshot_id"] for p in payloads(replay, "source_imported")
            if p["source"]["provider"] == provider]


def configuration(replay):
    ids = sources(replay, CONFIG)
    require(len(ids) == 1, "exactly one discovery configuration is required")
    cfg = artifact_json(replay, ids[0])
    installed_id = sha256(Path(__file__).read_bytes())
    require(cfg["adapter_id"] == installed_id or cfg["adapter_id"] in COMPATIBLE_RECORDING_ADAPTERS,
            "unknown recording adapter; no compatible reader is declared")
    retained_adapter = artifact_bytes(replay, cfg["adapter_id"])
    require(sha256(retained_adapter) == cfg["adapter_id"], "frozen adapter bytes differ")
    require(replay.value["target"]["name"] == PROGRAM, "wrong target program")
    require(cfg["recorder_id"] == sha256(Path(__file__).with_name("factory_replay.py").read_bytes()),
            "installed recorder differs from frozen source")
    return cfg


def record_verifier_update(replay, cfg):
    current = Path(__file__).read_bytes()
    current_id = sha256(current)
    if cfg["adapter_id"] == current_id:
        return
    for identity in sources(replay, VERIFIER_UPDATE):
        if artifact_json(replay, identity).get("verification_source_id") == current_id:
            return
    source_id = replay.artifact(current, raw=True, media_type="text/x-python")
    update = {"schema": "coworld/17lands-verifier-update@1",
              "recording_adapter_id": cfg["adapter_id"], "verification_source_id": source_id,
              "compatibility": "Identical decoding, report derivation and diagnostic identities; stricter offline provenance checks. Original baseline receipts remain unchanged.",
              "active_execution_adapter_id": source_id}
    source(replay, replay.artifact(update), VERIFIER_UPDATE,
           "Explicit recording-reader upgrade before further actions; the active adapter source and original derivation source are both retained.")


def safe_member(directory, name):
    path = directory / name
    require(not path.is_symlink() and path.resolve().is_relative_to(directory.resolve()),
            "cohort members must be regular files inside the cohort directory")
    require(path.is_file(), "missing cohort member: " + name)
    return path


def prepare(args):
    cohort_path = args.cohort.resolve()
    cohort = read_json(cohort_path)
    require(cohort["schema"] == "coworld/17lands-cohort@1", "unsupported cohort schema")
    require(re.fullmatch("[0-9a-f]{40}", args.baseline_revision), "baseline must be a full commit")
    data = safe_member(cohort_path.parent, cohort["replay"]["path"]).read_bytes()
    mapping = safe_member(cohort_path.parent, cohort["mapping"]["path"]).read_bytes()
    require(sha256(data) == cohort["replay"]["sha256"], "cohort source hash mismatch")
    require(sha256(mapping) == cohort["mapping"]["sha256"], "cohort mapping hash mismatch")
    _, records, raw_records = csv_records(data)
    cases = cohort["cases"]
    require(cases and len({c["game_index"] for c in cases}) == len(cases), "cohort cases must be nonempty and unique")
    require(all(type(c["game_index"]) is int and 0 <= c["game_index"] < len(records) for c in cases),
            "cohort game indexes must name retained records")
    if "rows" in cohort["replay"]:
        require(cohort["replay"]["rows"] == len(records), "declared source row count differs")
    if "count" in cohort["selection"]:
        require(cohort["selection"]["count"] == len(cases), "declared selection count differs")
    for selected in cases:
        if "source_row_sha256" in selected:
            require(selected["source_row_sha256"] == sha256(raw_records[selected["game_index"] + 1]),
                    "selected raw source record identity differs")
    manifest_bytes = args.input_manifest.read_bytes()
    manifest = strict_json(manifest_bytes)
    scope = {**cohort["fit"], "deadline_seconds": args.deadline_seconds, "memory_bytes": args.memory_bytes}
    for key in ("turn_pairs", "nodes", "max_actions", "deadline_seconds", "memory_bytes"):
        require(type(scope[key]) is int and scope[key] > 0, "positive integer scope limit required: " + key)
    require(scope["max_actions"] <= 512, "max_actions exceeds fitter limit")
    with Replay.create(args.runtime, args.run_dir, args.run_id, args.title,
                       PROGRAM, REPOSITORY, args.baseline_revision) as replay:
        cohort_id = replay.artifact(cohort_path.read_bytes(), raw=True)
        data_id = replay.artifact(data, raw=True, media_type="text/csv")
        mapping_id = replay.artifact(mapping, raw=True, media_type="text/csv")
        source(replay, cohort_id, "17Lands frozen trajectory cohort",
               json.dumps(cohort["source"]["attribution"], ensure_ascii=False) + " " + json.dumps(cohort["selection"]),
               cohort["source"]["url"])
        source(replay, data_id, "17Lands exact public game records",
               "Exact source header and records; the cohort receipt retains original row numbers and byte offsets.",
               cohort["source"]["url"])
        source(replay, mapping_id, "17Lands official card identity mapping",
               "Official mapping bytes used by each worker. Names do not prove complete face or effect support.")
        adapter_id = replay.artifact(Path(__file__).read_bytes(), raw=True, media_type="text/x-python")
        recorder_id = replay.artifact(Path(__file__).with_name("factory_replay.py").read_bytes(),
                                      raw=True, media_type="text/x-python")
        runtime_manifest_artifact_id = replay.artifact(manifest_bytes, raw=True)
        source(replay, runtime_manifest_artifact_id, "Pinned runtime input manifest",
               "Exact native runtime input manifest; corpus bytes stay external. Its validation counters are not discovery measurements.")
        registered = []
        for selected in cases:
            spec = {"schema": "coworld/17lands-fit-case@1", "cohort_id": cohort_id,
                    "source_id": data_id, "mapping_id": mapping_id, "selection": selected,
                    "scope": scope}
            case_id = replay.artifact(spec)
            row = selected["source_row_index"]
            title = f"17Lands source row {row}"
            replay.event("cases", "case_registered", case_id=case_id, title=title,
                         derivation={"kind": "source_derived", "source_ids": [cohort_id, data_id, mapping_id],
                                     "source_records": [{"source_id": data_id, "record_id": f"game-index:{selected['game_index']}"}],
                                     "recipe": "Frozen source selection without filtering on fitting results. " +
                                               json.dumps(cohort["selection"], sort_keys=True),
                                     "seed": selected["game_index"]})
            registered.append({"case_id": case_id, "title": title, **selected})
            # The factory case identity is the entire frozen specification, not a source-only label.
            registered[-1]["case_id"] = case_id
        cfg = {"schema": "coworld/17lands-discovery-config@1", "cohort_id": cohort_id,
               "data_id": data_id, "mapping_id": mapping_id, "adapter_id": adapter_id,
               "recorder_id": recorder_id, "cases": registered, "scope": scope,
                "runtime_manifest_sha256": sha256(manifest_bytes), "runtime_manifest_id": manifest["manifest_id"],
               "runtime_manifest_artifact_id": runtime_manifest_artifact_id,
               "runtime_phase_revision": manifest["phase_revision"],
               "limitations": LIMITATIONS}
        source(replay, replay.artifact(cfg), CONFIG, "Frozen source cases, scope and discovery recording code.")
        verify_domain(replay)
        native_verify(args, replay.directory)
        print(json.dumps({"run_dir": str(replay.directory), "cohort_id": cohort_id, "cases": len(cases)}))


def decode_result(raw):
    result = strict_json(raw)
    require(result.get("schema") == "coworld-17lands-guided-fit-v1", "unsupported native fitting result")
    require(result.get("status") in FIT_STATUSES, "unknown native fitting status")
    require(isinstance(result.get("issues"), list), "native issues must be a list")
    return result


def classify(result):
    return ("completed" if result["status"] == "matched_supported_projection" else "inconclusive", None)


def coverage(constraints):
    fields = constraints.get("fields", []) if constraints else []
    return {kind: sorted(f["column"] for f in fields if f["disposition"] == kind and f.get("milestone"))
            for kind in ("enforced", "unsupported", "informational")}


def issues_for(result, detail=None):
    if result is None:
        return [{"kind": "worker_execution", "detail": detail or "No valid native receipt.",
                 "source_columns": [], "evidence": None}]
    return result["issues"]


def issue_identity(issue):
    # Group only a repeatable diagnostic signature. All raw occurrences survive.
    # Engine/search evidence remains in origins; this key is triage, not a shared root-cause proof.
    columns = sorted(set(re.sub(r"^(user|oppo)_turn_[0-9]+_", "", c)
                         for c in issue["source_columns"]))
    signature = {"kind": issue["kind"], "columns": columns, "detail": issue["detail"]}
    return sha256(canonical(signature))


def outcome(replay, cfg, case, start, finish):
    evidence = artifact_json(replay, finish["evidence_id"])
    request = artifact_json(replay, start["request_id"])
    expected_record = {"case_id": case["case_id"], "game_index": case["game_index"],
                       "cohort_id": cfg["cohort_id"], "scope": cfg["scope"],
                       "runtime_manifest_sha256": cfg["runtime_manifest_sha256"]}
    require(encode_json(strict_json(artifact_bytes(replay, request["input_sha256"]))) == encode_json(expected_record),
            "worker request input differs from frozen case")
    require(evidence["request_id"] == start["request_id"], "execution evidence request mismatch")
    require(request["case_id"] == case["case_id"] and request["build_id"] == start["build_id"],
            "request case/build binding differs")
    builds = [p["build"] for p in payloads(replay, "build_recorded") if p["build_id"] == start["build_id"]]
    require(len(builds) == 1, "execution build missing or ambiguous")
    require(request["worker_sha256"] == evidence["worker_sha256"] == builds[0]["binary_sha256"],
            "worker binary identity mismatch")
    build = builds[0]
    attestation_link = artifact_json(replay, build["attestation_id"])
    attestation = artifact_json(replay, attestation_link["original_receipt_id"])
    require(attestation["schema"] == "coworld-guided-fit-build-v1"
            and attestation["source_revision"] == build["source_revision"]
            and attestation["worker_sha256"] == build["binary_sha256"]
            and attestation["exit_code"] == 0
            and attestation["source_files_before"] == attestation["source_files_after"],
            "build attestation binding differs")
    scope = cfg["scope"]
    require(request["deadline_seconds"] == scope["deadline_seconds"] and request["memory_bytes"] == scope["memory_bytes"],
            "supervision bounds differ from frozen scope")
    require(request["protocol"] == "17lands-fit-files-v1" and request.get("output_name") == "result.json"
            and request.get("companion_names") == ["constraints.json"], "native file protocol differs")
    command = request["command"]
    flags = {"--replay-sha256": cfg["data_id"], "--cards-csv-sha256": cfg["mapping_id"],
             "--game-index": str(case["game_index"]), "--turn-pairs": str(scope["turn_pairs"]),
             "--nodes": str(scope["nodes"]), "--max-actions": str(scope["max_actions"]),
             "--opponent-filler": scope["opponent_filler"]}
    require(len(command) > 1 and command[1] == "fit17lands", "wrong native command")
    for flag, value in flags.items():
        require(command.count(flag) == 1 and command.index(flag) + 1 < len(command)
                and command[command.index(flag) + 1] == value, "command differs from scope: " + flag)
    result_id = evidence["output_artifact_id"]
    constraints_id = evidence.get("companion_artifact_ids", {}).get("constraints.json")
    constraints = artifact_json(replay, constraints_id) if constraints_id else None
    result = None
    process_ok = evidence["exit_code"] == 0 and evidence["timed_out"] is False and not evidence.get("companion_errors")
    if process_ok and result_id and evidence["observation"] is not None:
        result = decode_result(artifact_bytes(replay, result_id))
        require(encode_json(result) == encode_json(evidence["observation"]), "decoded result differs from raw worker bytes")
        require(constraints is not None, "successful worker missing constraints")
        require(result["input_sha256"] == sha256(canonical(constraints)), "result does not bind exact constraints")
        require(result["source_sha256"] == constraints["source_sha256"] == cfg["data_id"],
                "native source identity mismatch")
        require(result["cards_mapping_sha256"] == constraints["cards_mapping_sha256"] == cfg["mapping_id"],
                "native mapping identity mismatch")
        require(result["manifest_id"] == cfg["runtime_manifest_id"], "native runtime manifest mismatch")
        require(result["phase_revision"] == cfg["runtime_phase_revision"], "native Phase revision differs")
        require(result["seed"] == constraints["seed"] == constraints["game_index"] == case["game_index"],
                "native seed/game identity mismatch")
        require(result["limits"] == {"nodes": scope["nodes"], "max_actions": scope["max_actions"]},
                "native search limits differ")
        require(type(result["nodes"]) is int and result["nodes"] <= scope["nodes"], "invalid native search usage")
        require(finish["status"] == classify(result)[0], "native execution classification differs")
    else:
        require(finish["status"] in ("error", "cancelled") and evidence["observation"] is None,
                "failed execution cannot become a valid observation")
    status = result["status"] if result else "worker_execution"
    discovered = issues_for(result, evidence.get("detail"))
    for issue in discovered:
        require(issue["kind"] in COMPONENTS, "unrecognized issue kind")
    receipt = {"schema": "coworld/17lands-discovery-feedback@1", "case_id": case["case_id"],
               "execution_id": start["execution_id"], "evidence_id": finish["evidence_id"],
               "constraints_id": constraints_id, "result_id": result_id, "status": status,
               "coverage": coverage(constraints), "issue_ids": sorted({issue_identity(i) for i in discovered}),
               "result": "satisfied" if status == "matched_supported_projection" else "inconclusive",
               "claim": CLAIM}
    return receipt, discovered


def report_value(replay, cfg, label, build_id, change_id, rows):
    issues = {}
    status_counts = Counter()
    for case, receipt, discovered in rows:
        status_counts[receipt["status"]] += 1
        for issue in discovered:
            identity = issue_identity(issue)
            item = issues.setdefault(identity, {"issue_id": identity, "kind": issue["kind"],
                                               "component": COMPONENTS[issue["kind"]],
                                               "title": issue["detail"], "origins": []})
            item["origins"].append({
                "case_id": case["case_id"], "source_row_index": case["source_row_index"],
                "execution_id": receipt["execution_id"], "result_id": receipt["result_id"],
                "source_columns": issue["source_columns"], "detail": issue["detail"],
                "evidence": issue.get("evidence")})
    case_rows = [{"case_id": c["case_id"], "title": c["title"], "source_row_index": c["source_row_index"],
                  "execution_id": r["execution_id"], "constraints_id": r["constraints_id"],
                  "result_id": r["result_id"], "feedback_id": sha256(canonical(r)),
                  "status": r["status"], "issue_ids": r["issue_ids"], "coverage": r["coverage"]}
                 for c, r, _ in rows]
    return {"schema": SCHEMA, "cohort_id": cfg["cohort_id"], "label": label,
            "build_id": build_id, "change_id": change_id, "scope": cfg["scope"],
            "complete": len(rows) == len(cfg["cases"]), "cases": case_rows,
            "issues": sorted(issues.values(), key=lambda i: i["issue_id"]),
            "summary": {"cases": len(rows), "planned_cases": len(cfg["cases"]),
                        "status_counts": dict(sorted(status_counts.items())),
                        "issue_counts": dict(sorted(Counter(i["kind"] for i in issues.values()).items()))},
            "limitations": cfg["limitations"]}


def validate_build(attestation, binary, revision):
    require(attestation.get("schema") == "coworld-guided-fit-build-v1", "expected guided fitter build receipt")
    require(attestation["source_revision"] == revision, "build source revision differs")
    require(attestation["worker_sha256"] == sha256(binary.read_bytes()), "build does not bind this worker")
    require(attestation["exit_code"] == 0, "build did not complete")
    require(attestation["source_files_before"] == attestation["source_files_after"], "sources changed during build")
    return attestation


def execute(args):
    with Replay(args.run_dir) as replay:
        cfg = configuration(replay)
        verify_domain(replay)
        record_verifier_update(replay, cfg)
        require(sha256(args.input_manifest.read_bytes()) == cfg["runtime_manifest_sha256"],
                "runtime manifest differs from prepared run")
        attestation = read_json(args.build_attestation)
        revision = attestation["source_revision"]
        validate_build(attestation, args.worker, revision)
        if args.label == "baseline":
            require(args.change_id is None and revision == replay.value["target"]["baseline_revision"],
                    "baseline must use the declared original source")
        else:
            require(args.change_id is not None, "candidate needs a separately proposed change")
            changes = [p for p in payloads(replay, "change_proposed") if p["change_id"] == args.change_id]
            require(len(changes) == 1, "unknown proposed change")
            attrs = [artifact_json(replay, i) for i in sources(replay, PROPOSAL)
                     if artifact_json(replay, i)["change_id"] == args.change_id]
            require(len(attrs) == 1 and attrs[0]["candidate_revision"] == revision,
                    "candidate build differs from attributed source revision")
        require(not any(artifact_json(replay, i)["label"] == args.label for i in sources(replay, REPORT)),
                "label already executed; use a distinct label for another candidate or repetition")
        build_receipt_id = replay.artifact(args.build_attestation.read_bytes(), raw=True)
        build_id = replay.build(PROGRAM, revision, args.worker, attestation["command"],
                                attestation["environment"], {"original_receipt_id": build_receipt_id,
                                "boundary": "Caller-attested compilation, not independent build proof."})
        scope = cfg["scope"]
        rows = []
        data_path = replay.directory / replay.value["artifacts"][cfg["data_id"]]["path"]
        mapping_path = replay.directory / replay.value["artifacts"][cfg["mapping_id"]]["path"]
        for case in cfg["cases"]:
            execution_id = f"{args.label}-game-{case['game_index']:04d}"
            record = {"case_id": case["case_id"], "game_index": case["game_index"],
                      "cohort_id": cfg["cohort_id"], "scope": scope,
                      "runtime_manifest_sha256": cfg["runtime_manifest_sha256"]}
            def arguments(_src, dst):
                return ["fit17lands", "--manifest-uri", str(args.input_manifest.resolve()),
                        "--replay-data", str(data_path), "--replay-sha256", cfg["data_id"],
                        "--cards-csv", str(mapping_path), "--cards-csv-sha256", cfg["mapping_id"],
                        "--game-index", str(case["game_index"]), "--turn-pairs", str(scope["turn_pairs"]),
                        "--nodes", str(scope["nodes"]), "--max-actions", str(scope["max_actions"]),
                        "--opponent-filler", scope["opponent_filler"], "--output-dir", str(dst.parent)]
            replay.run_jsonl(execution_id=execution_id, case_id=case["case_id"], build_id=build_id,
                binary=args.worker, record=record, arguments=arguments, protocol="17lands-fit-files-v1",
                classify_status=classify, change_id=args.change_id, deadline_seconds=scope["deadline_seconds"],
                memory_bytes=scope["memory_bytes"], decode_output=decode_result, output_media_type="application/json",
                output_name="result.json", companion_names=("constraints.json",))
            start = next(p for p in payloads(replay, "execution_started") if p["execution_id"] == execution_id)
            finish = next(p for p in payloads(replay, "execution_finished") if p["execution_id"] == execution_id)
            receipt, discovered = outcome(replay, cfg, case, start, finish)
            replay.feedback(case["case_id"], [execution_id], receipt,
                evaluator="17Lands bounded trajectory discovery", evaluator_version=cfg["adapter_id"],
                strength="weak", method="Replay source-derived milestones through legal engine actions",
                claim=CLAIM, result=receipt["result"], summary=receipt["status"])
            rows.append((case, receipt, discovered))
            report = report_value(replay, cfg, args.label, build_id, args.change_id, rows)
            report_id = replay.artifact(report)
            source(replay, report_id, REPORT, "Derived case outcomes and issue origins from recorded native executions.")
            print(json.dumps({"execution": execution_id, "status": receipt["status"],
                              "issues": len(discovered), "report_id": report_id}), flush=True)
        verify_domain(replay)
        native_verify(args, replay.directory)


def all_reports(replay):
    return [(identity, artifact_json(replay, identity)) for identity in sources(replay, REPORT)]


def complete_report(replay, identity):
    require(identity in sources(replay, REPORT), "report is not recorded in this run")
    report = artifact_json(replay, identity)
    require(report["complete"], "comparison/proposal requires a complete cohort")
    return report


def propose(args):
    with Replay(args.run_dir) as replay:
        cfg = configuration(replay)
        verify_domain(replay)
        record_verifier_update(replay, cfg)
        report = complete_report(replay, args.report_id)
        require(report["label"] == "baseline", "repair attribution must start from baseline discovery")
        known = {i["issue_id"]: i for i in report["issues"]}
        require(args.issue_id and all(i in known for i in args.issue_id), "select actual discovered issue IDs")
        patch = args.patch.read_bytes()
        require(patch and b"diff --git " in patch, "provide a nonempty Git patch")
        require(re.fullmatch("[0-9a-f]{40}", args.candidate_revision), "candidate must be a full commit")
        actual_patch = subprocess.check_output(["git", "-C", str(args.candidate_repository),
            "diff", "--binary", "--full-index", replay.value["target"]["baseline_revision"],
            args.candidate_revision, "--"])
        require(patch == actual_patch, "patch differs from exact baseline-to-candidate commit diff")
        identity = replay.artifact(patch, raw=True, media_type="text/x-diff")
        require(not any(p["change_id"] == identity for p in payloads(replay, "change_proposed")),
                "this patch is already proposed")
        case_ids = {o["case_id"] for i in args.issue_id for o in known[i]["origins"]}
        feedback_ids = [c["feedback_id"] for c in report["cases"] if c["case_id"] in case_ids]
        replay.event("changes", "change_proposed", change_id=identity, description=args.description,
                     base_revision=replay.value["target"]["baseline_revision"], motivating_feedback_ids=feedback_ids)
        diagnosis_id = replay.artifact(args.diagnosis.read_bytes(), raw=True, media_type="text/markdown")
        attribution = {"schema": "coworld/17lands-repair-attribution@1", "change_id": identity,
                       "baseline_report_id": args.report_id, "origin_issue_ids": sorted(set(args.issue_id)),
                       "origin_case_ids": sorted(case_ids), "diagnosis_id": diagnosis_id,
                       "component": args.component, "candidate_revision": args.candidate_revision,
                       "authority": "Operator-supplied diagnosis and patch; discovery alone does not prove this diagnosis."}
        source(replay, replay.artifact(attribution), PROPOSAL, "Issue-to-patch attribution with a separate diagnosis.")
        verify_domain(replay)
        native_verify(args, replay.directory)
        print(json.dumps({"change_id": identity}))


def comparison_value(replay, cfg, before_id, after_id, change_id):
    before, after = complete_report(replay, before_id), complete_report(replay, after_id)
    require(before["label"] == "baseline" and after["change_id"] == change_id,
            "comparison requires baseline and candidate for the proposed change")
    require(before["cohort_id"] == after["cohort_id"] and before["scope"] == after["scope"],
            "cohort and declared search limits differ")
    attrs = [artifact_json(replay, i) for i in sources(replay, PROPOSAL)
             if artifact_json(replay, i)["change_id"] == change_id]
    require(len(attrs) == 1 and attrs[0]["baseline_report_id"] == before_id, "repair attribution mismatch")
    rows, scope_changes = [], []
    for first, second in zip(before["cases"], after["cases"], strict=True):
        require(first["case_id"] == second["case_id"], "comparison case order differs")
        a, b = set(first["issue_ids"]), set(second["issue_ids"])
        rows.append({"case_id": first["case_id"], "before_status": first["status"],
                     "after_status": second["status"], "resolved_issue_ids": sorted(a - b),
                     "remaining_issue_ids": sorted(a & b), "new_issue_ids": sorted(b - a),
                     "coverage_before": first["coverage"], "coverage_after": second["coverage"]})
        old = artifact_json(replay, first["constraints_id"]) if first["constraints_id"] else None
        new = artifact_json(replay, second["constraints_id"]) if second["constraints_id"] else None
        if old is not None and new is not None:
            old_fields = {f["column"]: f for f in old["fields"]}
            new_fields = {f["column"]: f for f in new["fields"]}
            for column in sorted(set(old_fields) | set(new_fields)):
                f, g = old_fields.get(column), new_fields.get(column)
                if f != g:
                    scope_changes.append({"case_id": first["case_id"], "kind": "observation_changed",
                                          "column": column, "before": f, "after": g})
            for key in ("assumptions", "decks", "libraries", "milestones"):
                if old.get(key) != new.get(key):
                    scope_changes.append({"case_id": first["case_id"], "kind": "reconstruction_changed",
                                          "field": key, "before": old.get(key), "after": new.get(key)})
        elif old is not new:
            scope_changes.append({"case_id": first["case_id"], "kind": "constraints_availability_changed"})
    return {"schema": COMPARISON_SCHEMA, "baseline_report_id": before_id, "candidate_report_id": after_id,
            "change_id": change_id, "origin_issue_ids": attrs[0]["origin_issue_ids"],
            "rows": rows, "assessment": "comparison_only", "scope_changes": scope_changes,
            "limitations": LIMITATIONS + ["Resolved means this diagnostic signature was absent from the rerun; it does not mean a reviewed fix."]}


def compare(args):
    with Replay(args.run_dir) as replay:
        cfg = configuration(replay)
        verify_domain(replay)
        value = comparison_value(replay, cfg, args.baseline_report_id, args.candidate_report_id, args.change_id)
        identity = replay.artifact(value)
        source(replay, identity, COMPARISON, "Mechanical before/after comparison; no automatic acceptance decision.")
        native_verify(args, replay.directory)
        print(json.dumps({"comparison_id": identity, "assessment": value["assessment"]}))


def validate_attributions(replay):
    changes = {p["change_id"]: p for p in payloads(replay, "change_proposed")}
    attributes = {}
    for identity in sources(replay, PROPOSAL):
        a = artifact_json(replay, identity)
        require(a.get("schema") == "coworld/17lands-repair-attribution@1", "unsupported repair attribution schema")
        change_id = a["change_id"]
        require(change_id in changes and change_id not in attributes, "attribution needs one unique proposed change")
        before = complete_report(replay, a["baseline_report_id"])
        require(before["label"] == "baseline" and before["change_id"] is None, "origins must come from baseline discovery")
        known = {i["issue_id"]: i for i in before["issues"]}
        ids = a["origin_issue_ids"]
        require(isinstance(ids, list) and ids and ids == sorted(set(ids)) and all(i in known for i in ids),
                "repair attribution names unknown or duplicate origin issues")
        origins = sorted({o["case_id"] for i in ids for o in known[i]["origins"]})
        require(a["origin_case_ids"] == origins, "repair attribution origin cases differ from actual issues")
        feedbacks = [c["feedback_id"] for c in before["cases"] if c["case_id"] in origins]
        change = changes[change_id]
        require(change["motivating_feedback_ids"] == feedbacks,
                "proposed change motivation differs from its discovered origins")
        require(change["base_revision"] == replay.value["target"]["baseline_revision"],
                "proposed change baseline revision differs")
        require(re.fullmatch("[0-9a-f]{40}", a["candidate_revision"]), "attribution candidate revision must be a full commit")
        require(a["component"] in COMPONENTS.values(), "unsupported attributed component")
        require(bool(artifact_bytes(replay, a["diagnosis_id"])), "attribution diagnosis must exist and be nonempty")
        require(b"diff --git " in artifact_bytes(replay, change_id), "attributed patch is not a Git diff")
        attributes[change_id] = a
    require(set(changes) == set(attributes), "every proposed change requires its source issue attribution")
    return attributes


def verify_domain(replay):
    cfg = configuration(replay)
    cases = {c["case_id"]: c for c in cfg["cases"]}
    feedbacks = {f["feedback"]["feedback_id"]: f["feedback"] for f in payloads(replay, "feedback_recorded")}
    starts = {p["execution_id"]: p for p in payloads(replay, "execution_started")}
    finishes = {p["execution_id"]: p for p in payloads(replay, "execution_finished")}
    attributes = validate_attributions(replay)
    builds = {p["build_id"]: p["build"] for p in payloads(replay, "build_recorded")}
    for identity in sources(replay, VERIFIER_UPDATE):
        update = artifact_json(replay, identity)
        require(update.get("schema") == "coworld/17lands-verifier-update@1"
                and update["recording_adapter_id"] == cfg["adapter_id"],
                "verification update differs from original recording adapter")
        require(sha256(artifact_bytes(replay, update["verification_source_id"])) == update["verification_source_id"]
                and update["active_execution_adapter_id"] == update["verification_source_id"],
                "verification source binding differs")
    # Recompute every displayed report from retained raw output and immutable cases.
    for _identity, report in all_reports(replay):
        rows = []
        build = builds[report["build_id"]]
        if report["label"] == "baseline":
            require(report["change_id"] is None and build["source_revision"] == replay.value["target"]["baseline_revision"],
                    "baseline report uses a different revision or proposed change")
        else:
            require(report["change_id"] in attributes and
                    build["source_revision"] == attributes[report["change_id"]]["candidate_revision"],
                    "candidate report revision differs from its attributed change")
        require(report["scope"] == cfg["scope"], "report scope differs")
        require([c["case_id"] for c in report["cases"]] == [c["case_id"] for c in cfg["cases"][:len(report["cases"])]],
                "report omits or reorders cohort cases")
        for row in report["cases"]:
            start, finish = starts[row["execution_id"]], finishes[row["execution_id"]]
            require(start["case_id"] == row["case_id"] and start["build_id"] == report["build_id"]
                    and start["change_id"] == report["change_id"], "report execution attribution mismatch")
            receipt, discovered = outcome(replay, cfg, cases[row["case_id"]], start, finish)
            identity = sha256(canonical(receipt))
            require(artifact_json(replay, identity) == receipt, "recorded feedback differs")
            feedback = feedbacks[identity]
            require(feedback["case_id"] == row["case_id"] and feedback["execution_ids"] == [row["execution_id"]]
                    and feedback["declared_strength"] == "weak" and feedback["bounded_claim"] == CLAIM
                    and feedback["result"] == receipt["result"] and feedback["evaluator_version"] == cfg["adapter_id"],
                    "feedback envelope overstates or changes the recorded claim")
            rows.append((cases[row["case_id"]], receipt, discovered))
        expected = report_value(replay, cfg, report["label"], report["build_id"], report["change_id"], rows)
        require(canonical(report) == canonical(expected), "derived discovery report differs from native evidence")
    for identity in sources(replay, COMPARISON):
        value = artifact_json(replay, identity)
        require(value == comparison_value(replay, cfg, value["baseline_report_id"],
                                         value["candidate_report_id"], value["change_id"]),
                "comparison differs from retained before/after evidence")
    return cfg


def native_verify(args, directory):
    subprocess.run([str(args.runtime), "verify", str(directory)], check=True)


def verify(args):
    native_verify(args, args.run_dir)
    replay = object.__new__(Replay)
    replay.directory = args.run_dir.resolve()
    replay.value = read_json(replay.directory / "replay.json")
    verify_domain(replay)
    print("Discovery reports, issue origins and comparisons recompute from retained native receipts.")


def finish(args):
    with Replay(args.run_dir) as replay:
        verify_domain(replay)
        reports = all_reports(replay)
        require(reports and reports[-1][1]["complete"], "cannot finish an incomplete cohort")
        native_verify(args, replay.directory)
        replay.finish()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--cohort", type=Path, required=True)
    prep.add_argument("--input-manifest", type=Path, required=True)
    prep.add_argument("--baseline-revision", required=True)
    prep.add_argument("--run-id", required=True)
    prep.add_argument("--title", default="17Lands: can the engine explain these games?")
    prep.add_argument("--deadline-seconds", type=int, default=240)
    prep.add_argument("--memory-bytes", type=int, default=8 * 1024**3)
    run = commands.add_parser("execute")
    run.add_argument("--label", required=True)
    run.add_argument("--change-id")
    run.add_argument("--worker", type=Path, required=True)
    run.add_argument("--build-attestation", type=Path, required=True)
    run.add_argument("--input-manifest", type=Path, required=True)
    proposal = commands.add_parser("propose")
    proposal.add_argument("--report-id", required=True)
    proposal.add_argument("--issue-id", action="append", required=True)
    proposal.add_argument("--patch", type=Path, required=True)
    proposal.add_argument("--diagnosis", type=Path, required=True)
    proposal.add_argument("--description", required=True)
    proposal.add_argument("--candidate-revision", required=True)
    proposal.add_argument("--candidate-repository", type=Path, required=True)
    proposal.add_argument("--component", choices=sorted(set(COMPONENTS.values())), required=True)
    comp = commands.add_parser("compare")
    comp.add_argument("--baseline-report-id", required=True)
    comp.add_argument("--candidate-report-id", required=True)
    comp.add_argument("--change-id", required=True)
    check = commands.add_parser("verify")
    done = commands.add_parser("finish")
    for command in (prep, run, proposal, comp, check, done):
        command.add_argument("--run-dir", type=Path, required=True)
        command.add_argument("--runtime", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "execute":
        require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", args.label), "label must be a safe short component")
    {"prepare": prepare, "execute": execute, "propose": propose,
     "compare": compare, "verify": verify, "finish": finish}[args.command](args)


if __name__ == "__main__":
    main()
