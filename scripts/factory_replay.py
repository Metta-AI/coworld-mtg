#!/usr/bin/env python3
"""Small recording kernel: immutable artifacts, atomic live replay and bounded workers.

Domain adapters own cases, evaluators and acceptance policy. The Rust contract owns
the public boundary and stage topology; this module never decides what is correct.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import resource
import re
import signal
import stat
import subprocess
import time
import tempfile


def encode_json(value):
    """Deterministic JSON bytes, preserving finite floats and JSON value types."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def decode_jsonl(data):
    """The worker protocol contains exactly one finite JSON observation."""
    lines = data.splitlines()
    if len(lines) != 1:
        raise ValueError("expected exactly one observation")
    value = json.loads(lines[0])
    encode_json(value)  # Reject nonstandard NaN and overflowed infinities.
    return value


def read_worker_output(path):
    """Never follow a worker's symlink or block on a FIFO/device."""
    limit = 16 * 1024**2
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    with os.fdopen(os.open(path, flags), "rb") as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > limit:
            raise ValueError("worker output must be a regular file of at most 16 MiB")
        data = stream.read(limit + 1)
        if len(data) > limit:
            raise ValueError("worker output exceeds 16 MiB")
        return data


def canonical(value):
    def integers_only(item):
        if isinstance(item, float):
            raise ValueError("canonical contract artifacts require integer JSON numbers")
        if isinstance(item, dict):
            for child in item.values():
                integers_only(child)
        elif isinstance(item, list):
            for child in item:
                integers_only(child)
    integers_only(value)
    return encode_json(value)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def atomic_json(path, value):
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".replay-", delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(canonical(value) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
            os.replace(temporary, path)
            directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            temporary.unlink(missing_ok=True)


class Replay:
    """One writer per run. Continuing a run preserves monotonic recorded time."""
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.path = self.directory / "replay.json"
        self.lock = (self.directory / ".writer.lock").open("a")
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.value = json.loads(self.path.read_text())
            self.started_unix_ms = json.loads((self.directory / ".recording-clock.json").read_text())["started_unix_ms"]
            self.previous_elapsed = max((e["elapsed_ms"] or 0 for e in self.value["events"]), default=0)
            if self.value["status"] != "running":
                raise ValueError("terminal replays are immutable; start another run")
        except BaseException:
            self.lock.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.lock.close()

    @classmethod
    def create(cls, runtime, directory, run_id, title, program, repository, baseline_revision):
        directory = Path(directory).resolve()
        directory.mkdir(parents=True, exist_ok=False)
        subprocess.run([str(runtime), "init", "--run-id", run_id, "--title", title,
                        "--program", program, "--repository", repository,
                        "--baseline-revision", baseline_revision,
                        "--output", str(directory / "replay.json")], check=True)
        atomic_json(directory / ".recording-clock.json", {"started_unix_ms": time.time_ns() // 1_000_000})
        (directory / "artifacts").mkdir()
        (directory / "work").mkdir()
        return cls(directory)

    def require_running(self):
        if self.value["status"] != "running":
            raise ValueError("terminal replays are immutable")

    def artifact(self, value, *, raw=False, media_type="application/json"):
        self.require_running()
        data = value if raw else canonical(value)
        identity = sha256(data)
        relative = "artifacts/" + identity
        path = self.directory / relative
        if path.exists():
            if path.read_bytes() != data:
                raise ValueError("artifact identity collision")
        else:
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".artifact-", delete=False) as stream:
                temporary = Path(stream.name)
                try:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                    os.link(temporary, path)
                    temporary.unlink()
                    directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
                    try:
                        os.fsync(directory_fd)
                    finally:
                        os.close(directory_fd)
                finally:
                    temporary.unlink(missing_ok=True)
        description = {"path": relative, "media_type": media_type,
                       "hash_mode": "bytes" if raw else "canonical_json"}
        previous = self.value["artifacts"].get(identity)
        if previous and previous != description:
            # Identical JSON bytes can have both identities. Prefer the first
            # recorded hash interpretation; both have already matched the bytes.
            description = previous
        self.value["artifacts"][identity] = description
        return identity

    def event(self, stage, kind, *, validation_runtime=None, **payload):
        self.require_running()
        self.previous_elapsed = max(self.previous_elapsed, time.time_ns() // 1_000_000 - self.started_unix_ms)
        event = {"sequence": len(self.value["events"]),
                 "elapsed_ms": self.previous_elapsed,
                 "stage": stage, "payload": {"kind": kind, **payload}}
        self.value["events"].append(event)
        if validation_runtime:
            candidate = self.directory / ".pending-replay.json"
            try:
                atomic_json(candidate, self.value)
                subprocess.run([str(validation_runtime), "verify", str(candidate)],
                               check=True, stdout=subprocess.DEVNULL)
            except BaseException:
                self.value["events"].pop()
                raise
            finally:
                candidate.unlink(missing_ok=True)
        self.save()
        return event

    def save(self):
        self.require_running()
        atomic_json(self.path, self.value)

    def finish(self, status="completed"):
        if status not in ("completed", "failed", "cancelled"):
            raise ValueError("invalid terminal status")
        self.require_running()
        self.value["status"] = status
        atomic_json(self.path, self.value)

    def build(self, program, revision, binary, command, environment, attestation=None):
        build = {"program": program, "source_revision": revision,
                 "binary_sha256": sha256(Path(binary).read_bytes()),
                 "command": command, "environment": environment,
                 "attestation_id": self.artifact(attestation) if attestation else None}
        identity = self.artifact(build)
        existing = [e for e in self.value["events"]
                    if e["payload"]["kind"] == "build_recorded"
                    and e["payload"]["build_id"] == identity]
        if not existing:
            self.event("execute", "build_recorded", build_id=identity, build=build)
        return identity

    def feedback(self, case_id, execution_ids, receipt, *, evaluator, evaluator_version,
                 strength, method, claim, result, summary):
        identity = self.artifact(receipt)
        feedback = {"adapter": "opaque", "feedback_id": identity, "case_id": case_id,
                    "execution_ids": execution_ids, "evaluator": evaluator,
                    "evaluator_version": evaluator_version, "declared_strength": strength,
                    "method": method, "bounded_claim": claim, "result": result, "summary": summary}
        self.event("feedback", "feedback_recorded", feedback=feedback)
        return identity

    def run_jsonl(self, *, execution_id, case_id, build_id, binary, record,
                  arguments, protocol, classify_status, change_id=None,
                  deadline_seconds=30, memory_bytes=2 * 1024**3,
                  decode_output=decode_jsonl, output_media_type="application/x-ndjson"):
        """Run a bounded worker; its adapter decodes retained raw output bytes.

        The default remains one JSONL observation. A decoder may wrap another
        native format for presentation, but verification must recompute that
        observation from the retained output with the same frozen decoder.
        """
        self.require_running()
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,159}", execution_id):
            raise ValueError("execution ID must be a safe single path component")
        builds = [e["payload"]["build"] for e in self.value["events"]
                  if e["payload"]["kind"] == "build_recorded" and e["payload"]["build_id"] == build_id]
        binary_hash = sha256(Path(binary).read_bytes())
        if len(builds) != 1 or builds[0]["binary_sha256"] != binary_hash:
            raise ValueError("worker binary differs from its recorded build")
        work = self.directory / "work" / execution_id
        work.mkdir(exist_ok=False)
        input_path = work / "input.jsonl"
        input_path.write_bytes(encode_json(record) + b"\n")
        input_id = self.artifact(input_path.read_bytes(), raw=True, media_type="application/x-ndjson")
        output_path = work / "output.jsonl"
        command = [str(Path(binary).resolve()), *arguments(input_path, output_path)]
        request = {"protocol": protocol, "command": command, "case_id": case_id,
                   "build_id": build_id, "input_sha256": input_id, "worker_sha256": binary_hash,
                   "deadline_seconds": deadline_seconds, "memory_bytes": memory_bytes}
        request_id = self.artifact(request)
        self.event("execute", "execution_started", execution_id=execution_id,
                   case_id=case_id, request_id=request_id, build_id=build_id, change_id=change_id)

        def limits():
            resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024**2, 16 * 1024**2))
        started = time.monotonic()
        timed_out = False
        interrupted = False
        process = None
        returncode = None
        process_error = None
        with (work / "stdout.txt").open("xb") as stdout, (work / "stderr.txt").open("xb") as stderr:
            try:
                process = subprocess.Popen(command, stdout=stdout, stderr=stderr,
                                           stdin=subprocess.DEVNULL, cwd=work,
                                           preexec_fn=limits, start_new_session=True)
                try:
                    returncode = process.wait(timeout=deadline_seconds)
                except subprocess.TimeoutExpired:
                    timed_out = True
                except KeyboardInterrupt:
                    interrupted = True
            except (OSError, subprocess.SubprocessError) as error:
                process_error = str(error)
            finally:
                if process is not None:
                    # The session was created for this exact worker. Clean its
                    # whole process group, including descendants after leader exit.
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    returncode = process.wait()
        duration = int((time.monotonic() - started) * 1000)
        traces = [self.artifact((work / name).read_bytes(), raw=True, media_type="text/plain")
                  for name in ("stdout.txt", "stderr.txt")]
        output_id = None
        raw_output = None
        output_error = None
        try:
            raw_output = read_worker_output(output_path)
            output_id = self.artifact(raw_output, raw=True, media_type=output_media_type)
            traces.append(output_id)
        except (OSError, ValueError) as error:
            output_error = str(error)
        output = None
        detail = None
        status = "completed"
        if timed_out or returncode or interrupted or process_error:
            status = "cancelled" if interrupted else "error"
            detail = ("worker interrupted" if interrupted else "worker deadline exceeded" if timed_out
                      else process_error or f"worker exited with status {returncode}")
        else:
            try:
                if output_error is not None:
                    raise ValueError(output_error)
                output = decode_output(raw_output)
                encode_json(output)
                status, detail = classify_status(output)
                if status not in ("completed", "inconclusive"):
                    raise ValueError("unknown observation status")
            except Exception as error:
                output = None
                status, detail = "error", f"invalid worker output: {error}"
        receipt = {"request_id": request_id, "worker_pid": process.pid if process else None,
                   "worker_sha256": binary_hash,
                   "exit_code": returncode, "timed_out": timed_out,
                   "observation": output, "detail": detail, "output_artifact_id": output_id}
        evidence_id = self.artifact(encode_json(receipt), raw=True)
        self.event("execute", "execution_finished", execution_id=execution_id,
                   status=status, evidence_id=evidence_id, trace_ids=list(dict.fromkeys(traces)), detail=detail)
        self.event("execute", "compute_recorded", usage={
            "execution_id": execution_id, "worker": f"process:{process.pid}" if process else "spawn-failed",
            "measurement": "measured", "wall_ms": duration, "cpu_ms": None,
            "peak_memory_bytes": None, "input_tokens": None, "output_tokens": None})
        if interrupted:
            raise KeyboardInterrupt
        return {"execution_id": execution_id, "evidence_id": evidence_id,
                "observation": output, "status": status}
