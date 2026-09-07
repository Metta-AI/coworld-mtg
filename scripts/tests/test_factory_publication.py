"""Publication and attestation regressions using explicitly constructed fixtures."""
import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest

from test_factory_recording import RecorderFixture, RUNTIME
import factory_replay as recorder
import mana_library_oracle as oracle
import scryfall_factory as factory
import scryfall_source


@unittest.skipUnless(RUNTIME.is_file(), "set FACTORY_RUNTIME to the built standalone runtime")
class PublicationTests(RecorderFixture):
    def test_invalid_event_never_replaces_the_published_snapshot(self):
        before = self.replay.path.read_bytes()
        events = copy.deepcopy(self.replay.value["events"])
        with self.assertRaises(subprocess.CalledProcessError):
            self.replay.event(
                "execute", "execution_finished", validation_runtime=RUNTIME,
                execution_id="never-started", status="error", evidence_id=None,
                trace_ids=[], detail="Constructed invalid lifecycle transition")
        self.assertEqual(self.replay.path.read_bytes(), before)
        self.assertEqual(self.replay.value["events"], events)
        self.assertFalse((self.directory / ".pending-replay.json").exists())
        # A rejected command must leave the writer usable for a valid next event.
        self.case({"fixture": "valid next event"})
        subprocess.run([str(RUNTIME), "verify", str(self.directory)], check=True, capture_output=True)

    def prepare_gate_run(self, candidate_classification=False):
        self.cards = []
        self.case_ids = []
        for index in range(3):
            card = {"object": "card", "id": f"fixture-printing-{index}",
                    "oracle_id": f"fixture-oracle-{index}", "name": f"Gate fixture {index}",
                    "layout": "normal", "games": ["paper"], "legalities": {"vintage": "legal"},
                    "type_line": "Artifact", "oracle_text": "{T}, Mill a card: Add {C}."}
            self.cards.append(card)
            self.case_ids.append(self.case(card))
        plan = {"case_id": self.case_ids[0], "regression_case_ids": [self.case_ids[1]],
                "holdout_case_ids": [self.case_ids[2]]}
        plan_id = self.replay.artifact(plan)
        self.replay.event("gates", "acceptance_plan_frozen", plan_id=plan_id, plan=plan)
        evaluator_id = self.replay.artifact(Path(oracle.__file__).read_bytes(), raw=True, media_type="text/x-python")
        source_id = self.replay.artifact(Path(scryfall_source.__file__).read_bytes(), raw=True, media_type="text/x-python")
        report_id = self.replay.artifact({"producer": {"script_sha256": source_id}})
        rules_id = self.replay.artifact(b"Explicit policy publication test fixture", raw=True)
        policy = {"kind": "source-aligned-mana-classification-v1", "scope": factory.CLAIM,
                  "evaluator_sha256": evaluator_id, "rules_sha256": rules_id,
                  "plan_id": plan_id, "repetitions": 2}
        self.cfg = {"cases": [{"case_id": identity, "source_contract": oracle.source_contracts(card)}
                              for identity, card in zip(self.case_ids, self.cards)],
                    "evaluator_sha256": evaluator_id, "rules_sha256": rules_id,
                    "discovery_report_id": report_id, "plan_id": plan_id,
                    "policy_id": self.replay.artifact(policy)}
        cfg_id = self.replay.artifact(self.cfg)
        self.replay.event("sources", "source_imported", source={
            "snapshot_id": cfg_id, "provider": factory.CONFIG_PROVIDER,
            "url": "urn:test:policy-configuration", "retrieved_at": "2026-09-07T00:00:00Z",
            "description": "Constructed policy publication fixture"})
        self.baseline_build = self.attested_build("fixture-base")
        self.baseline_feedback = self.record_pair(0, self.baseline_build, "baseline", True)
        self.assertEqual(self.feedback(self.baseline_feedback)["result"], "violated")
        self.change_id = self.replay.artifact(b"diff --git a/fixture b/fixture\n", raw=True, media_type="text/x-diff")
        self.replay.event("changes", "change_proposed", change_id=self.change_id,
                          description="Constructed candidate change", base_revision="fixture-base",
                          motivating_feedback_ids=[self.baseline_feedback])
        self.candidate_build = self.attested_build("fixture-candidate", self.change_id)
        self.candidate_feedbacks = [self.record_pair(i, self.candidate_build, f"candidate-{i}",
                                                       candidate_classification if i == 0 else False,
                                                       self.change_id) for i in range(3)]
        factory.verify_domain(self.replay, self.cfg)
        subprocess.run([str(RUNTIME), "verify", str(self.directory)], check=True, capture_output=True)

    def attested_build(self, revision, change_id=None):
        # Distinct recorded bytes identify these intentionally synthetic workers;
        # no production build or execution is claimed by this policy unit fixture.
        binary_hash = recorder.sha256(revision.encode())
        attestation = {"binary_sha256": binary_hash, "phase_revision": revision,
                       "declared_phase_revision": "fixture-pin", "command": ["fixture-compiler"],
                       "environment": {}, "source_files": {}, "harness_revision": "fixture-harness"}
        if change_id:
            attestation.update(phase_base_revision="fixture-base", phase_patch_sha256=change_id)
        build = {"program": "Fixture parser", "source_revision": revision,
                 "binary_sha256": binary_hash, "command": attestation["command"],
                 "environment": {}, "attestation_id": self.replay.artifact(attestation)}
        identity = self.replay.artifact(build)
        self.replay.event("execute", "build_recorded", build_id=identity, build=build)
        return identity

    def feedback(self, identity):
        return next(e["payload"]["feedback"] for e in self.replay.value["events"]
                    if e["payload"]["kind"] == "feedback_recorded"
                    and e["payload"]["feedback"]["feedback_id"] == identity)

    def record_pair(self, index, build_id, prefix, classification, change_id=None):
        card, case_id = self.cards[index], self.case_ids[index]
        build = factory.artifact_json(self.replay, build_id)
        ability = {"kind": "Activated", "cost": {"type": "Composite", "costs": [
                       {"type": "Tap"}, {"type": "Mill", "count": 1}]},
                   "effect": {"type": "Mana", "produced": {"type": "Colorless", "count": {"type": "Fixed", "value": 1}}},
                   "condition": None, "duration": None, "target_prompt": None,
                   "forward_result": False, "optional": False, "optional_targeting": False,
                   "sub_ability": None}
        if classification is not None:
            ability["is_mana_ability"] = classification
        observation = {"status": "parsed", "oracle_id": card["oracle_id"], "card_id": card["id"],
                       "phase_revision": "fixture-pin", "parsed": {"abilities": [ability],
                       "extractedKeywords": [], "replacements": [], "statics": [], "triggers": []}}
        runs = []
        for repeat in range(2):
            execution_id = f"{prefix}-{repeat}"
            input_id = self.replay.artifact(json.dumps(card).encode() + b"\n", raw=True)
            request = {"protocol": "oracle-probe-jsonl-v1", "case_id": case_id, "build_id": build_id,
                       "worker_sha256": build["binary_sha256"], "input_sha256": input_id}
            request_id = self.replay.artifact(request)
            self.replay.event("execute", "execution_started", execution_id=execution_id,
                              case_id=case_id, request_id=request_id, build_id=build_id, change_id=change_id)
            output_id = self.replay.artifact(json.dumps(observation).encode() + b"\n", raw=True,
                                             media_type="application/x-ndjson")
            evidence_id = self.replay.artifact({"request_id": request_id, "worker_sha256": build["binary_sha256"],
                                               "observation": observation, "output_artifact_id": output_id,
                                               "exit_code": 0, "timed_out": False,
                                               "detail": None, "fixture_repeat": repeat})
            self.replay.event("execute", "execution_finished", execution_id=execution_id,
                              status="completed", evidence_id=evidence_id, trace_ids=[output_id], detail=None)
            runs.append({"execution_id": execution_id, "evidence_id": evidence_id,
                         "status": "completed", "observation": observation})
        receipt = factory.evaluate_runs(case_id, card, runs, build["source_revision"], self.cfg,
                                        declared_revision="fixture-pin")
        return self.replay.feedback(case_id, [r["execution_id"] for r in runs], receipt,
                                    evaluator="Independent source-aligned CR605.1a grammar",
                                    evaluator_version=self.cfg["evaluator_sha256"], strength="strong",
                                    method="Constructed publication fixture", claim=factory.CLAIM,
                                    result=receipt["result"], summary="Constructed policy gate result")

    def add_review(self, candidate_id):
        review = {"plan_id": self.cfg["plan_id"], "baseline_receipt_id": self.baseline_feedback,
                  "candidate_receipt_id": candidate_id, "reviewer": "Fixture independent reviewer",
                  "rationale": "Constructed independent approval for a publication regression test",
                  "decision": "approve"}
        identity = self.replay.artifact(review)
        self.replay.event("review", "review_recorded", review_id=identity, review=review)
        return identity

    def decide(self, review_id=None, *, continue_on_rejection=False):
        self.replay.lock.close()
        args = SimpleNamespace(run_dir=self.directory, runtime=RUNTIME,
                               change_id=self.change_id, review_id=review_id,
                               continue_on_rejection=continue_on_rejection)
        with contextlib.redirect_stdout(io.StringIO()):
            factory.decide(args)

    def test_invalid_review_is_not_published_by_the_review_command(self):
        self.prepare_gate_run()
        report = self.root / "review-report.txt"
        report.write_text("Explicit independent review fixture with nonempty findings.\n")
        before = self.replay.path.read_bytes()
        self.replay.lock.close()
        for reviewer, rationale in [("   ", "Constructed review fixture"),
                                    ("Fixture reviewer", "   ")]:
            with self.subTest(reviewer=reviewer, rationale=rationale):
                args = SimpleNamespace(run_dir=self.directory, runtime=RUNTIME,
                                       change_id=self.change_id, report=report,
                                       reviewer=reviewer, rationale=rationale, decision="approve")
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises((ValueError, subprocess.CalledProcessError)):
                        factory.record_review(args)
                self.assertEqual(self.replay.path.read_bytes(), before)
                self.assertFalse((self.directory / ".pending-replay.json").exists())
        subprocess.run([str(RUNTIME), "verify", str(self.directory)], check=True, capture_output=True)

    def test_duplicate_proposal_is_rejected_without_changing_the_snapshot(self):
        self.prepare_gate_run()
        patch = self.root / "existing-change.patch"
        patch.write_bytes((self.directory / "artifacts" / self.change_id).read_bytes())
        before = self.replay.path.read_bytes()
        self.replay.lock.close()
        args = SimpleNamespace(run_dir=self.directory, runtime=RUNTIME, patch=patch,
                               description="Duplicate proposal test fixture")
        with self.assertRaisesRegex(ValueError, "already been proposed"):
            factory.propose(args)
        self.assertEqual(self.replay.path.read_bytes(), before)
        self.assertEqual(sum(e["payload"]["kind"] == "change_proposed"
                             for e in json.loads(before)["events"]), 1)

    def test_review_for_another_case_cannot_publish_an_accepted_decision(self):
        self.prepare_gate_run()
        # This is a valid recorded review of an existing receipt, but it approves
        # the regression case instead of the repaired target.
        wrong_review = self.add_review(self.candidate_feedbacks[1])
        before = self.replay.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "review does not bind"):
            self.decide(wrong_review)
        self.assertEqual(self.replay.path.read_bytes(), before)
        self.assertFalse(any(e["payload"]["kind"] == "decision_recorded"
                             for e in json.loads(before)["events"]))
        self.assertFalse((self.directory / ".pending-replay.json").exists())

    def test_inconclusive_gate_records_rejection_without_inventing_a_violation(self):
        self.prepare_gate_run(candidate_classification=None)
        target_feedback = self.feedback(self.candidate_feedbacks[0])
        self.assertEqual(target_feedback["result"], "inconclusive")
        original_receipt = factory.artifact_json(self.replay, target_feedback["feedback_id"])
        self.assertEqual(original_receipt["evaluations"][0]["verdict"], "inconclusive")
        self.decide()
        saved = json.loads(self.replay.path.read_bytes())
        decisions = [e["payload"]["decision"] for e in saved["events"]
                     if e["payload"]["kind"] == "decision_recorded"]
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0]["kind"], "rejected")
        self.assertIn(self.case_ids[0], decisions[0]["reasons"][0])
        saved_feedback = next(e["payload"]["feedback"] for e in saved["events"]
                              if e["payload"]["kind"] == "feedback_recorded"
                              and e["payload"]["feedback"]["feedback_id"] == target_feedback["feedback_id"])
        self.assertEqual(saved_feedback["result"], "inconclusive")
        self.assertEqual(saved["status"], "completed")
        terminal_bytes = self.replay.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "terminal"):
            self.decide(continue_on_rejection=True)
        self.assertEqual(self.replay.path.read_bytes(), terminal_bytes)
        subprocess.run([str(RUNTIME), "verify", str(self.directory)], check=True, capture_output=True)
        with contextlib.redirect_stdout(io.StringIO()):
            factory.verify_run(SimpleNamespace(runtime=RUNTIME, run_dir=self.directory))

    def test_rejected_patch_can_precede_a_distinct_patch_under_the_same_frozen_plan(self):
        self.prepare_gate_run(candidate_classification=True)
        original_change = self.change_id
        frozen_ids = [self.cfg["plan_id"], self.cfg["policy_id"], self.cfg["evaluator_sha256"],
                      self.cfg["rules_sha256"], self.baseline_feedback, *self.case_ids]
        frozen_bytes = {identity: (self.directory / self.replay.value["artifacts"][identity]["path"]).read_bytes()
                        for identity in frozen_ids}
        self.replay.lock.close()
        # Exercise the public CLI flag, including prospective native validation.
        completed = subprocess.run([
            sys.executable, str(Path(factory.__file__)), "decide", "--run-dir", str(self.directory),
            "--runtime", str(RUNTIME), "--change-id", self.change_id, "--continue-on-rejection"],
            check=True, capture_output=True)
        self.assertEqual(json.loads(completed.stdout)["result"], "rejected")
        first = json.loads(self.replay.path.read_bytes())
        self.assertEqual(first["status"], "running")
        rejection = first["events"][-1]["payload"]
        self.assertEqual(rejection["decision"]["kind"], "rejected")
        self.assertEqual(rejection["plan_id"], self.cfg["plan_id"])
        # Continuing must not make the existing change eligible for another decision.
        before = self.replay.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "already has an immutable decision"):
            self.decide(continue_on_rejection=True)
        self.assertEqual(self.replay.path.read_bytes(), before)

        patch = self.root / "distinct-combined-repair.patch"
        patch.write_bytes(b"diff --git a/fixture b/fixture\n+distinct combined repair fixture\n")
        with contextlib.redirect_stdout(io.StringIO()):
            factory.propose(SimpleNamespace(run_dir=self.directory, runtime=RUNTIME, patch=patch,
                                            description="Distinct next repair against the same baseline"))
        self.change_id = recorder.sha256(patch.read_bytes())
        self.assertNotEqual(self.change_id, original_change)
        self.replay = recorder.Replay(self.directory)
        self.addCleanup(self.replay.lock.close)
        next_build = self.attested_build("fixture-combined-candidate", self.change_id)
        next_feedback = [self.record_pair(index, next_build, f"next-candidate-{index}", False,
                                          self.change_id) for index in range(3)]
        review_id = self.add_review(next_feedback[0])
        self.decide(review_id, continue_on_rejection=True)
        final = json.loads(self.replay.path.read_bytes())
        self.assertEqual(final["status"], "completed")
        self.assertEqual(final["events"][:len(first["events"])], first["events"])
        self.assertEqual(final["target"], first["target"])
        decisions = [event["payload"] for event in final["events"]
                     if event["payload"]["kind"] == "decision_recorded"]
        self.assertEqual([item["change_id"] for item in decisions], [original_change, self.change_id])
        self.assertEqual([item["decision"]["kind"] for item in decisions], ["rejected", "accepted"])
        self.assertEqual({item["plan_id"] for item in decisions}, {self.cfg["plan_id"]})
        self.assertEqual(sum(event["payload"]["kind"] == "acceptance_plan_frozen"
                             for event in final["events"]), 1)
        for identity, original in frozen_bytes.items():
            self.assertEqual((self.directory / final["artifacts"][identity]["path"]).read_bytes(), original)
        with contextlib.redirect_stdout(io.StringIO()):
            factory.verify_run(SimpleNamespace(runtime=RUNTIME, run_dir=self.directory))

    def test_continue_flag_cannot_keep_an_accepted_run_open_or_reopen_it(self):
        self.prepare_gate_run()
        review_id = self.add_review(self.candidate_feedbacks[0])
        self.decide(review_id, continue_on_rejection=True)
        saved = self.replay.path.read_bytes()
        self.assertEqual(json.loads(saved)["status"], "completed")
        with self.assertRaisesRegex(ValueError, "terminal"):
            self.decide(review_id, continue_on_rejection=True)
        self.assertEqual(self.replay.path.read_bytes(), saved)

    def test_valid_review_can_publish_the_exact_accepted_decision(self):
        self.prepare_gate_run()
        review_id = self.add_review(self.candidate_feedbacks[0])
        self.decide(review_id)
        saved = json.loads(self.replay.path.read_bytes())
        decision = next(e["payload"]["decision"] for e in saved["events"]
                        if e["payload"]["kind"] == "decision_recorded")
        self.assertEqual(decision["kind"], "accepted")
        self.assertEqual(decision["review_id"], review_id)
        self.assertEqual(decision["baseline_receipt_id"], self.baseline_feedback)
        self.assertEqual(decision["candidate_receipt_id"], self.candidate_feedbacks[0])
        self.assertEqual(decision["gate_receipt_ids"], self.candidate_feedbacks[1:])
        subprocess.run([str(RUNTIME), "verify", str(self.directory)], check=True, capture_output=True)


class AttestationMappingTests(RecorderFixture):
    def checked_fixture_build(self, *, dirty=False, pinned=False):
        build = self.root / "checked-build"
        (build / "source/crates/phase-bridge/src").mkdir(parents=True)
        worker = build / "worker"
        worker.write_text(
            f"#!{sys.executable}\n"
            "import pathlib, sys\n"
            "assert sys.argv[1:4] == ['case', 'build-check', '--build']\n"
            "pathlib.Path(sys.argv[4], 'check-was-invoked').write_text('fixture check')\n")
        worker.chmod(0o700)
        actual, declared, base = "a" * 40, "b" * 40, "c" * 40
        (build / "source/crates/phase-bridge/src/lib.rs").write_text(
            f'pub const PHASE_REVISION: &str = "{declared}";\n')
        phase = {"kind": "pinned" if pinned else "checkout", "revision": actual,
                 "repository": "https://example.test/phase-fixture"}
        if not pinned:
            phase.update(base_revision=base, worktree_clean=not dirty,
                         patch_sha256=recorder.sha256(b"fixture patch"), source_files={"fixture.rs": "d" * 64})
        original = {"binary_sha256": recorder.sha256(worker.read_bytes()), "phase": phase,
                    "harness_revision": "fixture-harness", "harness_source_files": {"adapter.rs": "e" * 64},
                    "command": ["fixture-compiler"], "build_environment": {"FIXTURE": "true"},
                    "compiler": "Explicit test compiler fixture"}
        original_bytes = json.dumps(original, indent=2).encode() + b"\n"
        (build / "build.json").write_bytes(original_bytes)
        return build, original, original_bytes, declared

    def test_dirty_checkout_attestation_preserves_original_receipt_and_separates_pin(self):
        build, original, original_bytes, declared = self.checked_fixture_build(dirty=True)
        output = self.root / "attestation.json"
        with contextlib.redirect_stdout(io.StringIO()):
            factory.attest_case_build(SimpleNamespace(build_dir=build, output=output))
        mapped = json.loads(output.read_bytes())
        self.assertTrue((build / "check-was-invoked").exists())
        self.assertEqual(mapped["original_build"], original)
        self.assertEqual(mapped["original_build_sha256"], recorder.sha256(original_bytes))
        self.assertEqual(mapped["declared_phase_revision"], declared)
        self.assertEqual(mapped["phase_revision"], original["phase"]["revision"] + "+patch:" + original["phase"]["patch_sha256"])
        self.assertEqual(mapped["phase_patch_sha256"], original["phase"]["patch_sha256"])
        self.assertEqual(mapped["phase_base_revision"], original["phase"]["base_revision"])
        self.assertEqual(mapped["phase_source_files"], original["phase"]["source_files"])

    def test_pinned_build_has_no_invented_dirty_patch_suffix(self):
        build, original, _, declared = self.checked_fixture_build(pinned=True)
        output = self.root / "attestation.json"
        with contextlib.redirect_stdout(io.StringIO()):
            factory.attest_case_build(SimpleNamespace(build_dir=build, output=output))
        mapped = json.loads(output.read_bytes())
        self.assertEqual(mapped["phase_revision"], original["phase"]["revision"])
        self.assertEqual(mapped["declared_phase_revision"], declared)
        self.assertNotIn("phase_patch_sha256", mapped)

    def test_mismatched_retained_worker_cannot_produce_an_attestation(self):
        build, original, _, _ = self.checked_fixture_build()
        original["binary_sha256"] = "0" * 64
        (build / "build.json").write_bytes(recorder.canonical(original))
        output = self.root / "attestation.json"
        with self.assertRaisesRegex(ValueError, "worker differs"):
            factory.attest_case_build(SimpleNamespace(build_dir=build, output=output))
        self.assertFalse(output.exists())
