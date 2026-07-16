#!/usr/bin/env python3
"""Build the deterministic private Coworld MTG runtime corpus archive."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path


SCHEMA = "coworld-mtg-corpus-v1"
PHASE_REVISION = "2dec6c88915db4697706234a7ba2fcedd97b1689"
CORPUS_FILES = (
    "phase-card-data.json",
    "decks/fractal_convergence.json",
    "decks/lorehold_excavation.json",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    payloads: dict[str, bytes] = {}
    for relative_path in CORPUS_FILES:
        path = args.source / relative_path
        payloads[relative_path] = path.read_bytes()

    phase_cards = json.loads(payloads["phase-card-data.json"])
    manifest = {
        "schema": SCHEMA,
        "phase_revision": PHASE_REVISION,
        "card_count": len(phase_cards),
        "files": {
            name: {"bytes": len(data), "sha256": sha256(data)}
            for name, data in sorted(payloads.items())
        },
    }
    payloads["manifest.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary_directory:
        tar_path = Path(temporary_directory) / "corpus.tar"
        with tarfile.open(tar_path, "w", format=tarfile.USTAR_FORMAT) as archive:
            for name, data in sorted(payloads.items()):
                info = tarfile.TarInfo(name)
                info.size = len(data)
                info.mode = 0o644
                info.mtime = 0
                info.uid = 0
                info.gid = 0
                info.uname = ""
                info.gname = ""
                archive.addfile(info, io.BytesIO(data))
        subprocess.run(
            ["zstd", "-q", "-f", "-3", str(tar_path), "-o", str(args.output)],
            check=True,
        )

    archive = args.output.read_bytes()
    print(json.dumps({"bytes": len(archive), "sha256": sha256(archive)}, sort_keys=True))


if __name__ == "__main__":
    main()
