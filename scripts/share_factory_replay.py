#!/usr/bin/env python3
"""Package an existing replay, optionally externalizing explicitly named sources.

Examples:
  share_factory_replay.py package RUN --output SHARE --runtime BIN \
    --external SHA256=https://publisher.example/original.txt
  share_factory_replay.py hydrate SHARE --runtime BIN

The replay and retained artifact bytes are unchanged. external-artifacts.json
maps source artifact IDs to their original HTTPS URLs. A package with missing
sources requires hydration before normal factory-runtime verify/serve/export.
Hydration verifies a complete staging copy with the native runtime before
atomically adding missing artifacts; existing files are never overwritten.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tempfile
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

EXTERNAL_FILE = "external-artifacts.json"
MAX_BYTES = 64 * 1024 * 1024


class ShareError(ValueError):
    pass


def checked_root(path):
    path = Path(os.path.abspath(Path(path).expanduser()))
    for component in [*reversed(path.parents), path]:
        if component.is_symlink():
            raise ShareError("symlink forbidden: " + str(component))
    return path


def checked_path(root, relative):
    if not isinstance(relative, str) or not relative or any(c in relative for c in "\\\x00:?#%"):
        raise ShareError("invalid artifact path")
    parts = relative.split("/")
    if any(part in ("", ".", "..") for part in parts) or PurePosixPath(relative).is_absolute():
        raise ShareError("artifact path must be a portable relative path")
    path = checked_root(root / relative)
    if root not in path.parents:
        raise ShareError("artifact path escapes run directory")
    if path.exists() and not path.is_file():
        raise ShareError("artifact is not a regular file: " + str(path))
    return path


def read_regular(path):
    checked_root(path)
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ShareError("not a regular file: " + str(path))
        return stream.read()


def load_run(directory):
    directory = checked_root(directory)
    if not directory.is_dir():
        raise ShareError("run directory is absent")
    raw = read_regular(directory / "replay.json")
    replay = json.loads(raw)
    artifacts = replay["artifacts"]
    paths = set()
    for identity, artifact in artifacts.items():
        if not re.fullmatch("[0-9a-f]{64}", identity):
            raise ShareError("invalid artifact identity")
        path = checked_path(directory, artifact["path"])
        if artifact["path"] in paths or artifact["path"] in ("replay.json", EXTERNAL_FILE):
            raise ShareError("duplicate or reserved artifact path")
        paths.add(artifact["path"])
    return directory, raw, replay


def https_url(url):
    if not isinstance(url, str) or any(ord(c) <= 32 or ord(c) == 127 for c in url):
        raise ShareError("source URL must be HTTPS")
    try:
        parsed = urlsplit(url)
        valid = (parsed.scheme == "https" and parsed.hostname and not parsed.username
                 and not parsed.password and not parsed.fragment)
        parsed.port
    except ValueError:
        valid = False
    if not valid:
        raise ShareError("source URL must be HTTPS without credentials or fragments")
    return url


def validate_external(replay, external):
    if not isinstance(external, dict):
        raise ShareError("external-artifacts.json must map artifact hashes to HTTPS URLs")
    sources = {}
    for event in replay["events"]:
        payload = event["payload"]
        if payload["kind"] == "source_imported":
            source = payload["source"]
            sources.setdefault(source["snapshot_id"], set()).add(source["url"])
    for identity, url in external.items():
        https_url(url)
        if identity not in replay["artifacts"] or url not in sources.get(identity, set()):
            raise ShareError("external artifact must match a source_imported ID and its recorded HTTPS URL")


def verify(runtime, directory):
    completed = subprocess.run([str(runtime), "verify", str(directory)],
                               capture_output=True, text=True)
    if completed.returncode:
        raise ShareError("native replay verification failed: " + (completed.stderr or completed.stdout).strip())


def copy_artifacts(source, destination, replay, allow_missing=()):
    for identity, artifact in replay["artifacts"].items():
        original = checked_path(source, artifact["path"])
        if not original.exists():
            if identity in allow_missing:
                continue
            raise ShareError("missing artifact without an external source: " + identity)
        target = checked_path(destination, artifact["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        # Read via O_NOFOLLOW; do not preserve source symlinks or special files.
        with target.open("xb") as stream:
            stream.write(read_regular(original))


def package_run(directory, output, runtime, external):
    directory, raw, replay = load_run(directory)
    output = checked_root(output)
    if output.exists() or directory == output or directory in output.parents or output in directory.parents:
        raise ShareError("output must be a new directory separate from the original run")
    validate_external(replay, external)
    verify(runtime, directory)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".replay-package-", dir=output.parent) as temporary:
        staged = Path(temporary)
        (staged / "replay.json").write_bytes(raw)
        copy_artifacts(directory, staged, replay)
        # Audit the exact captured snapshot, including every artifact we will omit.
        verify(runtime, staged)
        if read_regular(directory / "replay.json") != raw:
            raise ShareError("source replay changed during packaging; retry from a stable snapshot")
        for identity in external:
            checked_path(staged, replay["artifacts"][identity]["path"]).unlink()
        (staged / EXTERNAL_FILE).write_text(json.dumps(external, sort_keys=True, indent=2) + "\n")
        # copytree creates the destination exclusively; it never merges an old run.
        checked_root(output)
        shutil.copytree(staged, output)
    return {"directory": str(output), "external_artifacts": len(external),
            "retained_artifacts": len(replay["artifacts"]) - len(external)}


class HTTPSRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        https_url(new_url)
        return super().redirect_request(request, fp, code, message, headers, new_url)


def fetch_source(url, destination, max_bytes=MAX_BYTES, timeout=30):
    https_url(url)
    opener = build_opener(HTTPSRedirects())
    request = Request(url, headers={
        "User-Agent": "Coworld-Replay-Hydrator/1.0 (+https://github.com/Metta-AI/coworld-mtg)",
        "Accept": "*/*", "Accept-Encoding": "identity",
    })
    with opener.open(request, timeout=timeout) as response:
        https_url(response.geturl())
        length = response.headers.get("Content-Length")
        if length is not None and int(length) > max_bytes:
            raise ShareError("source exceeds download size limit")
        total = 0
        with destination.open("xb") as stream:
            while chunk := response.read(min(1024 * 1024, max_bytes + 1 - total)):
                total += len(chunk)
                if total > max_bytes:
                    raise ShareError("source exceeds download size limit")
                stream.write(chunk)


def hydrate_run(directory, runtime, max_bytes=MAX_BYTES, timeout=30):
    if max_bytes <= 0 or timeout <= 0:
        raise ShareError("download size and timeout must be positive")
    directory, raw, replay = load_run(directory)
    manifest_raw = read_regular(directory / EXTERNAL_FILE)
    external = json.loads(manifest_raw)
    validate_external(replay, external)
    missing = [identity for identity in external
               if not checked_path(directory, replay["artifacts"][identity]["path"]).exists()]
    with tempfile.TemporaryDirectory(prefix=".replay-hydrate-", dir=directory.parent) as temporary:
        staged = Path(temporary)
        (staged / "replay.json").write_bytes(raw)
        copy_artifacts(directory, staged, replay, allow_missing=missing)
        for identity in missing:
            target = checked_path(staged, replay["artifacts"][identity]["path"])
            target.parent.mkdir(parents=True, exist_ok=True)
            fetch_source(external[identity], target, max_bytes, timeout)
        # Native hashing handles both bytes and canonical_json exactly as the contract.
        # No downloaded artifact is added to the shared run until this audit passes.
        verify(runtime, staged)
        if (read_regular(directory / "replay.json") != raw
                or read_regular(directory / EXTERNAL_FILE) != manifest_raw):
            raise ShareError("replay or external source manifest changed during hydration")
        for identity in missing:
            relative = replay["artifacts"][identity]["path"]
            target = checked_path(directory, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            checked_path(directory, relative)
            # Both directories share a filesystem. link is atomic and fails if ANY
            # existing target (including a symlink) appears; it never replaces data.
            os.link(checked_path(staged, relative), target, follow_symlinks=False)
    verify(runtime, directory)
    return {"directory": str(directory), "hydrated_artifacts": len(missing),
            "verified": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    modes = parser.add_subparsers(dest="mode", required=True)
    package = modes.add_parser("package", help="verify and copy a replay, omitting explicit original HTTPS sources")
    package.add_argument("run", type=Path)
    package.add_argument("--output", required=True, type=Path)
    package.add_argument("--runtime", required=True, type=Path, help="native factory-runtime executable")
    package.add_argument("--external", action="append", default=[], metavar="SHA256=HTTPS_URL",
                         help="source_imported artifact and its exact recorded URL; repeat for multiple sources")
    hydrate = modes.add_parser("hydrate", help="retrieve missing external sources, hash-check and verify the replay")
    hydrate.add_argument("run", type=Path)
    hydrate.add_argument("--runtime", required=True, type=Path, help="native factory-runtime executable")
    hydrate.add_argument("--max-bytes", type=int, default=MAX_BYTES, help="maximum bytes per source (default: 64 MiB)")
    hydrate.add_argument("--timeout", type=float, default=30, help="network timeout in seconds (default: 30)")
    args = parser.parse_args()
    if args.mode == "package":
        external = {}
        for item in args.external:
            identity, separator, url = item.partition("=")
            if not separator or identity in external:
                parser.error("--external requires a unique SHA256=HTTPS_URL")
            external[identity] = url
        result = package_run(args.run, args.output, args.runtime, external)
    else:
        result = hydrate_run(args.run, args.runtime, args.max_bytes, args.timeout)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
