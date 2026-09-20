#!/usr/bin/env python3
"""Prepare private immutable inputs. No runs, loops, model calls, or acceptance here."""
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--corpus",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    source=out/"source";source.mkdir()
    # All tracked Rust workspace inputs, including compile-time test fixtures.
    paths=subprocess.check_output(["git","-C",str(args.repo),"ls-files","-z"],text=True).split("\0")
    for name in paths:
        if not name:continue
        if name.startswith(("crates/","fixtures/",".cargo/")) or name in ("Cargo.toml","Cargo.lock","rust-toolchain.toml","phase-source.json"):
            src=args.repo/name
            if src.is_file():
                dest=source/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
    shutil.copytree(args.repo/"fixtures/17lands/sos-cohort-20",out/"cohort")
    (out/"corpus").mkdir()
    for name in ("card-data.json","original-manifest.json"):
        shutil.copy2(args.corpus/name,out/"corpus"/name)
    (out/"sample").write_text("coworld-caos-real-cohort-20260920-attempt-1\n")
    shutil.copy2(args.repo/"caos-factory/policy.json",out/"policy.json")
    print(out)

if __name__=="__main__":main()
