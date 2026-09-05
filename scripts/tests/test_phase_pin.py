from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class PhasePinTests(unittest.TestCase):
    def test_corpus_revision_is_part_of_pin_gate(self) -> None:
        # Use the shipped pin surfaces and actual CLI: a stale corpus previously
        # passed this gate, then failed the server's Corpus::load check.
        files = (
            "phase-source.json",
            "corpus.lock.json",
            "Dockerfile.coworld",
            "crates/phase-bridge/Cargo.toml",
            "crates/phase-bridge/src/lib.rs",
            "scripts/build-phase-client.sh",
            "scripts/build-corpus-artifact.py",
            "scripts/check-phase-pin.py",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in files:
                destination = root / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, destination)
            command = [sys.executable, str(root / "scripts/check-phase-pin.py")]
            consistent = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(consistent.returncode, 0, consistent.stderr)
            lock_path = root / "corpus.lock.json"
            lock = json.loads(lock_path.read_text())
            lock["phase_revision"] = "0" * 40
            lock_path.write_text(json.dumps(lock))
            stale = subprocess.run(command, text=True, capture_output=True)
            self.assertNotEqual(stale.returncode, 0)
            self.assertIn("corpus.lock.json: expected Phase", stale.stderr)


if __name__ == "__main__":
    unittest.main()
