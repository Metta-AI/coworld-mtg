#!/usr/bin/env python3
"""Record completed Codex CLI work without publishing private prompts or logs."""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time

from factory_replay import Replay, atomic_json, sha256

PROVIDER = "Codex agent work v1"
KIND = "codex_agent_work_v1"
TOKEN_FIELDS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
                "output_tokens", "reasoning_output_tokens")
U64_MAX = 2**64 - 1


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def parse_session(data):
    """Read one CLI thread, summing per-turn usage without counting subsets twice."""
    thread = None
    active = False
    usages = []
    lines = data.splitlines()
    if not lines:
        raise ValueError("session is empty")
    for index, line in enumerate(lines, 1):
        try:
            record = json.loads(line, object_pairs_hook=unique_object,
                                parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        except (ValueError, UnicodeError):
            raise ValueError(f"session line {index} is not valid finite JSON") from None
        if not isinstance(record, dict) or not isinstance(record.get("type"), str):
            raise ValueError(f"session line {index} is not a CLI event")
        kind = record["type"]
        if kind == "thread.started":
            if thread is not None or active or usages:
                raise ValueError("multiple CLI sessions cannot be combined")
            thread = record.get("thread_id")
            if not isinstance(thread, str) or not thread.strip():
                raise ValueError("session has no thread identity")
        elif kind == "turn.started":
            if thread is None or active:
                raise ValueError("invalid CLI turn ordering")
            active = True
        elif kind == "turn.completed":
            if not active:
                raise ValueError("completed CLI turn has no matching start")
            usage = record.get("usage")
            if usage is not None:
                if not isinstance(usage, dict) or set(usage) - set(TOKEN_FIELDS):
                    raise ValueError("unsupported CLI usage fields")
                for value in usage.values():
                    if type(value) is not int or not 0 <= value <= U64_MAX:
                        raise ValueError("CLI token counts must be nonnegative integers")
                for subset, total in [("cached_input_tokens", "input_tokens"),
                                      ("cache_write_input_tokens", "input_tokens"),
                                      ("reasoning_output_tokens", "output_tokens")]:
                    if subset in usage and total in usage and usage[subset] > usage[total]:
                        raise ValueError("CLI token subset exceeds its reported total")
            usages.append(usage)
            active = False
        elif kind in ("item.started", "item.updated", "item.completed"):
            if thread is None or (not active and usages):
                raise ValueError("CLI item falls outside startup or a running turn")
            if not isinstance(record.get("item"), dict):
                raise ValueError("CLI item must contain an object")
            # The current CLI also emits startup items before the first turn.
            # Item contents are private and do not establish additional usage.
        elif kind in ("turn.failed", "error"):
            raise ValueError("session contains a failed or interrupted CLI turn")
        else:
            raise ValueError(f"session line {index} uses an unsupported CLI event")
    if active or thread is None or not usages:
        raise ValueError("session does not end with completed CLI work")
    totals = {}
    for field in TOKEN_FIELDS:
        totals[field] = (sum(usage[field] for usage in usages)
                         if all(usage is not None and field in usage for usage in usages) else None)
        if totals[field] is not None and totals[field] > U64_MAX:
            raise ValueError("aggregate CLI token count exceeds the contract limit")
    total_input, cached, output = (totals[k] for k in ("input_tokens", "cached_input_tokens", "output_tokens"))
    totals.update(
        uncached_input_tokens=total_input - cached if total_input is not None and cached is not None else None,
        total_tokens=total_input + output if total_input is not None and output is not None else None,
        billed_tokens=None,
        completed_turns=len(usages),
        turns_with_usage=sum(usage is not None for usage in usages),
        per_turn=usages,
        accounting="CLI input and output totals; cached and reasoning counts are subsets, not additional tokens. Billing is unknown.")
    return totals


def verify(runtime, manifest):
    try:
        subprocess.run([str(runtime), "verify", str(manifest)], check=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError):
        # Do not echo runtime diagnostics that might include private paths/data.
        raise ValueError("native replay verification failed; no agent work was published") from None


def text_argument(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must contain public text")
    return value.strip()


def record_work(args):
    model = text_argument(args.model, "model")
    role = text_argument(args.role, "role")
    summary = text_argument(args.summary, "summary")
    reasoning = text_argument(args.reasoning_effort, "reasoning effort") if args.reasoning_effort else None
    try:
        prompt, report, session = (Path(path).read_bytes() for path in (args.prompt, args.report, args.session))
    except OSError:
        raise ValueError("a private input file could not be read") from None
    if not prompt.strip() or not report.strip():
        raise ValueError("prompt and completed report must be nonempty")
    usage = parse_session(session)
    identities = {"prompt_sha256": sha256(prompt), "report_sha256": sha256(report),
                  "session_sha256": sha256(session)}
    requested_links = list(args.feedback_id or [])
    if len(set(requested_links)) != len(requested_links) or any(
            not re.fullmatch(r"[0-9a-f]{64}", identity) for identity in requested_links):
        raise ValueError("feedback references must be distinct lowercase SHA-256 identities")
    if args.feedback_supplied_at_start and not requested_links:
        raise ValueError("a supplied-at-start assertion requires feedback references")
    relation = "caller_asserted_supplied_at_start" if args.feedback_supplied_at_start else "cross_reference"
    with Replay(args.run_dir) as replay:
        verify(args.runtime, replay.path)
        feedback_ids = {event["payload"]["feedback"]["feedback_id"] for event in replay.value["events"]
                        if event["payload"]["kind"] == "feedback_recorded"}
        if not set(requested_links) <= feedback_ids:
            raise ValueError("feedback reference is not recorded in this replay")
        if args.stage not in {stage["id"] for stage in replay.value["stages"]}:
            raise ValueError("compute stage is not in the replay topology")
        content = {"kind": KIND, "session_format": "codex-exec-jsonl", **identities,
                   "model": model, "role": role, "reasoning_effort": reasoning, "summary": summary,
                   "attribution": "Model, role, summary and start-time feedback assertions are supplied by the caller.",
                   "feedback_links": [{"feedback_id": identity, "relationship": relation}
                                      for identity in sorted(requested_links)],
                   "usage": usage, "wall_ms": None, "started_at": None, "completed_at": None,
                   "compute_stage": args.stage,
                   "privacy": "Only hashes and this public summary are retained; prompt, report and session bytes stay private."}
        for event in replay.value["events"]:
            payload = event["payload"]
            if payload["kind"] != "source_imported" or payload["source"]["provider"] != PROVIDER:
                continue
            identity = payload["source"]["snapshot_id"]
            previous = json.loads((replay.directory / replay.value["artifacts"][identity]["path"]).read_bytes())
            if not isinstance(previous, dict) or previous.get("kind") != KIND:
                raise ValueError("existing agent-work record has an incompatible format")
            if (previous.get("report_sha256") == identities["report_sha256"] or
                    previous.get("session_sha256") == identities["session_sha256"]):
                if previous != content:
                    raise ValueError("this report or session is already recorded with different attribution")
                return {"status": "duplicate", "summary_id": identity, "compute_recorded": False}
        original = copy.deepcopy(replay.value)
        temporary = None
        try:
            summary_id = replay.artifact(content)
            now = datetime.now(timezone.utc).isoformat()
            payloads = [("sources", {"kind": "source_imported", "source": {
                "snapshot_id": summary_id, "provider": PROVIDER,
                "url": "urn:coworld:codex-session:" + identities["session_sha256"],
                "retrieved_at": now, "description": summary}})]
            has_compute = usage["input_tokens"] is not None or usage["output_tokens"] is not None
            if has_compute:
                payloads.append((args.stage, {"kind": "compute_recorded", "usage": {
                    "execution_id": None, "worker": "codex-agent:" + summary_id,
                    "measurement": "measured", "wall_ms": None, "cpu_ms": None,
                    "peak_memory_bytes": None, "input_tokens": usage["input_tokens"],
                    "output_tokens": usage["output_tokens"]}}))
            elapsed = max(replay.previous_elapsed, time.time_ns() // 1_000_000 - replay.started_unix_ms)
            for stage, payload in payloads:
                replay.value["events"].append({"sequence": len(replay.value["events"]),
                                                "elapsed_ms": elapsed, "stage": stage, "payload": payload})
            # Both events become visible in one snapshot only after deep validation.
            with tempfile.NamedTemporaryFile(dir=replay.directory, prefix=".agent-work-", suffix=".json", delete=False) as stream:
                temporary = Path(stream.name)
            atomic_json(temporary, replay.value)
            verify(args.runtime, temporary)
            replay.save()
        except BaseException:
            replay.value = original
            raise
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return {"status": "recorded", "summary_id": summary_id, "compute_recorded": has_compute}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("run-dir", "runtime", "session", "prompt", "report"):
        parser.add_argument("--" + flag, type=Path, required=True)
    for flag in ("model", "role", "summary"):
        parser.add_argument("--" + flag, required=True)
    parser.add_argument("--reasoning-effort")
    parser.add_argument("--stage", default="changes", help="Replay stage for compute (default: changes)")
    parser.add_argument("--feedback-id", action="append", default=[])
    parser.add_argument("--feedback-supplied-at-start", action="store_true",
                        help="Assert linked feedback was supplied at start; otherwise links are cross-references")
    args = parser.parse_args()
    try:
        result = record_work(args)
    except ValueError as error:
        parser.exit(2, f"Agent work was not recorded: {error}\n")
    except OSError:
        parser.exit(2, "Agent work was not recorded: replay storage could not be accessed.\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
