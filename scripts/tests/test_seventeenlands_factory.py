"""Constructed transport/policy fixtures, never reported as measured miner results."""
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
import seventeenlands_coverage as coverage
import seventeenlands_factory as factory

HEADER = "draft_id,game_number,user_turn_1_creatures_cast,oppo_turn_2_user_instants_sorceries_cast,user_total_creatures_cast\n"
MAPPING = b"id,name\n1,First card\n2,Second card\n3,First card\n"
SOURCE = (HEADER + 'fixture,1,1|2|1,3,999\n').encode()
BASE = "a" * 40
PHASE = "b" * 40
PATCH = b"diff --git a/fixture.rs b/fixture.rs\n--- a/fixture.rs\n+++ b/fixture.rs\n@@ -1 +1 @@\n-broken\n+fixed\n"


def native_report(expected, manifest_id="fixture-manifest"):
    return {"schema": coverage.NATIVE_SCHEMA, "dataset_sha256": expected["source_sha256"], "manifest_id": manifest_id,
            "rows": expected["rows"], "card_frequency": copy.deepcopy(expected["card_frequency"]),
            "normalization": {**copy.deepcopy(expected["normalization"]), "cards_mapping": {"sha256": expected["mapping_sha256"], "bytes": len(MAPPING), "source": "fixture.csv"}},
            "numeric_summaries": [{"name": "fixture-score", "mean": 1.25}]}


def attestation(binary, change_id=None):
    files = {"Cargo.lock": "1" * 64, "crates/fixture.rs": "2" * 64}
    return {"schema": "17lands-miner-build-v1", "program": factory.PROGRAM, "repository": factory.REPOSITORY,
            "source_revision": "c" * 40 if change_id else BASE, "base_revision": BASE, "declared_phase_revision": PHASE,
            "patch_sha256": change_id or kernel.sha256(b""), "binary_sha256": kernel.sha256(binary.read_bytes()),
            "cargo_lock_sha256": files["Cargo.lock"], "source_files": files, "source_files_before": dict(files), "source_files_after": dict(files),
            "source_tree_clean": True, "compiler": {"rustc_vv": "fixture compiler", "cargo_version": "fixture Cargo"},
            "command": ["fixture-build"], "environment": {"FIXTURE": "true"}, "attestation": "Constructed unit-test fixture; no real compilation or miner success is asserted."}


class CoverageTests(unittest.TestCase):
    def test_independent_census_preserves_repeats_ids_roles_and_name_aggregation(self):
        expected = coverage.source_expectation(SOURCE, MAPPING)
        self.assertTrue(expected["qualified"])
        self.assertEqual(expected["normalization"]["cast_occurrences"], 4)
        self.assertEqual(expected["normalization"]["distinct_cast_arena_ids"], 3)
        self.assertEqual(expected["card_frequency"], [{"name": "First card", "count": 3}, {"name": "Second card", "count": 1}])
        cast = expected["normalization"]["casts"][-1]
        self.assertEqual((cast["row"], cast["column"], cast["value_index"], cast["arena_id"], cast["active_player"], cast["casting_player"], cast["cast_kind"]),
                         (1, "oppo_turn_2_user_instants_sorceries_cast", 0, 3, "oppo", "user", "instant_sorcery"))
        report = native_report(expected)
        self.assertEqual(coverage.evaluate(expected, coverage.decode_native(kernel.encode_json(report)), "fixture-manifest")["result"], "satisfied")
        report["card_frequency"] = []
        report.pop("normalization")
        self.assertEqual(coverage.evaluate(expected, coverage.decode_native(kernel.encode_json(report)), "fixture-manifest")["result"], "violated")

    def test_unknown_schema_unmapped_invalid_and_conflicting_mapping_are_inconclusive(self):
        for data, mapping in [(SOURCE.replace(b"creatures_cast", b"CREATURES_CAST"), MAPPING),
                              (SOURCE.replace(b"1|2|1", b"900"), MAPPING),
                              (SOURCE.replace(b"1|2|1", b" 1|4294967296|0"), MAPPING),
                              (SOURCE, MAPPING + b"1,Conflicting name\n")]:
            with self.subTest(source=data, mapping=mapping):
                expected = coverage.source_expectation(data, mapping)
                self.assertFalse(expected["qualified"])
                self.assertEqual(coverage.evaluate(expected, None, "fixture")["result"], "inconclusive")

    def test_missing_rows_wrong_source_or_unknown_normalization_is_not_a_semantic_failure(self):
        expected = coverage.source_expectation(SOURCE, MAPPING)
        for mutate in [lambda r: r.update(rows=0), lambda r: r.update(dataset_sha256="9"*64),
                       lambda r: r["normalization"].update(schema="unknown"), lambda r: r.pop("normalization")]:
            report = native_report(expected)
            mutate(report)
            self.assertEqual(coverage.evaluate(expected, coverage.decode_native(kernel.encode_json(report)), "fixture-manifest")["result"], "inconclusive")

    def test_unknown_normalization_is_inconclusive_before_frequency_comparison(self):
        expected = coverage.source_expectation(SOURCE,MAPPING)
        for normalization in [{"schema": "future-v2"}, None, [], "unsupported"]:
            for frequency in [expected["card_frequency"], []]:
                with self.subTest(normalization=normalization,frequency=frequency):
                    report = native_report(expected)
                    report["normalization"] = normalization
                    report["card_frequency"] = frequency
                    result = coverage.evaluate(expected,coverage.decode_native(kernel.encode_json(report)),"fixture-manifest")
                    self.assertEqual(result["result"],"inconclusive")
        report = native_report(expected)
        report.pop("normalization")
        report["card_frequency"] = []
        self.assertEqual(coverage.evaluate(expected,coverage.decode_native(kernel.encode_json(report)),"fixture-manifest")["result"],"violated")

    def test_normalization_identity_tampering_violates_even_when_frequency_is_unchanged(self):
        expected = coverage.source_expectation(SOURCE, MAPPING)
        report = native_report(expected)
        report["normalization"]["casts"][0]["arena_id"] = 3  # Same official name, different source ID.
        self.assertEqual(coverage.evaluate(expected, coverage.decode_native(kernel.encode_json(report)), "fixture-manifest")["result"], "violated")

    def test_card_name_column_is_not_confused_with_a_cast_schema_column(self):
        lines = SOURCE.splitlines()
        source = lines[0] + b",deck_Castle Doom\n" + lines[1] + b",1\n"
        expected = coverage.source_expectation(source,MAPPING)
        self.assertTrue(expected["qualified"])
        self.assertEqual(expected["normalization"]["cast_occurrences"],4)

    def test_empty_pipe_positions_whitespace_and_boolean_counts_are_not_silently_accepted(self):
        data = SOURCE.replace(b"1|2|1", b"1|1|999||x| ")
        expected = coverage.source_expectation(data, MAPPING)
        self.assertEqual(expected["normalization"]["cast_occurrences"], 7)
        self.assertEqual(expected["normalization"]["invalid_cast_occurrences"], 3)
        self.assertFalse(expected["qualified"])
        expected = coverage.source_expectation(SOURCE, MAPPING)
        report = native_report(expected)
        report["card_frequency"][1]["count"] = True
        self.assertEqual(coverage.evaluate(expected, coverage.decode_native(kernel.encode_json(report)), "fixture-manifest")["result"], "violated")

    def test_raw_record_slicing_preserves_quoted_newlines_and_rejects_missing_rows(self):
        data = b'id,name\r\n1,"line one\nline two"\r\n2,last\r\n'
        self.assertEqual(coverage.slice_csv(data, 2, 2), b'id,name\r\n2,last\r\n')
        with self.assertRaises(ValueError):
            coverage.slice_csv(data, 2, 3)

    def test_native_decoder_rejects_duplicate_nonfinite_utf8_schema_and_boolean_rows(self):
        for raw in [b'{"schema":"x","schema":"y"}', b'{"n":NaN}', b'{"n":1e999}', b'\xff', b'{}',
                    kernel.encode_json({"schema": coverage.NATIVE_SCHEMA, "rows": True, "card_frequency": []})]:
            with self.subTest(raw=raw), self.assertRaises((ValueError, UnicodeError)):
                coverage.decode_native(raw)


class NativeTransportTests(RecorderFixture):
    def run_native(self, raw, decoder=coverage.decode_native, returncode=0):
        return self.replay.run_jsonl(execution_id="native", case_id=self.case({"fixture": "native-json"}), build_id=self.build(),
            binary=sys.executable, record={"fixture": "native-json"}, protocol="fixture-native-json-v1",
            arguments=lambda src, dst: ["-c", "import pathlib,sys;pathlib.Path(sys.argv[1]).write_bytes(" + repr(raw) + ");sys.exit(" + str(returncode) + ")", str(dst)],
            classify_status=lambda value: ("completed", None), decode_output=decoder, output_media_type="application/json")

    def test_pretty_native_json_preserves_raw_bytes_and_finite_floats(self):
        raw = json.dumps(native_report(coverage.source_expectation(SOURCE, MAPPING)), indent=2).encode()
        result = self.run_native(raw)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["observation"]["data"]["numeric_summaries"][0]["mean"], 1.25)
        evidence = factory.artifact_json(self.replay, result["evidence_id"])
        self.assertEqual(factory.artifact_bytes(self.replay, evidence["output_artifact_id"]), raw)
        self.assertEqual(self.replay.value["artifacts"][evidence["output_artifact_id"]]["hash_mode"], "bytes")
        self.assertEqual(factory.artifact_json(self.replay, evidence["request_id"])["command"][0], str(Path(sys.executable).resolve()))

    def test_decoder_exception_preserves_raw_output_but_publishes_no_observation(self):
        def broken(_):
            raise RuntimeError("fixture decoder failed")
        result = self.run_native(b'{"partial": true}', decoder=broken)
        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["observation"])
        evidence = factory.artifact_json(self.replay, result["evidence_id"])
        self.assertIsNotNone(evidence["output_artifact_id"])

    def test_process_failure_is_not_replaced_by_successful_native_output(self):
        result = self.run_native(kernel.encode_json(native_report(coverage.source_expectation(SOURCE, MAPPING))), returncode=2)
        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["observation"])


@unittest.skipUnless(RUNTIME.is_file(), "set FACTORY_RUNTIME to existing native runtime")
class FactoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        known = (HEADER + "".join(f"constructed,{i},1|2|1,3,999\n" for i in range(1, 93))).encode()
        holdout = (HEADER + "".join(f"constructed,{i},1,2,999\n" for i in range(93, 109))).encode()
        files = {"known-92.csv": known, "holdout-first-16-new.csv": holdout, "cards.csv": MAPPING}
        for name, data in files.items():
            (self.source / name).write_bytes(data)
        freeze = {"schema": "constructed-test-fixture", "artifacts": {name: {"sha256": kernel.sha256(data), "bytes": len(data)} for name, data in files.items()},
                  "prefix_match": {"exact": True}, "selection": {"known_data_rows": [1,92], "holdout_data_rows": [93,108]},
                  "archive_url": "https://example.test/constructed.csv.gz", "retrieved_at": "2026-09-07T00:00:00Z",
                  "cards_mapping": {"url": "https://example.test/cards.csv", "retrieved_at": "2026-09-07T00:00:00Z"},
                  "dataset_attribution": "Constructed unit-test data.", "modification": "Constructed fixture.", "scope": "Tests only; no real gameplay or miner result."}
        (self.source / "source-freeze.json").write_bytes(kernel.canonical(freeze))
        self.run_dir = self.root / "run"
        factory.prepare(Args(source_dir=self.source, output_dir=self.run_dir, run_id="fixture-17lands", title="Constructed coverage fixture", baseline_revision=BASE, runtime=RUNTIME))
        self.worker = self.root / "fixture-worker"
        reports = {}
        for data in [known, holdout, coverage.slice_csv(known,1,46), coverage.slice_csv(known,47,92)]:
            expected = coverage.source_expectation(data,MAPPING)
            reports[expected["source_sha256"]] = native_report(expected)
        self.worker.write_text('#!/usr/bin/env python3\nimport json,sys,pathlib\nreports=' + repr(reports) + '\nargs=sys.argv\nmanifest=json.loads(pathlib.Path(args[args.index("--manifest-uri")+1]).read_bytes())\nreport=reports[manifest["artifacts"]["17lands"]["sha256"]]\nreport["manifest_id"]=manifest["manifest_id"]\nif "--input-schema" not in args:\n report["card_frequency"]=[]\n report.pop("normalization")\npathlib.Path(args[args.index("--output")+1]).write_text(json.dumps(report,indent=2))\n')
        self.worker.chmod(0o700)
        self.baseline_attestation = self.root / "baseline.json"
        self.baseline_attestation.write_bytes(kernel.canonical(attestation(self.worker)))
        self.change_id = kernel.sha256(PATCH)
        self.candidate_attestation = self.root / "candidate.json"
        self.candidate_attestation.write_bytes(kernel.canonical(attestation(self.worker, self.change_id)))
        self.patch = self.root / "change.patch"
        self.patch.write_bytes(PATCH)

    def execute(self, phase):
        factory.execute(Args(run_dir=self.run_dir, runtime=RUNTIME, worker=self.worker, phase=phase,
            change_id=self.change_id if phase == "candidate" else None,
            build_attestation=self.candidate_attestation if phase == "candidate" else self.baseline_attestation))

    def candidate(self):
        self.execute("baseline")
        factory.propose(Args(run_dir=self.run_dir, runtime=RUNTIME, patch=self.patch, description="Constructed patch for policy fixture"))
        self.execute("candidate")

    def test_fixture_end_to_end_requires_review_then_records_exact_accepted_policy(self):
        self.candidate()
        with self.assertRaisesRegex(ValueError,"review"):
            factory.decide(Args(run_dir=self.run_dir, runtime=RUNTIME, change_id=self.change_id, review_id=None))
        report = self.root / "review.txt"
        report.write_text("Constructed independent review fixture; not a real miner review.")
        factory.record_review(Args(run_dir=self.run_dir, runtime=RUNTIME, change_id=self.change_id, report=report,
            reviewer="Fixture reviewer", rationale="Fixture coverage and bindings checked", decision="approve"))
        replay = factory.read_json(self.run_dir / "replay.json")
        review_id = next(e["payload"]["review_id"] for e in replay["events"] if e["payload"]["kind"] == "review_recorded")
        factory.decide(Args(run_dir=self.run_dir, runtime=RUNTIME, change_id=self.change_id, review_id=review_id))
        factory.verify_run(Args(run_dir=self.run_dir,runtime=RUNTIME))
        replay = factory.read_json(self.run_dir / "replay.json")
        self.assertEqual(replay["status"], "completed")
        self.assertEqual(replay["events"][-1]["payload"]["decision"]["kind"], "accepted")
        with self.assertRaises(ValueError):
            kernel.Replay(self.run_dir)

    def test_rehashed_nested_observation_cannot_replace_retained_native_output(self):
        self.execute("baseline")
        with kernel.Replay(self.run_dir) as replay:
            cfg = factory.configuration(replay)
            finished = factory.payloads(replay,"execution_finished")[0]
            evidence = factory.artifact_json(replay,finished["evidence_id"])
            evidence["observation"]["data"]["rows"] = 999
            finished["evidence_id"] = replay.artifact(kernel.encode_json(evidence),raw=True)
            with self.assertRaisesRegex(ValueError,"retained native output"):
                factory.verify_domain(replay,cfg)

    def test_feedback_strength_and_worker_invocation_cannot_be_rebound(self):
        self.execute("baseline")
        with kernel.Replay(self.run_dir) as replay:
            cfg = factory.configuration(replay)
            feedback = factory.strong_feedbacks(replay)[0]
            feedback["bounded_claim"] = "Invented gameplay correctness"
            with self.assertRaisesRegex(ValueError,"attribution"):
                factory.verify_domain(replay,cfg)
            feedback["bounded_claim"] = coverage.CLAIM
            started = factory.payloads(replay,"execution_started")[0]
            request = factory.artifact_json(replay,started["request_id"])
            request["command"] += ["--unknown-flag"]
            started["request_id"] = replay.artifact(request)
            with self.assertRaisesRegex(ValueError,"invocation"):
                factory.verify_domain(replay,cfg)

    def test_two_different_failing_outputs_do_not_claim_repeatable_failure(self):
        self.execute("baseline")
        with kernel.Replay(self.run_dir) as replay:
            cfg = factory.configuration(replay)
            case = cfg["cases"][0]
            expected = factory.artifact_json(replay,case["expectation_id"])
            report_a = native_report(expected)
            report_a["card_frequency"] = []
            report_b = copy.deepcopy(report_a)
            report_b["card_frequency"] = [{"name": "Other wrong output", "count": 4}]
            runs = [{"status": "completed", "evidence_id": str(i)*64, "observation": coverage.decode_native(kernel.encode_json(report))}
                    for i,report in enumerate((report_a,report_b))]
            receipt = factory.evaluate_runs(case,expected,runs,"fixture-manifest",cfg)
            self.assertFalse(receipt["data"]["repeatable"])
            self.assertEqual(receipt["data"]["result"],"inconclusive")

    def test_source_and_build_tampering_fail_before_executions(self):
        valid = attestation(self.worker)
        for mutate in [lambda a:a.update(source_tree_clean=1), lambda a:a.update(binary_sha256=True),
                       lambda a:a["source_files_after"].update({"Cargo.lock":"9"*64}),
                       lambda a:a.update(base_revision="d"*40), lambda a:a.update(program="Phase engine"),
                       lambda a:a.update(environment={"jobs":1})]:
            value = copy.deepcopy(valid)
            mutate(value)
            with self.subTest(value=value), self.assertRaises(ValueError):
                factory.validate_build(value,BASE,None)
        with kernel.Replay(self.run_dir) as replay:
            cfg = factory.configuration(replay)
            expected = factory.artifact_json(replay,cfg["cases"][0]["expectation_id"])
            expected["normalization"]["cast_occurrences"] += 1
            cfg["cases"][0]["expectation_id"] = replay.artifact(expected)
            config_event = next(p for p in factory.payloads(replay,"source_imported") if p["source"]["provider"] == factory.CONFIG_PROVIDER)
            config_event["source"]["snapshot_id"] = replay.artifact(cfg)
            with self.assertRaisesRegex(ValueError,"recompute"):
                factory.configuration(replay)

    def test_configuration_requires_exact_installed_adapter_identity(self):
        with kernel.Replay(self.run_dir) as replay:
            cfg = factory.configuration(replay)
            cfg["adapter_sha256"] = replay.artifact(b"different adapter implementation",raw=True)
            config_event = next(p for p in factory.payloads(replay,"source_imported") if p["source"]["provider"] == factory.CONFIG_PROVIDER)
            config_event["source"]["snapshot_id"] = replay.artifact(cfg)
            with self.assertRaisesRegex(ValueError,"policy adapter"):
                factory.configuration(replay)

    def test_source_evaluator_and_map_are_portable_without_private_bootstrap(self):
        factory.verify_run(Args(run_dir=self.run_dir,runtime=RUNTIME))
        exported = self.root / "bundle.json"
        subprocess.run([str(RUNTIME),"export",str(self.run_dir),"--output",str(exported)],check=True,stdout=subprocess.DEVNULL)
        bundle = json.loads(exported.read_bytes())
        contents = "\n".join(bundle["artifact_contents"].values())
        self.assertNotIn("materialized/",contents)
        self.assertNotIn("phase_card_data",contents)
        self.assertIn("Constructed unit-test data",contents)


if __name__ == "__main__":
    unittest.main()
