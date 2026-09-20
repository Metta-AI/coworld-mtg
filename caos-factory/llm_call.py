"""A single metered model call; only this frozen expression receives the API key."""
from pathlib import Path
import json, urllib.request, urllib.error, subprocess, tempfile
ARGS=Path("/cas/args")
def read(name):
    subprocess.run(["caos","get",str(ARGS/name)],check=True)
    return (ARGS/name).read_text()
body={"model":read("model").strip(),"max_tokens":int(read("max-tokens")),
    "system":read("system"),"messages":json.loads(read("messages"))}
key=Path("/secret/anthropic-api-key").read_text()
request=urllib.request.Request("https://api.anthropic.com/v1/messages",
    data=json.dumps(body).encode(),headers={"x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"})
try:
    with urllib.request.urlopen(request,timeout=300) as response: result=json.load(response)
except urllib.error.HTTPError as error:
    raise RuntimeError("Model provider returned HTTP "+str(error.code)+": "+error.read(2000).decode(errors="replace")) from None
output={"schema":"coworld/model-call@1","provider":"anthropic","model":result.get("model"),
    "usage":result.get("usage"),"stop_reason":result.get("stop_reason"),
    "text":"\n".join(block["text"] for block in result["content"] if block["type"]=="text")}
with tempfile.TemporaryDirectory() as d:
    path=Path(d)/"response.json";path.write_text(json.dumps(output))
    subprocess.run(["caos","put",str(path),"/cas/out"],check=True)
