#!/usr/bin/env python3
"""Import a retained MTG acceptance archive into the verified replay format.

This reconstructs logical event order from retained artifacts. It does not run
the old scenarios, rebuild old workers, infer historical timing, or change the
original acceptance. The shared factory runtime validates the deep MTG adapter.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

EXPECTED_HUSHBRINGER_ACCEPTANCE = "66ef2e974d5dfb7f59f93f98405dcd6d9dd7b17fb9fab9df0fc3491dfdf6aba4"
RECORDING_DESCRIPTION = "reconstructed logical order from retained artifacts; no historical timing"
AUTHORED_DESCRIPTION = (
    "Authored case from the retained acceptance archive. The scenario is an authored "
    "engine setup and operation sequence, not a Scryfall-discovered case or a recorded human game."
)
ARCHIVE_URL = "https://github.com/Metta-AI/coworld-mtg/tree/main/cases/evidence/"


class ImportError(ValueError):
    pass


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return sha256(canonical(value))


def read_json(path):
    return json.loads(Path(path).read_bytes())


def write_json(path, value):
    with Path(path).open("x") as output:
        output.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n")


def ensure_separate_output(archive, output):
    archive, output = Path(archive).resolve(), Path(output).resolve()
    if archive == output or archive in output.parents or output in archive.parents:
        raise ImportError("output must be separate from the retained archive")
    if output.exists():
        raise FileExistsError("refusing to overwrite an existing replay directory")
    return archive, output


def validate_bundle(directory, expected_case_id, build):
    case = read_json(directory / "case.json")
    request = read_json(directory / "request.json")
    receipt = read_json(directory / "receipt.json")
    if digest(case) != expected_case_id or receipt["case_id"] != expected_case_id:
        raise ImportError(f"case identity mismatch in {directory}")
    if request["scenario"] != case["scenario"]:
        raise ImportError(f"request scenario differs from retained case in {directory}")
    corpus_id = sha256((directory / "corpus.json").read_bytes())
    if corpus_id != request["corpus_sha256"] or corpus_id != receipt["corpus_sha256"]:
        raise ImportError(f"corpus identity mismatch in {directory}")
    if receipt["worker_sha256"] != build["binary_sha256"]:
        raise ImportError(f"worker differs from retained build in {directory}")
    evidence = [read_json(directory / f"execution-{index}.json") for index in range(len(receipt["evidence_sha256"]))]
    if [digest(item) for item in evidence] != receipt["evidence_sha256"]:
        raise ImportError(f"evidence identity mismatch in {directory}")
    if any(item["request_id"] != digest(request) or item["binary_sha256"] != receipt["worker_sha256"]
           for item in evidence):
        raise ImportError(f"execution/request/worker binding mismatch in {directory}")
    return {"directory": directory, "case": case, "request": request,
            "receipt": receipt, "evidence": evidence}


def load_archive(archive, expected_acceptance_id=EXPECTED_HUSHBRINGER_ACCEPTANCE):
    archive = Path(archive).resolve()
    if not archive.is_dir():
        raise ImportError("archive directory is absent")
    for path in archive.rglob("*"):
        if path.is_symlink():
            raise ImportError("symlink in evidence archive: " + str(path))
    decision = read_json(archive / "acceptance.json")
    if digest(decision) != expected_acceptance_id:
        raise ImportError("original acceptance identity does not match the requested accepted archive")
    if decision.get("kind") != "accepted":
        raise ImportError("archive does not contain an accepted decision")
    plan, review, case = (read_json(archive / name) for name in ("plan.json", "review.json", "case.json"))
    if decision["plan_id"] != digest(plan) or decision["review_id"] != digest(review) or plan["case_id"] != digest(case):
        raise ImportError("original plan/review/case identities do not agree")
    baseline_build = read_json(archive / "baseline-build.json")
    candidate_build = read_json(archive / "candidate-build.json")
    patch_id = sha256((archive / "repair.patch").read_bytes())
    attribution = read_json(archive / "attribution.json")
    build_ids = {label: sha256((archive / f"{label}-build.json").read_bytes())
                 for label in ("baseline", "candidate")}
    if any(attribution["repair"][f"{label}_build_sha256"] != identity
           for label, identity in build_ids.items()):
        raise ImportError("build bytes differ from original attribution identities")
    if attribution["repair"]["patch_sha256"] != patch_id or attribution["acceptance"] != decision:
        raise ImportError("attribution patch or acceptance differs from retained artifacts")
    if candidate_build["phase"].get("kind") != "checkout" or candidate_build["phase"].get("patch_sha256") != patch_id:
        raise ImportError("candidate build does not attest to the retained patch")
    base_revision = baseline_build["phase"]["revision"]
    if candidate_build["phase"].get("base_revision") != base_revision:
        raise ImportError("baseline and candidate build revisions do not agree")
    case_ids = [plan["case_id"], *plan["regression_case_ids"], *plan["holdout_case_ids"]]
    if len(set(case_ids)) != len(case_ids):
        raise ImportError("acceptance plan case groups are not disjoint")
    baseline = validate_bundle(archive / "baseline" / plan["case_id"], plan["case_id"], baseline_build)
    candidates = [validate_bundle(archive / "candidate" / case_id, case_id, candidate_build) for case_id in case_ids]
    if digest(baseline["receipt"]) != decision["baseline_receipt_id"] or digest(candidates[0]["receipt"]) != decision["candidate_receipt_id"]:
        raise ImportError("primary receipts differ from the original acceptance")
    if [digest(bundle["receipt"]) for bundle in candidates[1:]] != decision["gate_receipt_ids"]:
        raise ImportError("ordered gate receipts differ from the original acceptance")
    return {
        "path": archive, "case": case, "plan": plan, "review": review, "decision": decision,
        "baseline_build": baseline_build, "candidate_build": candidate_build, "build_ids": build_ids,
        "baseline": baseline, "candidates": candidates, "patch_id": patch_id,
        "base_revision": base_revision, "acceptance_id": digest(decision),
    }


class ArtifactStore:
    def __init__(self, output, replay):
        self.output, self.replay = output, replay
        self.inventory = []
        (output / "artifacts").mkdir()

    def add(self, raw, hash_mode, media_type, suffix, original_path=None):
        identity = digest(json.loads(raw)) if hash_mode == "canonical_json" else sha256(raw)
        relative = f"artifacts/{identity}{suffix}"
        if identity not in self.replay["artifacts"]:
            (self.output / relative).write_bytes(raw)
            self.replay["artifacts"][identity] = {
                "path": relative, "media_type": media_type, "hash_mode": hash_mode,
            }
        if original_path is not None:
            self.inventory.append({
                "original_path": original_path, "content_id": identity,
                "original_bytes_sha256": sha256(raw), "original_bytes": len(raw),
                "retained_path": self.replay["artifacts"][identity]["path"],
            })
        return identity

    def file(self, path, original_path=None):
        path = Path(path)
        # The original attribution records build identities as exact file bytes.
        byte_hashed_json = {"corpus.json", "baseline-build.json", "candidate-build.json"}
        mode = "canonical_json" if path.suffix == ".json" and path.name not in byte_hashed_json else "bytes"
        media = {".json": "application/json", ".md": "text/markdown", ".patch": "text/x-diff"}.get(path.suffix, "text/plain")
        return self.add(path.read_bytes(), mode, media, path.suffix or ".txt", original_path)

    def json(self, value):
        return self.add(canonical(value) + b"\n", "canonical_json", "application/json", ".json")


def import_archive(archive, output, runtime, run_id=None,
                   expected_acceptance_id=EXPECTED_HUSHBRINGER_ACCEPTANCE,
                   corpus_provenance=None):
    archive, output = ensure_separate_output(archive, output)
    data = load_archive(archive, expected_acceptance_id)
    runtime = Path(runtime).resolve()
    if not runtime.is_file():
        raise ImportError("factory runtime executable is absent")
    if corpus_provenance is None:
        inferred = archive.parents[1] / "corpus" / "sources.json"
        corpus_provenance = inferred if inferred.is_file() else None
    if corpus_provenance is not None:
        provenance = read_json(corpus_provenance)
        if provenance.get("corpus_sha256") != data["baseline"]["receipt"]["corpus_sha256"]:
            raise ImportError("retained corpus provenance identifies a different corpus")
    output.mkdir(parents=True)
    initial = output / "initial-replay.json"
    target_repository = data["baseline_build"]["phase"]["repository"]
    subprocess.run([
        str(runtime), "init", "--run-id", run_id or "imported-" + archive.name,
        "--title", data["case"]["title"] + " (authored, imported)", "--program", "Phase MTG engine",
        "--repository", target_repository, "--baseline-revision", data["base_revision"],
        "--output", str(initial),
    ], check=True, capture_output=True, text=True)
    replay = read_json(initial)
    replay["recording"] = {"kind": "imported", "description": RECORDING_DESCRIPTION}
    replay["status"] = "completed"
    store = ArtifactStore(output, replay)
    for path in sorted(archive.rglob("*")):
        if path.is_file():
            store.file(path, str(path.relative_to(archive)))
    provenance_id = store.file(corpus_provenance, "external/cases/corpus/sources.json") if corpus_provenance else None

    def event(stage, kind, **fields):
        replay["events"].append({"sequence": len(replay["events"]), "elapsed_ms": None,
                                 "stage": stage, "payload": {"kind": kind, **fields}})

    corpus_id = data["baseline"]["receipt"]["corpus_sha256"]
    event("sources", "source_imported", source={
        "snapshot_id": corpus_id, "provider": "Retained parsed Phase card corpus",
        "url": ARCHIVE_URL + archive.name,
        "retrieved_at": "not recorded in retained archive",
        "description": (
            "Parsed engine card data retained with the original executions. The original raw Scryfall "
            "snapshot and its retrieval time are not retained here. "
            + (f"Original corpus source metadata is retained as artifact {provenance_id}." if provenance_id else
               "No separate original corpus source metadata was found.")
        ),
    })
    for bundle in data["candidates"]:
        spec = bundle["case"]
        event("cases", "case_registered", case_id=digest(spec), title=spec["title"],
              derivation={"kind": "authored", "author": spec["author"], "description": AUTHORED_DESCRIPTION})

    def record_build(attestation, attestation_id):
        build = {
            "program": "Phase MTG engine", "source_revision": attestation["phase"]["revision"],
            "binary_sha256": attestation["binary_sha256"], "command": attestation["command"],
            "environment": attestation["build_environment"], "attestation_id": attestation_id,
        }
        build_id = store.json(build)
        event("execute", "build_recorded", build_id=build_id, build=build)
        return build_id

    def record_bundle(bundle, build_id, change_id, label):
        spec, receipt = bundle["case"], bundle["receipt"]
        case_id, request_id, receipt_id = digest(spec), digest(bundle["request"]), digest(receipt)
        execution_ids = []
        for index, evidence in enumerate(bundle["evidence"]):
            execution_id = f"{label}-{case_id[:12]}-repeat-{index + 1}"
            execution_ids.append(execution_id)
            event("execute", "execution_started", execution_id=execution_id, case_id=case_id,
                  request_id=request_id, build_id=build_id, change_id=change_id)
            kind = evidence["outcome"]["kind"]
            if kind not in ("completed", "inconclusive"):
                raise ImportError("unsupported retained execution outcome: " + kind)
            event("execute", "execution_finished", execution_id=execution_id, status=kind,
                  evidence_id=digest(evidence), trace_ids=[],
                  detail="Imported retained execution evidence and ordered step hashes; historical timing was not retained.")
        event("feedback", "feedback_recorded", feedback={
            "adapter": "mtg_evaluation_v1", "feedback_id": receipt_id, "case_id": case_id,
            "execution_ids": execution_ids, "evaluator": "coworld-mtg-harness retained case checker",
            "evaluator_version": receipt["checker_sha256"], "declared_strength": "strong",
            "method": "Original repeated execution receipts; the shared MTG adapter rechecks observations, reachability guards and assertions.",
            "bounded_claim": "Only the authored CaseSpec scenario, guards and assertions; no source-discovery or universal gameplay claim.",
            "result": receipt["result"]["kind"],
            "summary": f'Retained {label} result: {receipt["result"]["kind"]}; {len(execution_ids)} executions preserved.',
        })

    baseline_build_id = record_build(data["baseline_build"], data["build_ids"]["baseline"])
    record_bundle(data["baseline"], baseline_build_id, None, "baseline")
    event("changes", "change_proposed", change_id=data["patch_id"],
          description="Retained accepted repair: use event-time trigger-suppression authority and last-known information during simultaneous deaths.",
          base_revision=data["base_revision"],
          motivating_feedback_ids=[digest(data["baseline"]["receipt"])])
    event("gates", "acceptance_plan_frozen", plan_id=digest(data["plan"]), plan=data["plan"])
    candidate_build_id = record_build(data["candidate_build"], data["build_ids"]["candidate"])
    for bundle in data["candidates"]:
        record_bundle(bundle, candidate_build_id, data["patch_id"], "candidate")
    event("review", "review_recorded", review_id=digest(data["review"]), review=data["review"])
    event("decisions", "decision_recorded", policy={"kind": "mtg_conformance_v1"},
          decision_id=data["acceptance_id"], change_id=data["patch_id"],
          plan_id=digest(data["plan"]), decision=data["decision"])

    report = {
        "schema_version": 1, "recording": replay["recording"],
        "original_acceptance_id": data["acceptance_id"],
        "original_attribution_id": digest(read_json(archive / "attribution.json")),
        "original_patch_sha256": data["patch_id"],
        "case_origin": "authored", "retained_baseline_bundles": 1,
        "retained_candidate_bundles": len(data["candidates"]),
        "retained_execution_count": sum(len(bundle["evidence"]) for bundle in [data["baseline"], *data["candidates"]]),
        "regression_case_count": len(data["plan"]["regression_case_ids"]),
        "holdout_case_count": len(data["plan"]["holdout_case_ids"]),
        "historical_timing": "not retained; all event elapsed_ms values are null",
        "raw_scryfall_snapshot": "not retained by this archive",
        "corpus_provenance_id": provenance_id,
        "source_file_inventory": store.inventory,
        "scope": "Import and deep verification of retained evidence, not new executions or a new acceptance.",
        "importer_sha256": sha256(Path(__file__).read_bytes()),
        "runtime_sha256": sha256(runtime.read_bytes()),
    }
    report_id = store.json(report)
    write_json(output / "import-report.json", dict(report, report_artifact_id=report_id))
    write_json(output / "replay.json", replay)
    # A failure is kept as an attempted import with its diagnostic. Never relax validation.
    checked = subprocess.run([str(runtime), "verify", str(output)], capture_output=True, text=True)
    write_json(output / "verification.json", {"exit_code": checked.returncode,
               "stdout": checked.stdout, "stderr": checked.stderr, "acceptance_id": data["acceptance_id"]})
    if checked.returncode:
        raise ImportError("deep factory validation rejected imported evidence: " + checked.stderr.strip())
    bundle_path = output / "portable-bundle.json"
    subprocess.run([str(runtime), "export", str(output), "--output", str(bundle_path)],
                   check=True, capture_output=True, text=True)
    subprocess.run([str(runtime), "verify", str(bundle_path)],
                   check=True, capture_output=True, text=True)
    return {"run_dir": str(output), "acceptance_id": data["acceptance_id"],
            "events": len(replay["events"]), "artifacts": len(replay["artifacts"]),
            "executions": report["retained_execution_count"], "portable_bundle": str(bundle_path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--expected-acceptance-id", default=EXPECTED_HUSHBRINGER_ACCEPTANCE)
    parser.add_argument("--corpus-provenance", type=Path)
    args = parser.parse_args()
    result = import_archive(args.archive, args.output_dir, args.runtime, args.run_id,
                            args.expected_acceptance_id, args.corpus_provenance)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
