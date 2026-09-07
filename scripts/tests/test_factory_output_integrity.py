"""Raw observation integrity and transport tests with explicit synthetic workers."""
import json
import subprocess
import sys
import time
import unittest

from test_factory_recording import DomainFeedbackFixture, RecorderFixture, ROOT, RUNTIME
import factory_replay as recorder
import scryfall_factory as factory


class OutputIntegrityTests(DomainFeedbackFixture):
    def rewrite_evidence_and_feedback(self, mutate):
        runs = []
        for event in self.replay.value["events"]:
            finished = event["payload"]
            if finished["kind"] != "execution_finished":
                continue
            evidence = factory.artifact_json(self.replay, finished["evidence_id"])
            mutate(evidence, finished)
            finished["evidence_id"] = self.replay.artifact(evidence)
            runs.append({"execution_id": finished["execution_id"],
                         "evidence_id": finished["evidence_id"],
                         "observation": evidence["observation"], "status": finished["status"]})
        # Recompute the downstream receipt so a failure must concern transport
        # integrity, not stale hashes or a verdict inconsistent with its nested AST.
        receipt = factory.evaluate_runs(self.case_id, self.card, runs, "fixture-base", self.cfg)
        self.feedback["feedback_id"] = self.replay.artifact(receipt)
        self.feedback["result"] = receipt["result"]
        return receipt

    def test_rehashed_nested_observation_cannot_disagree_with_retained_output(self):
        before = {event["payload"]["execution_id"]: list(event["payload"]["trace_ids"])
                  for event in self.replay.value["events"]
                  if event["payload"]["kind"] == "execution_finished"}
        def alter_observation(evidence, finished):
            evidence["observation"]["parsed"]["abilities"][0]["is_mana_ability"] = False
        receipt = self.rewrite_evidence_and_feedback(alter_observation)
        self.assertEqual(receipt["result"], "violated")
        self.assertEqual(before, {event["payload"]["execution_id"]: event["payload"]["trace_ids"]
                                  for event in self.replay.value["events"]
                                  if event["payload"]["kind"] == "execution_finished"})
        with self.assertRaises(ValueError):
            factory.verify_domain(self.replay, self.cfg)

    def test_explicit_output_identity_must_belong_to_execution_traces(self):
        def substitute_unlisted_output(evidence, finished):
            # The JSON value remains identical; only its recorded provenance differs.
            data = b" " + json.dumps(evidence["observation"]).encode() + b"\n"
            evidence["output_artifact_id"] = self.replay.artifact(data, raw=True,
                                                                media_type="application/x-ndjson")
            self.assertNotIn(evidence["output_artifact_id"], finished["trace_ids"])
        self.rewrite_evidence_and_feedback(substitute_unlisted_output)
        with self.assertRaises(ValueError):
            factory.verify_domain(self.replay, self.cfg)

    def test_raw_output_cannot_be_replaced_by_a_canonical_json_artifact(self):
        def substitute_canonical_output(evidence, finished):
            evidence["output_artifact_id"] = self.replay.artifact(evidence["observation"])
            finished["trace_ids"] = [evidence["output_artifact_id"]]
        self.rewrite_evidence_and_feedback(substitute_canonical_output)
        with self.assertRaises(ValueError):
            factory.verify_domain(self.replay, self.cfg)

    def test_legacy_receipt_with_one_retained_jsonl_trace_still_verifies(self):
        self.rewrite_evidence_and_feedback(lambda evidence, _: evidence.pop("output_artifact_id"))
        factory.verify_domain(self.replay, self.cfg)

    def test_legacy_receipt_without_raw_output_cannot_verify_success(self):
        def remove_output(evidence, finished):
            evidence.pop("output_artifact_id")
            finished["trace_ids"] = []
        self.rewrite_evidence_and_feedback(remove_output)
        with self.assertRaises(ValueError):
            factory.verify_domain(self.replay, self.cfg)

    def test_legacy_receipt_cannot_choose_between_multiple_jsonl_traces(self):
        def add_ambiguous_output(evidence, finished):
            evidence.pop("output_artifact_id")
            alternate = self.replay.artifact(b" " + json.dumps(evidence["observation"]).encode() + b"\n",
                                             raw=True, media_type="application/x-ndjson")
            finished["trace_ids"].append(alternate)
        self.rewrite_evidence_and_feedback(add_ambiguous_output)
        with self.assertRaises(ValueError):
            factory.verify_domain(self.replay, self.cfg)


class OutputTransportTests(RecorderFixture):
    @unittest.skipUnless(RUNTIME.is_file(), "set FACTORY_RUNTIME to the built standalone runtime")
    def test_finite_float_observation_survives_receipt_and_portable_export(self):
        output = b'{"status":"parsed","score":1.25,"uncertainty":1e-12,"name":"caf\xc3\xa9"}\n'
        result = self.run_worker("import pathlib, sys; pathlib.Path(sys.argv[2]).write_bytes(" + repr(output) + ")")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["observation"], json.loads(output))
        finished = next(event["payload"] for event in self.replay.value["events"]
                        if event["payload"]["kind"] == "execution_finished")
        evidence = factory.artifact_json(self.replay, result["evidence_id"])
        output_id = evidence["output_artifact_id"]
        self.assertIn(output_id, finished["trace_ids"])
        self.assertEqual(output_id, recorder.sha256(output))
        self.assertEqual(self.replay.value["artifacts"][result["evidence_id"]]["hash_mode"], "bytes")
        self.assertEqual(evidence["observation"], json.loads(output))
        self.replay.finish()
        bundle_path = self.root / "float-observation.json"
        subprocess.run([str(RUNTIME), "export", str(self.directory), "--output", str(bundle_path)],
                       check=True, capture_output=True)
        bundle = json.loads(bundle_path.read_bytes())
        self.assertEqual(bundle["artifact_contents"][output_id].encode(), output)
        self.assertEqual(json.loads(bundle["artifact_contents"][result["evidence_id"]])["observation"], json.loads(output))
        subprocess.run([str(RUNTIME), "verify", str(bundle_path)], check=True, capture_output=True)

    def run_protocol_violation(self, code):
        case_id, build_id = self.case({"fixture": "output file transport"}), self.build()
        self.replay.lock.close()
        wrapper = """
import json, sys
sys.path.insert(0, sys.argv[1])
from factory_replay import Replay
with Replay(sys.argv[2]) as replay:
    result = replay.run_jsonl(
        execution_id='transport-worker', case_id=sys.argv[3], build_id=sys.argv[4],
        binary=sys.executable, record={'fixture': 'output file transport'},
        arguments=lambda src, dst: ['-c', sys.argv[5], str(src), str(dst)],
        protocol='fixture-jsonl-v1', deadline_seconds=1,
        classify_status=lambda output: ('completed', None))
    print(json.dumps(result))
"""
        started = time.monotonic()
        try:
            completed = subprocess.run([sys.executable, "-c", wrapper, str(ROOT / "scripts"),
                                        str(self.directory), case_id, build_id, code],
                                       check=True, capture_output=True, text=True, timeout=4)
        except subprocess.TimeoutExpired:
            self.fail("recorder blocked on a non-regular worker output file")
        self.assertLess(time.monotonic() - started, 4)
        result = json.loads(completed.stdout)
        self.replay.value = json.loads(self.replay.path.read_bytes())
        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["observation"])
        evidence = factory.artifact_json(self.replay, result["evidence_id"])
        self.assertIn("invalid worker output", evidence["detail"])
        self.assertIsNone(evidence.get("output_artifact_id"))
        return evidence

    def test_symlink_output_is_rejected_without_reading_its_target(self):
        target = self.root / "outside-output.jsonl"
        contents = b'{"fixture_secret":"must not be followed"}\n'
        target.write_bytes(contents)
        self.run_protocol_violation(
            "import os, sys; os.symlink(" + repr(str(target)) + ", sys.argv[2])")
        self.assertEqual(target.read_bytes(), contents)
        self.assertNotIn(recorder.sha256(contents), self.replay.value["artifacts"])

    def test_fifo_output_is_rejected_without_blocking_for_a_writer(self):
        self.run_protocol_violation("import os, sys; os.mkfifo(sys.argv[2])")
