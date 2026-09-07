"""Completed-session provenance with explicitly private synthetic test inputs."""
import json
import subprocess
import sys
from types import SimpleNamespace
import unittest

from test_factory_recording import RecorderFixture, ROOT, RUNTIME
import record_agent_work as agent_work
from factory_replay import sha256


CURRENT_USAGE = {"input_tokens": 3307670, "cached_input_tokens": 3081344,
                 "cache_write_input_tokens": 0, "output_tokens": 28488,
                 "reasoning_output_tokens": 8104}


def session_bytes(usages):
    events = [{"type": "thread.started", "thread_id": "private-thread-test-identity"}]
    for usage in usages:
        events.extend([
            {"type": "turn.started"},
            {"type": "item.completed", "item": {"id": "private-item", "type": "agent_message",
                                                   "text": "PRIVATE_SESSION_CONTENT_MUST_NOT_BE_PUBLISHED"}},
            {"type": "turn.completed", **({"usage": usage} if usage is not None else {})}])
    return b"\n".join(json.dumps(event).encode() for event in events) + b"\n"


class SessionUsageTests(unittest.TestCase):
    def test_current_cli_usage_keeps_subsets_separate_and_billing_unknown(self):
        usage = agent_work.parse_session(session_bytes([CURRENT_USAGE]))
        for name, value in CURRENT_USAGE.items():
            self.assertEqual(usage[name], value)
        self.assertEqual(usage["total_tokens"], CURRENT_USAGE["input_tokens"] + CURRENT_USAGE["output_tokens"])
        self.assertEqual(usage["uncached_input_tokens"], 226326)
        self.assertIsNone(usage["billed_tokens"])
        self.assertEqual(usage["completed_turns"], 1)

    def test_current_cli_startup_item_before_first_turn_is_supported(self):
        records = session_bytes([CURRENT_USAGE]).splitlines()
        records.insert(1, b'{"type":"item.completed","item":{"type":"fixture_startup_notice","text":"private startup fixture"}}')
        usage = agent_work.parse_session(b"\n".join(records) + b"\n")
        self.assertEqual(usage["input_tokens"], CURRENT_USAGE["input_tokens"])
        self.assertEqual(usage["completed_turns"], 1)

    def test_multiple_completed_turns_sum_usage_once(self):
        usage = agent_work.parse_session(session_bytes([
            {"input_tokens": 10, "cached_input_tokens": 8, "output_tokens": 4, "reasoning_output_tokens": 2},
            {"input_tokens": 20, "cached_input_tokens": 18, "output_tokens": 3, "reasoning_output_tokens": 1}]))
        self.assertEqual((usage["input_tokens"], usage["output_tokens"], usage["total_tokens"]), (30, 7, 37))
        self.assertEqual((usage["cached_input_tokens"], usage["reasoning_output_tokens"]), (26, 3))
        self.assertIsNone(usage["cache_write_input_tokens"])

    def test_missing_turn_usage_does_not_become_zero_or_partial_total(self):
        usage = agent_work.parse_session(session_bytes([CURRENT_USAGE, None]))
        self.assertEqual(usage["turns_with_usage"], 1)
        self.assertEqual(usage["completed_turns"], 2)
        self.assertIsNone(usage["input_tokens"])
        self.assertIsNone(usage["output_tokens"])
        self.assertIsNone(usage["total_tokens"])
        self.assertEqual(usage["per_turn"], [CURRENT_USAGE, None])

    def test_malformed_incomplete_or_combined_sessions_are_rejected(self):
        complete = session_bytes([CURRENT_USAGE])
        cases = [b"", b"not JSON\n", complete + complete,
                 complete + b'{"type":"turn.started"}\n',
                 b'{"type":"turn.completed","usage":{}}\n',
                 complete.replace(b'"turn.completed"', b'"turn.failed"'),
                 complete + b'{"type":"turn.completed"}\n',
                 complete.replace(b'"item": {', b'"not_an_item": {'),
                 complete.replace(b'"output_tokens": 28488', b'"output_tokens": 28488,"output_tokens": 1')]
        for index, content in enumerate(cases):
            with self.subTest(index=index):
                with self.assertRaises(ValueError):
                    agent_work.parse_session(content)

    def test_invalid_or_incompatible_usage_is_rejected(self):
        for replacement in [True, -1, 1.5, 2**64, "4"]:
            usage = {**CURRENT_USAGE, "input_tokens": replacement}
            with self.subTest(replacement=replacement):
                with self.assertRaises(ValueError):
                    agent_work.parse_session(session_bytes([usage]))
        for usage in [{**CURRENT_USAGE, "unknown_billed_count": 4},
                      {**CURRENT_USAGE, "cached_input_tokens": CURRENT_USAGE["input_tokens"] + 1},
                      {**CURRENT_USAGE, "reasoning_output_tokens": CURRENT_USAGE["output_tokens"] + 1}]:
            with self.assertRaises(ValueError):
                agent_work.parse_session(session_bytes([usage]))


@unittest.skipUnless(RUNTIME.is_file(), "set FACTORY_RUNTIME to the built standalone runtime")
class AgentWorkRecordingTests(RecorderFixture):
    def setUp(self):
        super().setUp()
        self.prompt = self.root / "private-prompt.txt"
        self.report = self.root / "private-report.md"
        self.session = self.root / "private-session.jsonl"
        self.prompt.write_bytes(b"PRIVATE_PROMPT_SECRET_MUST_NOT_BE_PUBLISHED")
        self.report.write_bytes(b"PRIVATE_REPORT_CONTENT_MUST_NOT_BE_PUBLISHED")
        self.session.write_bytes(session_bytes([CURRENT_USAGE]))
        self.args = SimpleNamespace(run_dir=self.directory, runtime=RUNTIME, prompt=self.prompt,
                                    report=self.report, session=self.session, model="gpt-6-astra",
                                    role="repair_plan", reasoning_effort="ultra", summary="Public planning summary.",
                                    stage="changes", feedback_id=[], feedback_supplied_at_start=False)

    def record(self):
        self.replay.lock.close()
        result = agent_work.record_work(self.args)
        self.replay.value = json.loads(self.replay.path.read_bytes())
        return result

    def summary(self, result):
        path = self.replay.value["artifacts"][result["summary_id"]]["path"]
        return json.loads((self.directory / path).read_bytes())

    def feedback(self):
        case_id = self.case({"fixture": "agent feedback reference"})
        return self.replay.feedback(case_id, [], {"fixture": "weak signal"}, evaluator="Fixture evaluator",
                                    evaluator_version="v1", strength="weak", method="Explicit test fixture",
                                    claim="A test signal only", result="inconclusive", summary="Constructed feedback")

    def test_cli_records_public_hashes_and_measured_compute_without_private_contents(self):
        self.replay.lock.close()
        completed = subprocess.run([
            sys.executable, str(ROOT / "scripts/record_agent_work.py"),
            "--run-dir", str(self.directory), "--runtime", str(RUNTIME), "--session", str(self.session),
            "--prompt", str(self.prompt), "--report", str(self.report), "--model", self.args.model,
            "--role", self.args.role, "--summary", self.args.summary], check=True, capture_output=True)
        result = json.loads(completed.stdout)
        self.replay.value = json.loads(self.replay.path.read_bytes())
        summary = self.summary(result)
        self.assertEqual(result["status"], "recorded")
        for name, path in [("prompt", self.prompt), ("report", self.report), ("session", self.session)]:
            self.assertEqual(summary[name + "_sha256"], sha256(path.read_bytes()))
        self.assertIsNone(summary["wall_ms"])
        self.assertIsNone(summary["completed_at"])
        usage = self.replay.value["events"][-1]["payload"]["usage"]
        self.assertEqual(usage["measurement"], "measured")
        self.assertEqual(usage["worker"], "codex-agent:" + result["summary_id"])
        self.assertEqual(usage["input_tokens"], CURRENT_USAGE["input_tokens"])
        self.assertEqual(usage["output_tokens"], CURRENT_USAGE["output_tokens"])
        self.assertIsNone(usage["wall_ms"])
        self.assertIsNone(usage["execution_id"])
        for path in self.directory.rglob("*"):
            if path.is_file():
                data = path.read_bytes()
                self.assertNotIn(b"PRIVATE_", data, str(path))
                self.assertNotIn(b"private-thread-test-identity", data, str(path))
                self.assertNotIn(str(self.root).encode(), data, str(path))
        subprocess.run([str(RUNTIME), "verify", str(self.directory)], check=True, capture_output=True)

    def test_no_usage_records_summary_without_an_empty_compute_event(self):
        self.session.write_bytes(session_bytes([None]))
        result = self.record()
        self.assertFalse(result["compute_recorded"])
        self.assertEqual([event["payload"]["kind"] for event in self.replay.value["events"]], ["source_imported"])
        summary = self.summary(result)
        self.assertIsNone(summary["usage"]["input_tokens"])
        self.assertIsNone(summary["usage"]["output_tokens"])
        self.assertIsNone(summary["usage"]["billed_tokens"])

    def test_duplicate_work_does_not_rewrite_snapshot_or_count_compute_again(self):
        original = self.record()
        before = self.replay.path.read_bytes()
        duplicate = self.record()
        self.assertEqual(duplicate, {"status": "duplicate", "summary_id": original["summary_id"], "compute_recorded": False})
        self.assertEqual(self.replay.path.read_bytes(), before)
        self.assertEqual(sum(event["payload"]["kind"] == "compute_recorded"
                             for event in self.replay.value["events"]), 1)
        self.args.summary = "Changed attribution for the same finished work."
        with self.assertRaisesRegex(ValueError, "already recorded"):
            self.record()
        self.assertEqual(self.replay.path.read_bytes(), before)

    def test_reused_report_or_session_alone_cannot_double_count_compute(self):
        self.record()
        before = self.replay.path.read_bytes()
        original = self.session.read_bytes()
        self.session.write_bytes(session_bytes([{**CURRENT_USAGE, "output_tokens": 30000}]))
        with self.assertRaisesRegex(ValueError, "already recorded"):
            self.record()
        self.session.write_bytes(original)
        self.report.write_bytes(b"A different retained report for the same private session.")
        with self.assertRaisesRegex(ValueError, "already recorded"):
            self.record()
        self.assertEqual(self.replay.path.read_bytes(), before)

    def test_feedback_defaults_to_cross_reference_and_start_assertion_is_explicit(self):
        identity = self.feedback()
        self.args.feedback_id = [identity]
        first = self.record()
        self.assertEqual(self.summary(first)["feedback_links"], [{"feedback_id": identity, "relationship": "cross_reference"}])
        self.report.write_bytes(b"Another distinct report.")
        self.session.write_bytes(session_bytes([{**CURRENT_USAGE, "output_tokens": 30000}]))
        self.args.feedback_supplied_at_start = True
        second = self.record()
        self.assertEqual(self.summary(second)["feedback_links"], [
            {"feedback_id": identity, "relationship": "caller_asserted_supplied_at_start"}])
        self.assertIn("supplied by the caller", self.summary(second)["attribution"])

    def test_invalid_links_and_terminal_runs_do_not_publish(self):
        before = self.replay.path.read_bytes()
        self.args.feedback_id = ["a" * 64]
        with self.assertRaisesRegex(ValueError, "not recorded"):
            self.record()
        self.assertEqual(self.replay.path.read_bytes(), before)
        self.args.feedback_id = []
        self.replay.finish("cancelled")
        before = self.replay.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "terminal"):
            self.record()
        self.assertEqual(self.replay.path.read_bytes(), before)

    def test_prospective_verification_failure_publishes_neither_summary_nor_compute(self):
        verifier = self.root / "reject-prospective-verifier"
        verifier.write_text(
            f"#!{sys.executable}\n"
            "import json, pathlib, subprocess, sys\n"
            f"subprocess.run([{str(RUNTIME)!r}, *sys.argv[1:]], check=True)\n"
            "path = pathlib.Path(sys.argv[2])\n"
            "if path.name.startswith('.agent-work-'):\n"
            "    value = json.loads(path.read_bytes())\n"
            "    assert [e['payload']['kind'] for e in value['events'][-2:]] == ['source_imported', 'compute_recorded']\n"
            "    sys.exit(9)\n")
        verifier.chmod(0o700)
        self.args.runtime = verifier
        before = self.replay.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "native replay verification failed"):
            self.record()
        self.assertEqual(self.replay.path.read_bytes(), before)
        self.assertEqual(list(self.directory.glob(".agent-work-*")), [])
        self.args.runtime = RUNTIME
        self.assertEqual(self.record()["status"], "recorded")
