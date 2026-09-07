"""Corpus packaging gate tests using explicit subprocess protocol fixtures."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/build-corpus-artifact.py"
REVISION = re.search(r'PHASE_REVISION = "([0-9a-f]{40})"', SCRIPT.read_text()).group(1)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def members(path):
    raw = subprocess.check_output(["zstd", "-q", "-d", "-c", str(path)])
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        return {item.name: archive.extractfile(item).read() for item in archive.getmembers()}


class BuildCorpusArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        (self.source / "decks").mkdir(parents=True)
        self.card_bytes = b'{"synthetic_fixture_card":{"test_only":true}}\n'
        (self.source / "phase-card-data.json").write_bytes(self.card_bytes)
        for name in ("fractal_convergence", "lorehold_excavation"):
            (self.source / "decks" / (name + ".json")).write_text('{"test_only":true,"cards":[]}\n')
        self.validator = self.root / "fixture-validator"
        self.write_validator(
            "import json,sys\n"
            "assert sys.argv[1:] == ['phase-card-data.json']\n"
            "data=json.load(open(sys.argv[1]))\n"
            "assert data['synthetic_fixture_card']['test_only'] is True\n"
            "print('OK: synthetic fixture validated from ' + sys.argv[1])\n")
        self.output = self.root / "corpus.tar.zst"

    def write_validator(self, body):
        self.validator.write_text(f"#!{sys.executable}\n" + body)
        self.validator.chmod(0o700)

    def build(self, output=None, validator=None, revision=REVISION, env=None):
        return subprocess.run([
            sys.executable, "-B", str(SCRIPT), str(self.source), str(output or self.output),
            "--validator", str(validator or self.validator), "--validator-phase-revision", revision,
        ], capture_output=True, env=env)

    def test_explicit_validator_is_required(self):
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(self.source), str(self.output)],
                                capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"--validator", result.stderr)
        self.assertFalse(self.output.exists())

    def test_native_rejection_retains_identities_and_never_creates_archive(self):
        self.write_validator("import sys\nprint('fixture rejection',file=sys.stderr)\nsys.exit(7)\n")
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())
        report = json.loads(result.stdout)
        self.assertEqual(report["validation"]["exit_code"], 7)
        self.assertEqual(report["validation"]["input"]["sha256"], digest(self.card_bytes))
        self.assertEqual(report["validation"]["validator_sha256"], digest(self.validator.read_bytes()))
        self.assertEqual(report["validation"]["declared_phase_revision"], REVISION)
        self.assertEqual(base64.b64decode(report["stderr_base64"]), b"fixture rejection\n")
        self.assertEqual(report["validation"]["stderr"]["sha256"], digest(b"fixture rejection\n"))
        self.assertEqual((self.source / "phase-card-data.json").read_bytes(), self.card_bytes)
        self.assertEqual(list(self.root.glob(".corpus-build-*")), [])

    def test_nonexecutable_validator_is_rejected(self):
        self.validator.chmod(0o600)
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())
        self.assertIsNone(json.loads(result.stdout)["validation"]["exit_code"])

    def test_success_is_deterministic_and_existing_fetch_accepts_provenance_members(self):
        first = self.build()
        self.assertEqual(first.returncode, 0, first.stderr)
        elsewhere = self.root / "another-validator-path"
        shutil.copyfile(self.validator, elsewhere)
        elsewhere.chmod(0o700)
        second_path = self.root / "second.tar.zst"
        second = self.build(second_path, elsewhere)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.output.read_bytes(), second_path.read_bytes())
        data = members(self.output)
        manifest = json.loads(data["manifest.json"])
        self.assertEqual(manifest["schema"], "coworld-mtg-corpus-v1")
        self.assertEqual(manifest["card_count"], 1)
        self.assertEqual(data["phase-card-data.json"], self.card_bytes)
        validation = manifest["validation"]
        self.assertEqual(validation["status"], "passed")
        self.assertEqual(validation["exit_code"], 0)
        self.assertEqual(validation["validator_sha256"], digest(self.validator.read_bytes()))
        self.assertIn("caller attests", validation["source_attribution"])
        self.assertIn("does not independently prove", validation["source_attribution"])
        self.assertNotIn(str(self.root).encode(), data["manifest.json"])
        self.assertNotIn(b"wall_ms", data["manifest.json"])
        for name, identity in manifest["files"].items():
            self.assertEqual(digest(data[name]), identity["sha256"])
            self.assertEqual(len(data[name]), identity["bytes"])
        for stream in ("stdout", "stderr"):
            self.assertEqual(digest(data[validation[stream]["path"]]), validation[stream]["sha256"])
        lock = self.root / "lock.json"
        lock.write_text(json.dumps({"archive_uri": str(self.output), "sha256": digest(self.output.read_bytes())}))
        destination = self.root / "installed"
        fetched = subprocess.run([str(ROOT / "scripts/fetch-corpus.sh")], capture_output=True,
                                 env=os.environ | {"COWORLD_MTG_CORPUS_LOCK": str(lock),
                                                   "COWORLD_MTG_CORPUS_DIR": str(destination),
                                                   "COWORLD_MTG_CORPUS_PARENT": str(self.root)})
        self.assertEqual(fetched.returncode, 0, fetched.stderr)
        self.assertEqual((destination / "phase-card-data.json").read_bytes(), self.card_bytes)
        self.assertEqual((destination / "validation/stdout.txt").read_bytes(), data["validation/stdout.txt"])

    def test_validator_mutation_of_staged_input_is_rejected(self):
        self.write_validator("from pathlib import Path\nPath('phase-card-data.json').write_text('{}')\n")
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["validation"]["exit_code"], 0)
        self.assertIn(b"changed or removed", result.stderr)
        self.assertFalse(self.output.exists())
        self.assertEqual((self.source / "phase-card-data.json").read_bytes(), self.card_bytes)

    def test_existing_output_is_immutable(self):
        self.output.write_bytes(b"previous completed archive")
        self.write_validator("raise RuntimeError('validator must not run for an existing output')\n")
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"refusing to overwrite", result.stderr)
        self.assertEqual(self.output.read_bytes(), b"previous completed archive")

    def test_failed_compression_cannot_publish_partial_archive(self):
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        compressor = bin_dir / "zstd"
        compressor.write_text(f"#!{sys.executable}\n"
                              "from pathlib import Path\nimport sys\n"
                              "Path(sys.argv[sys.argv.index('-o')+1]).write_bytes(b'partial')\n"
                              "sys.exit(9)\n")
        compressor.chmod(0o700)
        result = self.build(env=os.environ | {"PATH": str(bin_dir) + os.pathsep + os.environ["PATH"]})
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob(".corpus-build-*")), [])

    def test_wrong_declared_revision_is_rejected(self):
        result = self.build(revision="0" * 40)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"pinned PHASE_REVISION", result.stderr)
        self.assertFalse(self.output.exists())

    def test_snapshot_is_packaged_even_if_original_source_changes_after_capture(self):
        original = self.source / "phase-card-data.json"
        self.write_validator("from pathlib import Path\n"
                             f"Path({str(original)!r}).write_text('{{}}')\n"
                             "assert Path('phase-card-data.json').read_text().startswith('{\"synthetic_fixture_card\"')\n")
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(members(self.output)["phase-card-data.json"], self.card_bytes)


if __name__ == "__main__":
    unittest.main()
