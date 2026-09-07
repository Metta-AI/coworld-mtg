#!/usr/bin/env python3
"""Record real public 17Lands miner coverage with the generic factory runtime."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone

from factory_replay import Replay, canonical, sha256, encode_json
import seventeenlands_coverage as coverage

PROGRAM = "coworld-mtg-harness/mine17lands"
REPOSITORY = "https://github.com/Metta-AI/coworld-mtg.git"
CONFIG_PROVIDER = "17Lands factory configuration"
PROTOCOL = "17lands-native-json-v1"
HASH = re.compile(r"^[0-9a-f]{64}$")
REVISION = re.compile(r"^[0-9a-f]{40}$")


def read_json(path):
    return coverage.strict_json(Path(path).read_bytes())


def source(replay, identity, provider, url, when, description):
    replay.event("sources", "source_imported", source={"snapshot_id": identity,
        "provider": provider, "url": url, "retrieved_at": when, "description": description})


def artifact_bytes(replay, identity):
    meta = replay.value["artifacts"][identity]
    path = replay.directory / meta["path"]
    if path.is_symlink() or not path.resolve().is_relative_to(replay.directory.resolve()):
        raise ValueError("unsafe artifact path")
    data = path.read_bytes()
    value = data if meta["hash_mode"] == "bytes" else canonical(coverage.strict_json(data))
    if sha256(value) != identity:
        raise ValueError("artifact content identity differs")
    return data


def artifact_json(replay, identity):
    return coverage.strict_json(artifact_bytes(replay, identity))


def payloads(replay, kind):
    return [event["payload"] for event in replay.value["events"] if event["payload"]["kind"] == kind]


def configuration(replay):
    matches = [p["source"]["snapshot_id"] for p in payloads(replay, "source_imported")
               if p["source"]["provider"] == CONFIG_PROVIDER]
    if len(matches) != 1:
        raise ValueError("exactly one immutable adapter configuration is required")
    cfg = artifact_json(replay, matches[0])
    if cfg["adapter_sha256"] != sha256(Path(__file__).read_bytes()) or artifact_bytes(replay, cfg["adapter_sha256"]) != Path(__file__).read_bytes():
        raise ValueError("installed repetition/policy adapter differs from frozen source")
    if cfg["evaluator_sha256"] != sha256(Path(coverage.__file__).read_bytes()):
        raise ValueError("installed decoder/evaluator differs from frozen source")
    if artifact_bytes(replay, cfg["evaluator_sha256"]) != Path(coverage.__file__).read_bytes():
        raise ValueError("retained evaluator source differs")
    if replay.value["target"]["name"] != PROGRAM or replay.value["target"]["repository"] != REPOSITORY:
        raise ValueError("run target is not this native importer")
    plan = artifact_json(replay, cfg["plan_id"])
    if plan != {"case_id": cfg["cases"][0]["case_id"], "regression_case_ids": [cfg["cases"][1]["case_id"]],
                "holdout_case_ids": [cfg["cases"][2]["case_id"]]}:
        raise ValueError("frozen partition roles differ from acceptance plan")
    policy = artifact_json(replay, cfg["policy_id"])
    if policy["scope"] != coverage.CLAIM or policy["evaluator_sha256"] != cfg["evaluator_sha256"] or policy["plan_id"] != cfg["plan_id"]:
        raise ValueError("policy differs from frozen evaluator or plan")
    mapping = artifact_bytes(replay, cfg["mapping_id"])
    freeze = artifact_json(replay, cfg["source_freeze_id"])
    if [case["role"] for case in cfg["cases"]] != ["primary", "regression", "holdout", "aggregate"]:
        raise ValueError("frozen partition roles changed")
    known = artifact_bytes(replay, cfg["cases"][3]["dataset_id"])
    holdout = artifact_bytes(replay, cfg["cases"][2]["dataset_id"])
    for name, data in [("known-92.csv", known), ("holdout-first-16-new.csv", holdout), ("cards.csv", mapping)]:
        if freeze["artifacts"][name] != {"sha256": sha256(data), "bytes": len(data)}:
            raise ValueError("frozen source receipt differs from retained public bytes")
    if coverage.slice_csv(known, 1, 46) != artifact_bytes(replay, cfg["cases"][0]["dataset_id"]) or coverage.slice_csv(known, 47, 92) != artifact_bytes(replay, cfg["cases"][1]["dataset_id"]):
        raise ValueError("known partitions differ from their exact source row slices")
    if len(coverage.csv_records(known)[1]) != 92 or len(coverage.csv_records(holdout)[1]) != 16:
        raise ValueError("retained source cohort row counts changed")
    for case in cfg["cases"]:
        if case["mapping_id"] != cfg["mapping_id"]:
            raise ValueError("case mapping differs from frozen official map")
        specification = artifact_json(replay, case["case_id"])
        if specification != {key: case[key] for key in ("schema", "dataset_id", "mapping_id", "role", "original_data_rows", "rows")}:
            raise ValueError("case differs from frozen partition descriptor")
        expected = coverage.source_expectation(artifact_bytes(replay, case["dataset_id"]), mapping)
        if encode_json(expected) != encode_json(artifact_json(replay, case["expectation_id"])):
            raise ValueError("source-only expectations do not recompute from frozen bytes")
    return cfg


def prepare(args):
    freeze = read_json(args.source_dir / "source-freeze.json")
    # An explicit allowlist prevents accidentally publishing nearby bootstrap files.
    files = {}
    for name in ("known-92.csv", "holdout-first-16-new.csv", "cards.csv"):
        data = (args.source_dir / name).read_bytes()
        if freeze["artifacts"][name] != {"sha256": sha256(data), "bytes": len(data)}:
            raise ValueError("frozen public source bytes changed: " + name)
        files[name] = data
    if freeze["prefix_match"].get("exact") is not True or freeze["selection"]["known_data_rows"] != [1, 92] or freeze["selection"]["holdout_data_rows"] != [93, 108]:
        raise ValueError("source receipt does not establish the declared known/new split")
    if len(coverage.csv_records(files["known-92.csv"])[1]) != 92 or len(coverage.csv_records(files["holdout-first-16-new.csv"])[1]) != 16:
        raise ValueError("frozen source row counts differ")
    if not REVISION.fullmatch(args.baseline_revision):
        raise ValueError("baseline must name a full Coworld commit")
    partitions = [("primary", [1, 46], coverage.slice_csv(files["known-92.csv"], 1, 46)),
                  ("regression", [47, 92], coverage.slice_csv(files["known-92.csv"], 47, 92)),
                  ("holdout", [93, 108], files["holdout-first-16-new.csv"]),
                  ("aggregate", [1, 92], files["known-92.csv"])]
    expectations = [coverage.source_expectation(data, files["cards.csv"]) for _, _, data in partitions]
    if any(not expected["qualified"] for expected in expectations):
        raise ValueError("source preparation is inconclusive: " + str([e["problems"] for e in expectations]))
    frozen_at = datetime.now(timezone.utc).isoformat()
    with Replay.create(args.runtime, args.output_dir, args.run_id, args.title, PROGRAM, REPOSITORY, args.baseline_revision) as replay:
        when = freeze["retrieved_at"]
        freeze_id = replay.artifact(freeze)
        source(replay, freeze_id, "17Lands public acquisition and slicing receipt", freeze["archive_url"], when,
               freeze["dataset_attribution"] + " " + freeze["modification"] + " Compressed prefix bytes are retained separately; their hashes are not full archive hashes.")
        mapping_id = replay.artifact(files["cards.csv"], raw=True, media_type="text/csv")
        source(replay, mapping_id, "17Lands official Arena card mapping", freeze["cards_mapping"]["url"], freeze["cards_mapping"]["retrieved_at"],
               "Exact official id/name CSV used independently by the evaluator and supplied to the candidate importer.")
        evaluator_id = replay.artifact(Path(coverage.__file__).read_bytes(), raw=True, media_type="text/x-python")
        source(replay, evaluator_id, "Frozen independent source coverage evaluator", "urn:coworld:17lands-coverage-v1", frozen_at,
               "Exact installed decoder/evaluator. Frozen before candidate observations; native implementation is not imported.")
        adapter_id = replay.artifact(Path(__file__).read_bytes(), raw=True, media_type="text/x-python")
        source(replay, adapter_id, "Frozen repetition and acceptance adapter", "urn:coworld:17lands-factory-v1", frozen_at,
               "Exact installed raw-output binding, coverage repetition reconciliation and acceptance-policy implementation.")
        cases = []
        for (role, row_range, data), expected in zip(partitions, expectations):
            dataset_id = replay.artifact(data, raw=True, media_type="text/csv")
            source(replay, dataset_id, "17Lands public wide CSV partition", freeze["archive_url"], when,
                   f"{role}: original data rows {row_range[0]} through {row_range[1]}; exact header and raw record bytes. " + freeze["scope"])
            spec = {"schema": "17lands-source-case-v1", "dataset_id": dataset_id, "mapping_id": mapping_id,
                    "role": role, "original_data_rows": row_range, "rows": expected["rows"]}
            case_id = replay.artifact(spec)
            replay.event("cases", "case_registered", case_id=case_id, title=f"17Lands {role}: source rows {row_range[0]}–{row_range[1]}",
                         derivation={"kind": "source_derived", "source_ids": [freeze_id, dataset_id, mapping_id],
                             "source_records": [{"source_id": dataset_id, "record_id": "data-rows:" + str(row_range[0]) + "-" + str(row_range[1])}],
                             "recipe": "First46 known rows primary, next46 known regression, first16 newly acquired complete rows holdout; whole92 aggregate overlaps the two known partitions and is informational.", "seed": None})
            expectation_id = replay.artifact(expected)
            cases.append({**spec, "case_id": case_id, "expectation_id": expectation_id})
            replay.feedback(case_id, [], {"schema": coverage.ENVELOPE, "summary": "Human draft-game records nominate a realistic importer workload; they are not a rules oracle.",
                            "data": {"role": role, "rows": expected["rows"], "source_cast_occurrences": expected["normalization"]["cast_occurrences"], "source_expectation_id": expectation_id}},
                            evaluator="17Lands observational workload nomination", evaluator_version=evaluator_id, strength="weak",
                            method="Public wide-game source selection", claim="The selected source rows contain recorded cast-list workload; no gameplay correctness follows.",
                            result="satisfied", summary="Recorded human workload; coverage will be evaluated separately against worker output.")
        plan = {"case_id": cases[0]["case_id"], "regression_case_ids": [cases[1]["case_id"]], "holdout_case_ids": [cases[2]["case_id"]]}
        plan_id = replay.artifact(plan)
        replay.event("gates", "acceptance_plan_frozen", plan_id=plan_id, plan=plan)
        policy = {"kind": "17lands-native-source-coverage-v1", "scope": coverage.CLAIM, "plan_id": plan_id,
                  "evaluator_sha256": evaluator_id, "repetitions": 2,
                  "requirements": ["repeatable primary baseline coverage violation", "same-build candidate coverage satisfaction on all frozen gates", "exact source/map/evaluator identities", "candidate build binds exact patch against baseline", "independent approving review"],
                  "limitations": ["Holdout is unseen rows of the same archive, not a new game format or rules test.", "The known92 aggregate overlaps primary and regression; do not sum their counts.", "Wide rows omit global action order, targets, priority and hidden state.", "Compilation provenance is caller attestation; source hashes do not independently prove compilation."]}
        policy_id = replay.artifact(policy)
        cfg = {"schema": "17lands-factory-v1", "source_freeze_id": freeze_id, "mapping_id": mapping_id,
               "evaluator_sha256": evaluator_id, "adapter_sha256": adapter_id, "cases": cases, "plan_id": plan_id, "policy_id": policy_id,
               "frozen_at": frozen_at}
        source(replay, replay.artifact(cfg), CONFIG_PROVIDER, "urn:coworld:17lands-factory-v1", cfg["frozen_at"],
               "Immutable source-only partitions, independent expectations, evaluator and acceptance policy. No private bootstrap material is included.")
        configuration(replay)
        verify_domain(replay, cfg)
        subprocess.run([str(args.runtime), "verify", str(replay.directory)], check=True)
        print(json.dumps({"run": str(replay.directory), "plan_id": plan_id, "evaluator_sha256": evaluator_id, "policy_id": policy_id}))


def validate_build(attestation, baseline, change_id, binary_hash=None):
    if attestation.get("schema") != "17lands-miner-build-v1" or attestation.get("program") != PROGRAM or attestation.get("repository") != REPOSITORY:
        raise ValueError("unsupported target build attestation")
    for key in ("source_revision", "base_revision", "declared_phase_revision"):
        if not isinstance(attestation.get(key), str) or not REVISION.fullmatch(attestation[key]):
            raise ValueError("build requires a full source revision: " + key)
    for key in ("patch_sha256", "binary_sha256", "cargo_lock_sha256"):
        if not isinstance(attestation.get(key), str) or not HASH.fullmatch(attestation[key]):
            raise ValueError("invalid build content hash: " + key)
    if attestation.get("source_tree_clean") is not True or attestation["base_revision"] != baseline:
        raise ValueError("build must attest a clean source tree and exact controlled baseline")
    if change_id is None:
        if attestation["source_revision"] != baseline or attestation["patch_sha256"] != sha256(b""):
            raise ValueError("baseline build must have no target patch")
    elif attestation["source_revision"] == baseline or attestation["patch_sha256"] != change_id:
        raise ValueError("candidate build must bind its distinct source commit to exact proposed patch")
    if binary_hash is not None and attestation["binary_sha256"] != binary_hash:
        raise ValueError("worker binary differs from attested bytes")
    files = attestation.get("source_files")
    if not isinstance(files, dict) or not files or "Cargo.lock" not in files:
        raise ValueError("build lacks source snapshot hashes")
    for path, identity in files.items():
        if not isinstance(path, str) or Path(path).is_absolute() or ".." in Path(path).parts or not isinstance(identity, str) or not HASH.fullmatch(identity):
            raise ValueError("invalid source snapshot path/hash")
    if files["Cargo.lock"] != attestation["cargo_lock_sha256"]:
        raise ValueError("Cargo lock differs from source snapshot")
    if attestation.get("source_files_before") != files or attestation.get("source_files_after") != files:
        raise ValueError("source changed across compilation or lacks before/after guard")
    if not isinstance(attestation.get("command"), list) or not attestation["command"] or any(not isinstance(x, str) or not x for x in attestation["command"]):
        raise ValueError("build command must be a nonempty argument vector")
    if not isinstance(attestation.get("environment"), dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in attestation["environment"].items()):
        raise ValueError("build environment must contain string values")
    compiler = attestation.get("compiler", {})
    if any(not isinstance(compiler.get(key), str) or not compiler[key].strip() for key in ("rustc_vv", "cargo_version")):
        raise ValueError("build lacks compiler identity")
    if not isinstance(attestation.get("attestation"), str) or not attestation["attestation"].strip():
        raise ValueError("build must describe its caller-attested provenance boundary")


def public_manifest(case, phase_revision):
    value = {"schema": "coworld-mtg-harness-corpus-v1", "manifest_id": "", "set": "MSH",
             "phase_revision": phase_revision, "generator_schema": "17lands-public-input-only-v1",
             "input_labels": {"cards_mapping_sha256": case["mapping_id"], "purpose": "Public CSV ingestion only; zero corpus-validation fields assert no Phase corpus validation."},
             "artifacts": {"17lands": {"source": "urn:sha256:" + case["dataset_id"], "sha256": case["dataset_id"],
                           "bytes": case["dataset_bytes"], "stored_path": "dataset.csv"}},
             "output_hashes": {}, "validation": {"phase_cards": 0, "phase_oracle_ids": 0, "scryfall_printings": 0,
             "matched_oracle_ids": 0, "matched_faces": 0, "scryfall_layouts": {}, "missing_scryfall_oracle_ids": [],
             "name_mismatches": [], "oracle_text_mismatches": [], "legality_mismatches": []}}
    value["manifest_id"] = sha256(canonical(value))
    return value


def evaluate_runs(case, expected, runs, manifest_id, cfg):
    evaluations = [coverage.evaluate(expected, run["observation"], manifest_id) for run in runs]
    def comparison(run):
        report = (run.get("observation") or {}).get("data", {})
        normalized = report.get("normalization")
        if isinstance(normalized, dict) and isinstance(normalized.get("cards_mapping"), dict):
            normalized = {**normalized, "cards_mapping": {k: v for k, v in normalized.get("cards_mapping", {}).items() if k != "source"}}
        return encode_json({key: report.get(key) for key in ("schema", "dataset_sha256", "manifest_id", "rows", "card_frequency")} | {"normalization": normalized})
    repeatable = (len(runs) == 2 and all(run["status"] == "completed" for run in runs)
                  and evaluations[0] == evaluations[1] and comparison(runs[0]) == comparison(runs[1]))
    result = evaluations[0]["result"] if repeatable else "inconclusive"
    return {"schema": coverage.ENVELOPE, "summary": "Independent source coverage receipt; acceptance requires the frozen policy and a recorded review.",
            "data": {"case_id": case["case_id"], "evaluator_sha256": cfg["evaluator_sha256"], "expectation_id": case["expectation_id"],
                     "evidence_ids": [run["evidence_id"] for run in runs], "repeatable": repeatable,
                     "evaluations": evaluations, "result": result}}


def execute(args):
    with Replay(args.run_dir) as replay:
        cfg = configuration(replay)
        verify_domain(replay, cfg)
        change_id = args.change_id
        if (args.phase == "candidate") != (change_id is not None):
            raise ValueError("only a candidate execution must specify its recorded change")
        if change_id and not any(p["change_id"] == change_id for p in payloads(replay, "change_proposed")):
            raise ValueError("candidate change must be proposed before execution")
        attestation = read_json(args.build_attestation)
        validate_build(attestation, replay.value["target"]["baseline_revision"], change_id, sha256(args.worker.read_bytes()))
        build_id = replay.build(PROGRAM, attestation["source_revision"], args.worker,
                                attestation["command"], attestation["environment"], attestation)
        selected = [case for case in cfg["cases"] if args.phase == "candidate" or case["role"] != "holdout"]
        for case in selected:
            data = artifact_bytes(replay, case["dataset_id"])
            mapping = artifact_bytes(replay, cfg["mapping_id"])
            manifest = public_manifest({**case, "dataset_bytes": len(data)}, attestation["declared_phase_revision"])
            def arguments(src, dst):
                (src.parent / "dataset.csv").write_bytes(data)
                (src.parent / "cards.csv").write_bytes(mapping)
                argv = ["mine17lands", "--manifest-uri", str(src), "--output", str(dst), "--row-limit", str(case["rows"])]
                if args.phase == "candidate":
                    argv += ["--input-schema", "public-replay-wide-v1", "--cards-csv", str(src.parent / "cards.csv"), "--cards-csv-sha256", cfg["mapping_id"]]
                return argv
            runs = [replay.run_jsonl(execution_id=f'{args.phase}-{(change_id or build_id)[:12]}-{case["role"]}-{repeat}',
                        case_id=case["case_id"], build_id=build_id, binary=args.worker, record=manifest,
                        arguments=arguments, protocol=PROTOCOL, classify_status=lambda value: ("completed", None),
                        change_id=change_id, decode_output=coverage.decode_native, output_media_type="application/json") for repeat in range(2)]
            expected = artifact_json(replay, case["expectation_id"])
            receipt = evaluate_runs(case, expected, runs, manifest["manifest_id"], cfg)
            replay.feedback(case["case_id"], [r["execution_id"] for r in runs], receipt,
                            evaluator=coverage.EVALUATOR, evaluator_version=cfg["evaluator_sha256"], strength="strong",
                            method=coverage.METHOD, claim=coverage.CLAIM, result=receipt["data"]["result"],
                            summary=case["role"] + ": " + receipt["data"]["result"] + "; " + coverage.CLAIM)
        verify_domain(replay, cfg)
        subprocess.run([str(args.runtime), "verify", str(replay.directory)], check=True)


def strong_feedbacks(replay):
    return [p["feedback"] for p in payloads(replay, "feedback_recorded") if p["feedback"]["declared_strength"] == "strong"]


def verify_domain(replay, cfg):
    builds = {p["build_id"]: p["build"] for p in payloads(replay, "build_recorded")}
    starts = {p["execution_id"]: p for p in payloads(replay, "execution_started")}
    finishes = {p["execution_id"]: p for p in payloads(replay, "execution_finished")}
    cases = {case["case_id"]: case for case in cfg["cases"]}
    observations = {}
    for identity, start in starts.items():
        case = cases[start["case_id"]]
        build = builds[start["build_id"]]
        attestation = artifact_json(replay, build["attestation_id"])
        validate_build(attestation, replay.value["target"]["baseline_revision"], start["change_id"], build["binary_sha256"])
        if build != {"program": PROGRAM, "source_revision": attestation["source_revision"], "binary_sha256": attestation["binary_sha256"],
                     "command": attestation["command"], "environment": attestation["environment"], "attestation_id": build["attestation_id"]}:
            raise ValueError("build envelope differs from attestation")
        request = artifact_json(replay, start["request_id"])
        manifest = public_manifest({**case, "dataset_bytes": len(artifact_bytes(replay, case["dataset_id"]))}, attestation["declared_phase_revision"])
        if artifact_json(replay, request["input_sha256"]) != manifest:
            raise ValueError("worker public manifest differs from exact frozen case/build")
        if request["protocol"] != PROTOCOL or request["case_id"] != case["case_id"] or request["build_id"] != start["build_id"] or request["worker_sha256"] != build["binary_sha256"]:
            raise ValueError("worker request differs from case, protocol or build")
        command = request.get("command", [])
        if len(command) < 8 or command[1:3] != ["mine17lands", "--manifest-uri"] or command[4] != "--output":
            raise ValueError("worker request lacks its exact native invocation")
        src, dst = Path(command[3]), Path(command[5])
        expected_command = [command[0], "mine17lands", "--manifest-uri", str(src), "--output", str(dst), "--row-limit", str(case["rows"])]
        if start["change_id"] is not None:
            expected_command += ["--input-schema", "public-replay-wide-v1", "--cards-csv", str(src.parent / "cards.csv"), "--cards-csv-sha256", cfg["mapping_id"]]
        if command != expected_command or src.name != "input.jsonl" or dst != src.parent / "output.jsonl":
            raise ValueError("worker invocation differs from declared baseline/candidate capabilities")
        if identity not in finishes:
            continue  # A live snapshot may end while its worker is running.
        finish = finishes[identity]
        evidence = artifact_json(replay, finish["evidence_id"])
        if evidence["request_id"] != start["request_id"] or evidence["worker_sha256"] != build["binary_sha256"]:
            raise ValueError("execution evidence differs from request/build")
        if type(evidence.get("timed_out")) is not bool or (evidence.get("exit_code") is not None and type(evidence["exit_code"]) is not int):
            raise ValueError("worker status requires boolean timeout and integer exit status")
        output_id = evidence.get("output_artifact_id")
        output = None
        output_valid = False
        if output_id is not None:
            if output_id not in finish["trace_ids"] or replay.value["artifacts"][output_id]["hash_mode"] != "bytes":
                raise ValueError("native raw output must be a retained byte trace")
            raw = artifact_bytes(replay, output_id)
            if len(raw) <= 16 * 1024**2 and evidence["exit_code"] == 0 and evidence["timed_out"] is False and evidence.get("detail") != "worker interrupted":
                try:
                    output = coverage.decode_native(raw)
                    output_valid = True
                except Exception:
                    pass
        expected_status = "cancelled" if evidence.get("detail") == "worker interrupted" else "completed" if output_valid else "error"
        if finish["status"] != expected_status or encode_json(evidence["observation"]) != encode_json(output):
            raise ValueError("recorded observation/status differs from retained native output")
        observations[identity] = {"execution_id": identity, "evidence_id": finish["evidence_id"], "observation": output, "status": finish["status"], "manifest_id": manifest["manifest_id"]}
    for feedback in strong_feedbacks(replay):
        if any(feedback.get(key) != value for key, value in {"adapter": "opaque", "evaluator": coverage.EVALUATOR,
                "evaluator_version": cfg["evaluator_sha256"], "method": coverage.METHOD, "bounded_claim": coverage.CLAIM}.items()):
            raise ValueError("feedback differs from frozen evaluator attribution")
        ids = feedback["execution_ids"]
        if len(ids) != 2 or len(set(ids)) != 2 or len({starts[x]["build_id"] for x in ids}) != 1 or len({starts[x]["change_id"] for x in ids}) != 1 or any(starts[x]["case_id"] != feedback["case_id"] for x in ids):
            raise ValueError("feedback must bind two distinct same-build executions of one case/change")
        case = cases[feedback["case_id"]]
        runs = [observations[x] for x in ids]
        expected = evaluate_runs(case, artifact_json(replay, case["expectation_id"]), runs, runs[0]["manifest_id"], cfg)
        if encode_json(artifact_json(replay, feedback["feedback_id"])) != encode_json(expected) or feedback["result"] != expected["data"]["result"]:
            raise ValueError("feedback differs from independently recomputed source coverage")
    return starts


def propose(args):
    with Replay(args.run_dir) as replay:
        cfg = configuration(replay)
        starts = verify_domain(replay, cfg)
        motivating = [f["feedback_id"] for f in strong_feedbacks(replay) if f["result"] == "violated" and all(starts[x]["change_id"] is None for x in f["execution_ids"])]
        patch = args.patch.read_bytes()
        if not motivating or not patch.startswith(b"diff --git ") or not args.description.strip():
            raise ValueError("proposal needs measured baseline failure, actual Git diff and description")
        identity = sha256(patch)
        if any(p["change_id"] == identity for p in payloads(replay, "change_proposed")):
            raise ValueError("exact change already proposed")
        replay.artifact(patch, raw=True, media_type="text/x-diff")
        replay.event("changes", "change_proposed", validation_runtime=args.runtime, change_id=identity,
                     description=args.description, base_revision=replay.value["target"]["baseline_revision"], motivating_feedback_ids=motivating)
        print(json.dumps({"change_id": identity}))


def decision_inputs(replay, cfg, change_id):
    starts = verify_domain(replay, cfg)
    plan = artifact_json(replay, cfg["plan_id"])
    required = [plan["case_id"], *plan["regression_case_ids"], *plan["holdout_case_ids"]]
    baseline = [f for f in strong_feedbacks(replay) if f["case_id"] == plan["case_id"] and {starts[x]["change_id"] for x in f["execution_ids"]} == {None}]
    candidates = [f for f in strong_feedbacks(replay) if f["case_id"] in required and {starts[x]["change_id"] for x in f["execution_ids"]} == {change_id}]
    if len(baseline) != 1 or len(candidates) != len(required) or {f["case_id"] for f in candidates} != set(required):
        raise ValueError("exact baseline and every frozen candidate gate must have unambiguous feedback")
    if len({starts[x]["build_id"] for f in candidates for x in f["execution_ids"]}) != 1:
        raise ValueError("candidate gates must use one identical build")
    if baseline[0]["result"] != "violated" or any(f["result"] != "satisfied" for f in candidates):
        raise ValueError("frozen source coverage gates did not all pass after a measured baseline violation")
    by_case = {f["case_id"]: f for f in candidates}
    return baseline[0], by_case[plan["case_id"]], [by_case[x]["feedback_id"] for x in required[1:]]


def record_review(args):
    if not args.reviewer.strip() or not args.rationale.strip() or not args.report.read_bytes().strip():
        raise ValueError("review needs a named reviewer, substantive rationale and retained report")
    with Replay(args.run_dir) as replay:
        cfg = configuration(replay)
        baseline, candidate, _ = decision_inputs(replay, cfg, args.change_id)
        report_id = replay.artifact(args.report.read_bytes(), raw=True, media_type="text/plain")
        review = {"plan_id": cfg["plan_id"], "baseline_receipt_id": baseline["feedback_id"], "candidate_receipt_id": candidate["feedback_id"],
                  "reviewer": args.reviewer, "rationale": args.rationale + " Full independent report artifact: " + report_id, "decision": args.decision}
        identity = replay.artifact(review)
        replay.event("review", "review_recorded", validation_runtime=args.runtime, review_id=identity, review=review)
        print(json.dumps({"review_id": identity, "report_id": report_id}))


def decide(args):
    with Replay(args.run_dir) as replay:
        cfg = configuration(replay)
        verify_domain(replay, cfg)
        if not any(p["change_id"] == args.change_id for p in payloads(replay, "change_proposed")) or any(p["change_id"] == args.change_id for p in payloads(replay, "decision_recorded")):
            raise ValueError("decision needs a proposed, undecided change")
        try:
            baseline, candidate, gates = decision_inputs(replay, cfg, args.change_id)
        except ValueError as error:
            decision = {"kind": "rejected", "reasons": [str(error)]}
        else:
            reviews = [p["review"] for p in payloads(replay, "review_recorded") if p["review_id"] == args.review_id]
            if len(reviews) != 1:
                raise ValueError("passing coverage gates require a recorded independent review")
            review = reviews[0]
            if review["plan_id"] != cfg["plan_id"] or review["baseline_receipt_id"] != baseline["feedback_id"] or review["candidate_receipt_id"] != candidate["feedback_id"]:
                raise ValueError("review differs from exact frozen plan and before/after feedback")
            decision = {"kind": "rejected", "reasons": ["Independent review rejected: " + review["rationale"]]} if review["decision"] == "reject" else {
                "kind": "accepted", "plan_id": cfg["plan_id"], "baseline_receipt_id": baseline["feedback_id"], "candidate_receipt_id": candidate["feedback_id"], "gate_receipt_ids": gates, "review_id": args.review_id}
        identity = replay.artifact(decision)
        attestation_id = replay.artifact({"policy_id": cfg["policy_id"], "scope": coverage.CLAIM, "decision_id": identity, "plan_id": cfg["plan_id"], "change_id": args.change_id})
        replay.event("decisions", "decision_recorded", validation_runtime=args.runtime, decision_id=identity, change_id=args.change_id,
                     plan_id=cfg["plan_id"], decision=decision, policy={"kind": "external", "policy_id": cfg["policy_id"], "scope": coverage.CLAIM, "attestation_id": attestation_id})
        replay.finish()
        print(json.dumps({"decision_id": identity, "result": decision["kind"], "scope": coverage.CLAIM}))


def verify_run(args):
    subprocess.run([str(args.runtime), "verify", str(args.run_dir)], check=True)
    replay = object.__new__(Replay)
    replay.directory = args.run_dir.resolve()
    replay.value = read_json(replay.directory / "replay.json")
    cfg = configuration(replay)
    verify_domain(replay, cfg)
    for p in payloads(replay, "decision_recorded"):
        if p["policy"]["policy_id"] != cfg["policy_id"] or p["policy"]["scope"] != coverage.CLAIM or p["plan_id"] != cfg["plan_id"]:
            raise ValueError("decision differs from frozen coverage policy")
        if p["decision"]["kind"] == "accepted":
            baseline, candidate, gates = decision_inputs(replay, cfg, p["change_id"])
            d = p["decision"]
            if d["baseline_receipt_id"] != baseline["feedback_id"] or d["candidate_receipt_id"] != candidate["feedback_id"] or d["gate_receipt_ids"] != gates:
                raise ValueError("decision differs from recomputed coverage feedback")
    print("Recomputed native importer source coverage from retained public CSV, mapping and raw native output.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    for name in ("source-dir", "output-dir", "runtime"):
        prep.add_argument("--" + name, type=Path, required=True)
    prep.add_argument("--run-id", required=True)
    prep.add_argument("--title", default="17Lands: native public CSV cast coverage")
    prep.add_argument("--baseline-revision", required=True)
    execute_parser = commands.add_parser("execute")
    execute_parser.add_argument("--phase", choices=("baseline", "candidate"), required=True)
    execute_parser.add_argument("--change-id")
    execute_parser.add_argument("--worker", type=Path, required=True)
    execute_parser.add_argument("--build-attestation", type=Path, required=True)
    proposal = commands.add_parser("propose")
    proposal.add_argument("--patch", type=Path, required=True)
    proposal.add_argument("--description", required=True)
    review = commands.add_parser("review")
    review.add_argument("--report", type=Path, required=True)
    review.add_argument("--reviewer", required=True)
    review.add_argument("--rationale", required=True)
    review.add_argument("--decision", choices=("approve", "reject"), required=True)
    decision = commands.add_parser("decide")
    decision.add_argument("--review-id")
    verify = commands.add_parser("verify")
    for command in (execute_parser, proposal, review, decision, verify):
        command.add_argument("--run-dir", type=Path, required=True)
        command.add_argument("--runtime", type=Path, required=True)
    for command in (review, decision):
        command.add_argument("--change-id", required=True)
    args = parser.parse_args()
    {"prepare": prepare, "execute": execute, "propose": propose, "review": record_review,
     "decide": decide, "verify": verify_run}[args.command](args)


if __name__ == "__main__":
    main()
