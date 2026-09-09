"""Constructed protocol/tamper regressions; production measurements use real CSV and native workers."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace as Args
import unittest

from test_factory_recording import RecorderFixture, RUNTIME
import factory_replay as kernel
import fit17lands_factory as factory

BASE = "a" * 40


class FileTransportTests(RecorderFixture):
    def test_named_native_outputs_and_companion_are_retained(self):
        raw = b'{"fixture":true}\n'
        result = self.replay.run_jsonl(execution_id="files", case_id=self.case({}), build_id=self.build(),
            binary=sys.executable, record={}, protocol="fixture-files-v1",
            arguments=lambda src, dst: ["-c", "import pathlib,sys;p=pathlib.Path(sys.argv[1]);"
                "p.write_bytes(" + repr(raw) + ");p.with_name('constraints.json').write_bytes(b'{}')", str(dst)],
            classify_status=lambda _: ("completed", None), decode_output=json.loads,
            output_name="result.json", companion_names=("constraints.json",))
        self.assertEqual(result["status"], "completed")
        receipt = factory.artifact_json(self.replay, result["evidence_id"])
        self.assertEqual(factory.artifact_bytes(self.replay, receipt["output_artifact_id"]), raw)
        self.assertEqual(factory.artifact_bytes(self.replay, receipt["companion_artifact_ids"]["constraints.json"]), b"{}")

    def test_missing_or_symlink_companion_makes_execution_error(self):
        for name, code in [
            ("missing", ""),
            ("symlink", "p.with_name('constraints.json').symlink_to('/etc/passwd')")]:
            result = self.replay.run_jsonl(execution_id=name, case_id=self.case({"name": name}), build_id=self.build(),
                binary=sys.executable, record={}, protocol="fixture-files-v1",
                arguments=lambda src, dst: ["-c",
                    "import pathlib,sys;p=pathlib.Path(sys.argv[1]);p.write_bytes(b'{}');" + code, str(dst)],
                classify_status=lambda _: ("completed", None), decode_output=json.loads,
                output_name="result.json", companion_names=("constraints.json",))
            self.assertEqual(result["status"], "error")
            self.assertIsNone(result["observation"])
            receipt = factory.artifact_json(self.replay, result["evidence_id"])
            self.assertEqual(receipt["companion_artifact_ids"], {})
            self.assertIn("constraints.json", receipt["companion_errors"])

    def test_unsafe_duplicate_or_reserved_names_rejected_before_start(self):
        for name, companions in [("../escape", ()), ("stdout.txt", ()), ("result.json", ("result.json",)),
                                 ("result.json", ("../constraints.json",))]:
            with self.subTest(name=name, companions=companions), self.assertRaises(ValueError):
                self.replay.run_jsonl(execution_id="unsafe", case_id=self.case({}), build_id=self.build(),
                    binary=sys.executable, record={}, protocol="fixture", arguments=lambda *_: [],
                    classify_status=lambda _: ("completed", None), output_name=name, companion_names=companions)
        self.assertFalse(factory.payloads(self.replay, "execution_started"))


WORKER = r'''#!/usr/bin/python3
import hashlib,json,pathlib,sys
args=sys.argv
def flag(name): return args[args.index(name)+1]
def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
index=int(flag('--game-index'))
issue={"kind":"unsupported_projection","detail":"Constructed projection gap","source_columns":["user_turn_1_user_mana_spent"],"evidence":None}
constraints={"seed":index,"game_index":index,"source_sha256":flag('--replay-sha256'),
"cards_mapping_sha256":flag('--cards-csv-sha256'),"issues":[issue],
"fields":[{"column":"user_turn_1_user_mana_spent","raw":"0.0","milestone":{"turn_owner":0,"turn_index":1,"boundary":"end_of_turn","observed_player":0},
"disposition":"unsupported","reason":"Constructed fixture gap","projection":None,"expected":None}],
"decks":[[],[]],"libraries":[[],[]],"assumptions":["Constructed test only"],"milestones":[]}
manifest=json.loads(pathlib.Path(flag('--manifest-uri')).read_text())
result={"schema":"coworld-17lands-guided-fit-v1","seed":index,"status":"matched_supported_projection",
"nodes":1,"limits":{"nodes":int(flag('--nodes')),"max_actions":int(flag('--max-actions'))},
"input_sha256":digest(constraints),"source_sha256":constraints["source_sha256"],
"cards_mapping_sha256":constraints["cards_mapping_sha256"],"manifest_id":manifest["manifest_id"],"phase_revision":manifest["phase_revision"],"issues":[issue]}
out=pathlib.Path(flag('--output-dir'))
(out/'constraints.json').write_text(json.dumps(constraints))
(out/'result.json').write_text(json.dumps(result))
'''


@unittest.skipUnless(RUNTIME.is_file(), "set FACTORY_RUNTIME to existing native runtime")
class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.run = self.root / "run"
        source = b"id,on_play\nfixture-0,True\nfixture-1,False\n"
        mapping = b"id,name\n1,Constructed card\n"
        (self.root / "games.csv").write_bytes(source)
        (self.root / "cards.csv").write_bytes(mapping)
        cohort = {"schema":"coworld/17lands-cohort@1",
            "source":{"url":"https://example.test/fixture.csv","attribution":"Constructed test fixture"},
            "replay":{"path":"games.csv","sha256":kernel.sha256(source)},
            "mapping":{"path":"cards.csv","sha256":kernel.sha256(mapping)},
            "selection":{"no_filters":True,"unseen_holdout":False},
            "fit":{"turn_pairs":2,"nodes":100,"max_actions":32,"opponent_filler":"Plains"},
            "cases":[{"game_index":i,"source_row_index":i,"role":"evaluation"} for i in range(2)]}
        self.cohort = self.root / "cohort.json"
        self.cohort.write_text(json.dumps(cohort))
        self.manifest = self.root / "manifest.json"
        self.manifest.write_text(json.dumps({"manifest_id":"test-runtime","phase_revision":"b"*40}))
        self.worker = self.root / "worker"
        self.worker.write_text(WORKER)
        self.worker.chmod(0o755)
        build = {"schema":"coworld-guided-fit-build-v1","source_revision":BASE,
                 "worker_sha256":kernel.sha256(self.worker.read_bytes()),"exit_code":0,
                 "source_files_before":{"test":"1"*64},"source_files_after":{"test":"1"*64},
                 "command":["constructed-test-worker"],"environment":{},"elapsed_seconds":0.125}
        self.build = self.root / "build.json"
        self.build.write_text(json.dumps(build))
        self.args = Args(runtime=RUNTIME,run_dir=self.run,cohort=self.cohort,input_manifest=self.manifest,
            baseline_revision=BASE,run_id="fixture-discovery",title="Constructed discovery fixture",
            deadline_seconds=5,memory_bytes=256*1024**2,label="baseline",worker=self.worker,
            build_attestation=self.build,change_id=None)
        factory.prepare(self.args)
        factory.execute(self.args)

    def replay(self):
        obj = object.__new__(kernel.Replay)
        obj.directory = self.run
        obj.value = json.loads((self.run / "replay.json").read_bytes())
        return obj

    def test_report_deduplicates_diagnostic_but_retains_every_origin(self):
        replay = self.replay()
        report_id, report = factory.all_reports(replay)[-1]
        self.assertTrue(report["complete"])
        self.assertEqual(len(report["cases"]), 2)
        self.assertEqual(len(report["issues"]), 1)
        self.assertEqual(len(report["issues"][0]["origins"]), 2)
        self.assertEqual(report["issues"][0]["component"], "observation_adapter")
        factory.verify_domain(replay)
        factory.verify(self.args)
        bundle = self.root / "replay-bundle.json"
        subprocess.run([str(RUNTIME),"export",str(self.run),"--output",str(bundle)],check=True,capture_output=True)
        exported = json.loads(bundle.read_bytes())
        self.assertIn(report_id, exported["artifact_contents"])

    def test_changed_runtime_manifest_rejected_before_additional_execution(self):
        self.manifest.write_text('{"manifest_id":"other"}')
        self.args.label = "candidate"
        with self.assertRaisesRegex(ValueError, "runtime manifest differs"):
            factory.execute(self.args)

    def test_rehashed_report_cannot_drop_issue_or_claim_more_coverage(self):
        with kernel.Replay(self.run) as replay:
            identity, report = factory.all_reports(replay)[-1]
            report["issues"] = []
            replacement = replay.artifact(report)
            event = next(e for e in reversed(replay.value["events"])
                         if e["payload"].get("source",{}).get("snapshot_id") == identity)
            event["payload"]["source"]["snapshot_id"] = replacement
            with self.assertRaisesRegex(ValueError, "derived discovery report differs"):
                factory.verify_domain(replay)

    def test_rehashed_receipt_cannot_change_request_seed_or_time_limit(self):
        for field, value in [("--game-index","999"),("--nodes","999")]:
            replay = self.replay()
            start = factory.payloads(replay,"execution_started")[0]
            request = factory.artifact_json(replay,start["request_id"])
            request["command"][request["command"].index(field)+1] = value
            with kernel.Replay(self.run) as writer:
                identity = writer.artifact(request)
                replay.value["artifacts"].update(writer.value["artifacts"])
                start["request_id"] = identity
                finish = factory.payloads(replay,"execution_finished")[0]
                evidence = factory.artifact_json(replay,finish["evidence_id"])
                evidence["request_id"] = identity
                finish["evidence_id"] = writer.artifact(evidence)
                replay.value["artifacts"].update(writer.value["artifacts"])
            with self.assertRaisesRegex(ValueError, "command differs from scope"):
                factory.verify_domain(replay)

    def test_failed_process_cannot_be_relabelled_matched(self):
        replay = self.replay()
        finish = factory.payloads(replay,"execution_finished")[0]
        evidence = factory.artifact_json(replay,finish["evidence_id"])
        evidence["timed_out"] = True
        with kernel.Replay(self.run) as writer:
            finish["evidence_id"] = writer.artifact(evidence)
            replay.value["artifacts"].update(writer.value["artifacts"])
        with self.assertRaisesRegex(ValueError, "failed execution cannot"):
            factory.verify_domain(replay)

    def test_feedback_strength_cannot_be_promoted_by_rehashing_report(self):
        replay = self.replay()
        factory.payloads(replay,"feedback_recorded")[0]["feedback"]["declared_strength"] = "strong"
        with self.assertRaisesRegex(ValueError, "feedback envelope"):
            factory.verify_domain(replay)


class SignatureTests(unittest.TestCase):
    def test_only_same_diagnostic_is_grouped_across_turn_numbers(self):
        first = {"kind":"unsupported_projection","detail":"missing event binding",
                 "source_columns":["user_turn_1_user_mana_spent"]}
        second = {**first,"source_columns":["oppo_turn_5_user_mana_spent"]}
        self.assertEqual(factory.issue_identity(first),factory.issue_identity(second))
        self.assertNotEqual(factory.issue_identity(first),factory.issue_identity({**second,"detail":"different diagnosis"}))

    def test_unknown_and_duplicate_native_json_are_rejected(self):
        for raw in [b'{"schema":"x"}',b'{"schema":"x","schema":"x"}',b'{"x":NaN}']:
            with self.assertRaises(ValueError):
                factory.decode_result(raw)
