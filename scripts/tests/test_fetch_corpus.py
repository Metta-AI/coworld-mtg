from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/fetch-corpus.sh"


def make_archive(root: Path, *, unsafe: bool = False) -> tuple[Path, str]:
    payload = b"{}\n"
    manifest = json.dumps(
        {
            "schema": "coworld-mtg-corpus-v1",
            "files": {
                "phase-card-data.json": {
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            },
        }
    ).encode()
    tar_path = root / "corpus.tar"
    with tarfile.open(tar_path, "w") as archive:
        for name, data in (
            ("manifest.json", manifest),
            ("phase-card-data.json", payload),
        ):
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
        if unsafe:
            info = tarfile.TarInfo("../escape")
            info.size = 1
            archive.addfile(info, io.BytesIO(b"x"))
    compressed = root / "corpus.tar.zst"
    subprocess.run(["zstd", "-q", "-f", str(tar_path), "-o", str(compressed)], check=True)
    return compressed, hashlib.sha256(compressed.read_bytes()).hexdigest()


class FetchCorpusTests(unittest.TestCase):
    def run_fetch(
        self, parent: Path, destination: Path, archive: Path, checksum: str
    ) -> subprocess.CompletedProcess[str]:
        lock = json.dumps({"archive_uri": str(archive), "sha256": checksum})
        lock_path = parent / "corpus.lock.json"
        lock_path.write_text(lock)
        environment = os.environ | {
            "COWORLD_MTG_CORPUS_LOCK": str(lock_path),
            "COWORLD_MTG_CORPUS_PARENT": str(parent),
            "COWORLD_MTG_CORPUS_DIR": str(destination),
        }
        return subprocess.run(
            [str(SCRIPT)], env=environment, text=True, capture_output=True
        )

    def test_installs_verified_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            archive, checksum = make_archive(parent)
            destination = parent / "corpus"
            result = self.run_fetch(parent, destination, archive, checksum)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((destination / "phase-card-data.json").read_bytes(), b"{}\n")

    def test_checksum_failure_preserves_existing_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            archive, _ = make_archive(parent)
            destination = parent / "corpus"
            destination.mkdir()
            (destination / "sentinel").write_text("keep")
            result = self.run_fetch(parent, destination, archive, "0" * 64)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((destination / "sentinel").read_text(), "keep")

    def test_rejects_archive_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            archive, checksum = make_archive(parent, unsafe=True)
            result = self.run_fetch(parent, parent / "corpus", archive, checksum)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsafe corpus archive path", result.stderr)

    def test_rejects_allowed_parent_as_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            archive, checksum = make_archive(parent)
            result = self.run_fetch(parent, parent, archive, checksum)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must be below allowed parent", result.stderr)


if __name__ == "__main__":
    unittest.main()
