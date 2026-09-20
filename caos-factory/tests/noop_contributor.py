"""Deterministic integration-test contributor. Never use as a real repair model.

It proposes a comment-only edit and approves its own test responses so the
frozen measured-improvement gate must reject it after the complete pipeline.
"""
import json, subprocess, tempfile
from pathlib import Path
args=Path("/cas/args")
subprocess.run(["caos","get",str(args/"messages")],check=True)
context=json.loads(json.loads((args/"messages").read_text())[0]["content"])
role=context["role"]
if role=="plan":
    value={"status":"propose","component":"observation_adapter",
        "issue_ids":[context["discovery"]["result"]["issues"][0]["id"]],
        "hypothesis":"Integration fixture: a comment-only edit must not earn improvement credit.",
        "changes":"Add a source comment without altering behavior.",
        "validation":"Run the full pipeline; expect the frozen comparison to reject the candidate.",
        "risks":["This is a deterministic plumbing test, not a discovered repair."]}
elif role=="implement":
    path=context["policy"]["target"]["allowed_paths"][0]
    old=context["source_files"][path][:200]
    assert context["source_files"][path].count(old)==1
    value={"summary":"Integration fixture: comment-only edit.",
        "edits":[{"path":path,"old":old,"new":"// CAOS integration fixture: no behavior change.\n"+old}]}
else:
    value={"approve":True,"findings":["Synthetic approval for integration testing only."],
        "rationale":"Exercise the measured-improvement gate even when the test contributor approves."}
output={"schema":"coworld/model-call@1","provider":"test-fixture",
    "model":"deterministic-comment-only","usage":{},"stop_reason":"end_turn","text":json.dumps(value)}
with tempfile.TemporaryDirectory() as d:
    p=Path(d)/"response.json";p.write_text(json.dumps(output))
    subprocess.run(["caos","put",str(p),"/cas/out"],check=True)
