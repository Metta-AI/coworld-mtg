"""Pinned dependency capture followed by offline candidate compilation."""
import os, shutil, subprocess
from pathlib import Path
import cas

def environment(root):
    env=dict(os.environ)
    home=root/"cargo-home"; home.mkdir()
    env.update(CARGO_HOME=str(home),HOME=str(root),CARGO_BUILD_JOBS="2",
        RUSTUP_TOOLCHAIN="nightly-2026-04-19",CARGO_PROFILE_DEV_DEBUG="0",CARGO_PROFILE_TEST_DEBUG="0",CARGO_INCREMENTAL="0",RUST_MIN_STACK="16777216")
    return env

def vendor():
    source=cas.argument("source")
    root=cas.scratch("vendor"); src=root/"src"
    cas.copy_value(source,src)
    env=environment(root)
    with (root/"stderr.txt").open("w") as err:
        p=subprocess.run(["cargo","vendor","--locked","vendor"],cwd=src,env=env,
            stdout=subprocess.PIPE,stderr=err,text=True,timeout=900)
    if p.returncode: raise RuntimeError((root/"stderr.txt").read_text()[-12000:])
    (src/"config.toml").write_text(p.stdout)
    cas.emit(cas.receipt("dependency-acquisition",{"lock_sha256":cas.sha(src/"Cargo.lock"),"mode":"cargo vendor --locked"},
        {"source":source},outputs={"vendor":cas.store(src/"vendor"),"config.toml":cas.store(src/"config.toml"),"log":cas.store(root/"stderr.txt")}))

def compile_target():
    source,deps,policy=cas.argument("source"),cas.argument("dependencies"),cas.value("policy")
    root=cas.scratch("build");src=root/"src";cas.copy_value(source,src)
    cas.copy_value(deps/"vendor",src/"vendor")
    (src/".cargo").mkdir(exist_ok=True)
    cas.copy_value(deps/"config.toml",src/".cargo"/"config.toml")
    env=environment(root)
    results=[];passed=True
    for name,argv in (("build",policy["target"]["build_command"]),("test",policy["target"]["test_command"])):
        log=root/(name+".log")
        with log.open("w") as output:
            p=subprocess.run(argv,cwd=src,env=env,stdout=output,stderr=subprocess.STDOUT,timeout=1800)
        results.append({"name":name,"argv":argv,"exit_code":p.returncode})
        if p.returncode:passed=False;break
    outputs={x["name"]+".log":cas.store(root/(x["name"]+".log")) for x in results}
    if passed: outputs["binary"]=cas.store(src/"target/debug/coworld-mtg-harness")
    cas.emit(cas.receipt("build",{"passed":passed,"commands":results,"source":cas.identity(source),"environment":{k:env[k] for k in ("RUSTUP_TOOLCHAIN","CARGO_BUILD_JOBS","CARGO_PROFILE_DEV_DEBUG","CARGO_PROFILE_TEST_DEBUG","CARGO_INCREMENTAL","RUST_MIN_STACK")}},
        {"source":source,"dependencies":deps,"policy":cas.argument("policy")},outputs=outputs))
