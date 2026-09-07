"""Focused failure-path tests for the recorder and bounded domain audit.

All data and workers here are explicitly constructed test fixtures. Production
Scryfall runs use retained source records and the actual Phase worker instead.
"""
import copy
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import factory_replay as recorder
import mana_library_oracle as oracle
import scryfall_factory as factory

RUNTIME = Path(os.environ.get("FACTORY_RUNTIME", Path(os.environ.get("CARGO_TARGET_DIR", ROOT / "target")) / "debug/factory-runtime"))


class RecorderFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.directory = self.root / "recording-test"
        if RUNTIME.is_file():
            self.replay = recorder.Replay.create(
                RUNTIME, self.directory, "recording-test", "Recorder test fixture",
                "Fixture parser", "https://example.test/fixture-parser", "fixture-base")
        else:
            # Recorder unit tests require only its storage fields; the portable
            # export test below separately requires the real contract runtime.
            self.directory.mkdir()
            (self.directory / "artifacts").mkdir()
            (self.directory / "work").mkdir()
            recorder.atomic_json(self.directory / "replay.json", {
                "status": "running", "events": [], "artifacts": {},
                "target": {"baseline_revision": "fixture-base"}})
            recorder.atomic_json(self.directory / ".recording-clock.json", {
                "started_unix_ms": time.time_ns() // 1_000_000})
            self.replay = recorder.Replay(self.directory)
        self.addCleanup(self.replay.lock.close)

    def case(self, record):
        raw = json.dumps(record, ensure_ascii=False, allow_nan=False).encode()
        identity = self.replay.artifact(raw, raw=True)
        self.replay.event("cases", "case_registered", case_id=identity,
                          title="Constructed recorder test input",
                          derivation={"kind": "authored", "author": "unit test",
                                      "description": "Constructed input for recorder validation"})
        return identity

    def build(self):
        return self.replay.build("Fixture parser", "fixture-base", sys.executable,
                                 [sys.executable], {}, None)

    def run_worker(self, code, record=None, name="worker", deadline=5):
        record = {"fixture": True} if record is None else record
        return self.replay.run_jsonl(
            execution_id=name, case_id=self.case(record), build_id=self.build(),
            binary=sys.executable, record=record,
            arguments=lambda src, dst: ["-c", code, str(src), str(dst)],
            protocol="fixture-jsonl-v1", deadline_seconds=deadline,
            classify_status=lambda output: ("completed", None))


class RecorderTests(RecorderFixture):
    def test_atomic_json_is_valid_and_artifact_failure_does_not_publish_partial_content(self):
        self.assertEqual(json.loads((self.directory / ".recording-clock.json").read_bytes())["started_unix_ms"], self.replay.started_unix_ms)
        value = {"fixture": "artifact publication interrupted"}
        identity = recorder.sha256(recorder.canonical(value))
        with patch.object(recorder.os, "link", side_effect=OSError("simulated publication failure")):
            with self.assertRaises(OSError):
                self.replay.artifact(value)
        self.assertFalse((self.directory / "artifacts" / identity).exists())
        self.assertNotIn(identity, self.replay.value["artifacts"])
        self.assertEqual(list((self.directory / "artifacts").glob(".artifact-*")), [])
        self.assertEqual(self.replay.artifact(value), identity)

    def test_binary_mismatch_is_rejected_before_starting_any_worker(self):
        case_id, build_id = self.case({"fixture": True}), self.build()
        alternate = self.root / "different-worker"
        alternate.write_bytes(b"a different executable identity")
        with patch.object(recorder.subprocess, "Popen") as spawn:
            with self.assertRaisesRegex(ValueError, "binary differs"):
                self.replay.run_jsonl(
                    execution_id="mismatched", case_id=case_id, build_id=build_id,
                    binary=alternate, record={"fixture": True}, arguments=lambda *_: [],
                    protocol="fixture-v1", classify_status=lambda _: ("completed", None))
            spawn.assert_not_called()
        self.assertFalse(any(e["payload"]["kind"] == "execution_started"
                             for e in self.replay.value["events"]))

    def test_timeout_stops_the_worker_and_its_spawned_descendant(self):
        child_file = self.root / "child-pid"
        code = (
            "import pathlib, subprocess, sys, time\n"
            "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
            f"pathlib.Path({str(child_file)!r}).write_text(str(child.pid))\n"
            "time.sleep(60)\n")
        child_pid = None
        try:
            result = self.run_worker(code, deadline=1)
            self.assertEqual(result["status"], "error")
            evidence = factory.artifact_json(self.replay, result["evidence_id"])
            self.assertTrue(evidence["timed_out"])
            self.assertIsNotNone(evidence["exit_code"])
            self.assertTrue(child_file.exists(), "descendant must actually have started")
            child_pid = int(child_file.read_text())
            for _ in range(50):
                if not process_running(child_pid):
                    break
                time.sleep(0.02)
            self.assertFalse(process_running(child_pid), "timed-out worker left its child running")
            self.assertFalse(process_running(evidence["worker_pid"]))
        finally:
            # Clean up only the descendant whose PID this test's worker recorded,
            # so a regression in production cleanup cannot leak this test process.
            if child_pid is None and child_file.exists():
                child_pid = int(child_file.read_text())
            if child_pid is not None and process_running(child_pid):
                os.kill(child_pid, signal.SIGKILL)

    def test_malformed_output_is_retained_and_execution_is_recorded_as_error(self):
        result = self.run_worker("import pathlib, sys; pathlib.Path(sys.argv[2]).write_bytes(b'{broken json')")
        self.assertEqual(result["status"], "error")
        finished = next(e["payload"] for e in self.replay.value["events"]
                        if e["payload"]["kind"] == "execution_finished")
        retained = [(self.directory / self.replay.value["artifacts"][identity]["path"]).read_bytes()
                    for identity in finished["trace_ids"]]
        self.assertIn(b"{broken json", retained)
        evidence = factory.artifact_json(self.replay, result["evidence_id"])
        self.assertIn("invalid worker output", evidence["detail"])

    @unittest.skipUnless(RUNTIME.is_file(), "set FACTORY_RUNTIME to the built standalone runtime")
    def test_raw_float_source_input_survives_portable_export_exactly(self):
        source = {"id": "fixture-id", "cmc": 1.5, "name": "café"}
        code = (
            "import json, pathlib, sys\n"
            "value = json.loads(pathlib.Path(sys.argv[1]).read_bytes())\n"
            "assert type(value['cmc']) is float and value['cmc'] == 1.5\n"
            "pathlib.Path(sys.argv[2]).write_text(json.dumps({'status':'parsed','received_float':True}) + '\\n')\n")
        result = self.run_worker(code, record=source)
        self.assertEqual(result["status"], "completed")
        started = next(e["payload"] for e in self.replay.value["events"]
                       if e["payload"]["kind"] == "execution_started")
        request = factory.artifact_json(self.replay, started["request_id"])
        input_id = request["input_sha256"]
        expected = (self.directory / "work/worker/input.jsonl").read_bytes()
        self.assertEqual(recorder.sha256(expected), input_id)
        self.replay.finish()
        bundle_path = self.root / "portable.json"
        subprocess.run([str(RUNTIME), "export", str(self.directory), "--output", str(bundle_path)], check=True, capture_output=True)
        bundle = json.loads(bundle_path.read_bytes())
        self.assertEqual(bundle["artifact_contents"][input_id].encode(), expected)
        self.assertEqual(json.loads(bundle["artifact_contents"][input_id]), source)
        subprocess.run([str(RUNTIME), "verify", str(bundle_path)], check=True, capture_output=True)

    def test_terminal_replay_cannot_be_mutated_through_existing_writer(self):
        self.replay.finish("failed")
        saved = (self.directory / "replay.json").read_bytes()
        for mutation in [lambda: self.replay.artifact({"later": True}),
                         lambda: self.replay.event("execute", "compute_recorded", usage={}),
                         self.replay.save, self.replay.finish]:
            with self.assertRaisesRegex(ValueError, "terminal"):
                mutation()
            self.assertEqual((self.directory / "replay.json").read_bytes(), saved)


def process_running(pid):
    status = Path(f"/proc/{pid}/stat")
    if status.exists():
        # A terminated descendant can briefly remain a zombie until its reaper runs.
        return status.read_text().rsplit(")", 1)[1].split()[0] not in ("Z", "X")
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


class DomainFeedbackTests(RecorderFixture):
    def build(self):
        attestation = {
            "binary_sha256": recorder.sha256(Path(sys.executable).read_bytes()),
            "phase_revision": "fixture-base", "declared_phase_revision": "fixture-base",
            "command": [sys.executable], "environment": {},
            "source_files": {}, "harness_revision": "explicit-test-fixture"}
        return self.replay.build("Fixture parser", "fixture-base", sys.executable,
                                 [sys.executable], {}, attestation)

    def setUp(self):
        super().setUp()
        self.card = {"object": "card", "id": "fixture-printing", "oracle_id": "fixture-oracle",
                     "name": "Constructed control fixture", "layout": "normal", "games": ["paper"],
                     "legalities": {"vintage": "legal"}, "type_line": "Artifact",
                     "oracle_text": "{T}: Add {G}."}
        self.case_id = self.case(self.card)
        self.build_id = self.build()
        self.cfg = {"cases": [{"case_id": self.case_id, "source_contract": oracle.source_contracts(self.card)}],
                    "evaluator_sha256": recorder.sha256(Path(oracle.__file__).read_bytes()),
                    "rules_sha256": self.replay.artifact(b"Explicit unit-test rules fixture", raw=True)}
        self.cfg["plan_id"] = self.replay.artifact({"case_id": self.case_id,
                                                   "regression_case_ids": [], "holdout_case_ids": []})
        self.cfg["policy_id"] = self.replay.artifact({
            "kind": "source-aligned-mana-classification-v1", "evaluator_sha256": self.cfg["evaluator_sha256"],
            "rules_sha256": self.cfg["rules_sha256"], "plan_id": self.cfg["plan_id"],
            "scope": factory.CLAIM, "repetitions": 2})
        ability = {"kind": "Activated", "cost": {"type": "Tap"},
                   "effect": {"type": "Mana", "produced": {"type": "Fixed", "colors": ["Green"]}},
                   "condition": None, "duration": None, "target_prompt": None,
                   "forward_result": False, "optional": False, "optional_targeting": False,
                   "sub_ability": None, "is_mana_ability": True}
        observation = {"status": "parsed", "oracle_id": self.card["oracle_id"],
                       "card_id": self.card["id"], "phase_revision": "fixture-base",
                       "parsed": {"abilities": [ability], "extractedKeywords": [],
                                  "replacements": [], "statics": [], "triggers": []}}
        runs = []
        for repeat in range(2):
            execution_id = f"fixture-{repeat}"
            input_id = self.replay.artifact(json.dumps(self.card).encode() + b"\n", raw=True)
            worker_hash = recorder.sha256(Path(sys.executable).read_bytes())
            request_id = self.replay.artifact({"protocol": "oracle-probe-jsonl-v1", "case_id": self.case_id,
                                               "build_id": self.build_id, "worker_sha256": worker_hash,
                                               "input_sha256": input_id})
            self.replay.event("execute", "execution_started", execution_id=execution_id,
                              case_id=self.case_id, request_id=request_id, build_id=self.build_id, change_id=None)
            evidence_id = self.replay.artifact({"request_id": request_id, "worker_sha256": worker_hash,
                                                "observation": observation, "fixture_repeat": repeat,
                                                "exit_code": 0, "timed_out": False, "detail": None})
            self.replay.event("execute", "execution_finished", execution_id=execution_id,
                              status="completed", evidence_id=evidence_id, trace_ids=[], detail=None)
            runs.append({"execution_id": execution_id, "evidence_id": evidence_id,
                         "status": "completed", "observation": observation})
        self.runs = runs
        receipt = factory.evaluate_runs(self.case_id, self.card, runs, "fixture-base", self.cfg)
        self.assertEqual(receipt["result"], "satisfied", "fixture must establish a real passing grammar check")
        self.replay.feedback(self.case_id, [r["execution_id"] for r in runs], receipt,
                             evaluator="Independent source-aligned CR605.1a grammar",
                             evaluator_version=self.cfg["evaluator_sha256"], strength="strong",
                             method="Constructed adapter regression fixture", claim=factory.CLAIM,
                             result="satisfied", summary="Constructed fixture passes its bounded check")
        self.feedback = self.replay.value["events"][-1]["payload"]["feedback"]

    def test_unchanged_evidence_recomputes_to_recorded_feedback(self):
        factory.verify_domain(self.replay, self.cfg)

    def test_rehashed_receipt_with_altered_result_fails_semantic_audit(self):
        receipt = factory.artifact_json(self.replay, self.feedback["feedback_id"])
        receipt["result"] = "violated"
        self.feedback["feedback_id"] = self.replay.artifact(receipt)
        self.feedback["result"] = "violated"
        with self.assertRaises(ValueError):
            factory.verify_domain(self.replay, self.cfg)

    def test_feedback_envelope_cannot_change_evaluator_or_claim(self):
        for field, replacement in [("evaluator_version", "different-evaluator"),
                                   ("bounded_claim", "All gameplay is correct")]:
            original = self.feedback[field]
            self.feedback[field] = replacement
            try:
                with self.assertRaises(ValueError, msg=field):
                    factory.verify_domain(self.replay, self.cfg)
            finally:
                self.feedback[field] = original

    def test_rehashed_worker_input_cannot_be_substituted_under_same_case(self):
        started = next(e["payload"] for e in self.replay.value["events"]
                       if e["payload"]["kind"] == "execution_started")
        request = factory.artifact_json(self.replay, started["request_id"])
        different = {**self.card, "oracle_text": "{T}: Add {R}."}
        request["input_sha256"] = self.replay.artifact(json.dumps(different).encode(), raw=True)
        started["request_id"] = self.replay.artifact(request)
        with self.assertRaisesRegex(ValueError, "input differs"):
            factory.verify_domain(self.replay, self.cfg)

    def test_nonzero_exit_or_timeout_cannot_be_relabelled_completed(self):
        finished = next(e["payload"] for e in self.replay.value["events"]
                        if e["payload"]["kind"] == "execution_finished")
        original_evidence, original_feedback = finished["evidence_id"], self.feedback["feedback_id"]
        for field, value in [("exit_code", 9), ("timed_out", True)]:
            evidence = factory.artifact_json(self.replay, original_evidence)
            evidence[field] = value
            finished["evidence_id"] = self.replay.artifact(evidence)
            receipt = factory.artifact_json(self.replay, original_feedback)
            receipt["evidence_ids"][0] = finished["evidence_id"]
            self.feedback["feedback_id"] = self.replay.artifact(receipt)
            try:
                with self.assertRaises(ValueError, msg=field):
                    factory.verify_domain(self.replay, self.cfg)
            finally:
                finished["evidence_id"] = original_evidence
                self.feedback["feedback_id"] = original_feedback

    def test_two_repeats_cannot_mix_different_build_records(self):
        original_build = next(e["payload"]["build"] for e in self.replay.value["events"]
                              if e["payload"]["kind"] == "build_recorded")
        alternate_build = copy.deepcopy(original_build)
        alternate_build["environment"]["FIXTURE_BUILD_VARIANT"] = "different-recipe"
        alternate_id = self.replay.artifact(alternate_build)
        index = next(i for i, e in enumerate(self.replay.value["events"])
                     if e["payload"]["kind"] == "build_recorded") + 1
        self.replay.value["events"].insert(index, {
            "sequence": index, "elapsed_ms": None, "stage": "execute",
            "payload": {"kind": "build_recorded", "build_id": alternate_id, "build": alternate_build}})
        for i, event in enumerate(self.replay.value["events"]):
            event["sequence"] = i
        start = next(e["payload"] for e in self.replay.value["events"]
                     if e["payload"].get("execution_id") == "fixture-1"
                     and e["payload"]["kind"] == "execution_started")
        finish = next(e["payload"] for e in self.replay.value["events"]
                      if e["payload"].get("execution_id") == "fixture-1"
                      and e["payload"]["kind"] == "execution_finished")
        request = factory.artifact_json(self.replay, start["request_id"])
        request["build_id"] = alternate_id
        start["build_id"], start["request_id"] = alternate_id, self.replay.artifact(request)
        evidence = factory.artifact_json(self.replay, finish["evidence_id"])
        evidence["request_id"] = start["request_id"]
        finish["evidence_id"] = self.replay.artifact(evidence)
        receipt = factory.artifact_json(self.replay, self.feedback["feedback_id"])
        receipt["evidence_ids"][1] = finish["evidence_id"]
        self.feedback["feedback_id"] = self.replay.artifact(receipt)
        with self.assertRaises(ValueError):
            factory.verify_domain(self.replay, self.cfg)

    def test_source_revision_and_declared_pin_are_separate(self):
        receipt = factory.evaluate_runs(self.case_id, self.card, self.runs,
                                        "fixture-candidate-source", self.cfg,
                                        declared_revision="fixture-base")
        self.assertTrue(receipt["repeatable"])
        self.assertEqual(receipt["phase_revision"], "fixture-candidate-source")
        self.assertEqual(receipt["result"], "satisfied")

    def test_missing_classifier_boolean_remains_inconclusive(self):
        observation = copy.deepcopy(self.runs[0]["observation"])
        observation["parsed"]["abilities"][0].pop("is_mana_ability")
        result = oracle.evaluate_card(self.card, observation)
        self.assertEqual(result["verdict"], "inconclusive")
        self.assertTrue(result["gate_blocked"])
