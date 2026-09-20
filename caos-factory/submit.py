#!/usr/bin/env python3
"""Freeze a private client and submit ONE CAOS program. Scheduling lives in CAOS."""
import argparse, hashlib, json, re, shutil, subprocess, uuid
from pathlib import Path

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--client",type=Path,required=True)
    parser.add_argument("--inputs",type=Path,required=True)
    parser.add_argument("--caos-cli",type=Path,required=True)
    parser.add_argument("--server",required=True)
    parser.add_argument("--image",required=True,help="Imported git-docker image object, already available on the server")
    contributor=parser.add_mutually_exclusive_group(required=True)
    contributor.add_argument("--key-file",type=Path)
    contributor.add_argument("--contributor",help="Existing immutable CAOS model-call capability; no key grant is created")
    parser.add_argument("--sample",help="Explicit sample identity override; leave unchanged when resuming")
    args=parser.parse_args()
    if not re.fullmatch("[0-9a-f]{40}",args.image):raise ValueError("expected an immutable Git image ID")
    if args.contributor and not re.fullmatch("[0-9a-f]{40}",args.contributor):
        raise ValueError("expected an immutable contributor object ID")
    client=args.client.resolve()
    if client.exists():raise ValueError("use a new private client directory; existing epochs are immutable")
    client.mkdir(parents=True)
    cli=str(args.caos_cli.resolve())
    def run(*argv,**kw):return subprocess.run(list(map(str,argv)),cwd=client,check=True,**kw)
    run("git","init","-q","-b","codex/factory-client-"+uuid.uuid4().hex[:8])
    run("git","remote","add","caos",args.server)
    run("git","config","pack.threads","2")
    run("git","fetch","caos",args.image)
    package=Path(__file__).parent
    shutil.copytree(args.inputs,client/"input")
    if args.sample is not None:(client/"input/sample").write_text(args.sample)
    (client/"factory").mkdir()
    shutil.copy2(package/"worker.py",client/"factory/worker.py")
    shutil.copytree(package/"lib",client/"factory/modules",ignore=shutil.ignore_patterns("__pycache__","*.pyc"))
    provider=client/"factory-llm";provider.mkdir();(provider/"modules").mkdir()
    (provider/"modules/placeholder").write_text("No provider helper modules.\n")
    shutil.copy2(package/"llm_call.py",provider/"llm_call.py")
    (provider/".caos-expr").write_text("curry --base:hash="+args.image+" --worker1:@=llm_call.py --modules:@=modules\n")
    (client/".gitignore").write_text(".caos-secrets/\nrequest\nresult.commit\nrun.log\nstatus.json\n")
    run("git","add",".gitignore","factory","factory-llm","input")
    if args.contributor:
        run("git","fetch","caos",args.contributor)
        llm=args.contributor
    else:
        secret=client/".caos-secrets";secret.mkdir(mode=0o700)
        key=args.key_file.resolve(strict=True)
        (secret/"anthropic-api-key").write_text("name=anthropic-api-key\nvalue:@="+str(key)+"\nreader=factory-llm\n")
        (secret/"anthropic-api-key").chmod(0o600)
        run(cli,"secrets")
        llm=subprocess.check_output([cli,"prepare-request","--base:@=factory-llm"],cwd=client,text=True).strip()
    kv=["--base:hash="+args.image,"--worker1:@=factory/worker.py","--modules:@=factory/modules","--stage=start",
        "--source:@=input/source","--cohort:@=input/cohort","--corpus:@=input/corpus",
        "--policy:@=input/policy.json","--sample:@=input/sample","--llm:hash="+llm]
    with (client/"request").open("w") as out:run(cli,"prepare-request",*kv,stdout=out)
    with (client/"result.commit").open("w") as out,(client/"run.log").open("w") as err:
        run(cli,"run",*kv,stdout=out,stderr=err)
    content=(client/"result.commit").read_bytes()
    commit=hashlib.sha1(b"commit "+str(len(content)).encode()+b"\0"+content).hexdigest()
    request=(client/"request").read_text().strip()
    run("git","fetch","caos",commit)
    ref="refs/factory/epochs/"+request
    run("git","update-ref",ref,commit)
    run("git","push","caos",commit+":"+ref)
    with (client/"status.json").open("w") as out:
        run(cli,"status","--all",(client/"request").read_text().strip(),stdout=out)
    print((client/"result.commit").read_text())

if __name__=="__main__":main()
