import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("import_case_replay", ROOT / "scripts/import_case_replay.py")
importer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = importer
SPEC.loader.exec_module(importer)
ARCHIVE = ROOT / "cases/evidence/hushbringer-simultaneous-death"


class ImportCaseReplayTests(unittest.TestCase):
    def test_original_acceptance_and_frozen_bindings_are_preserved(self):
        archive = importer.load_archive(ARCHIVE)
        self.assertEqual(archive["acceptance_id"], "66ef2e974d5dfb7f59f93f98405dcd6d9dd7b17fb9fab9df0fc3491dfdf6aba4")
        self.assertEqual(len(archive["candidates"]), 10)
        self.assertEqual(len(archive["plan"]["regression_case_ids"]), 7)
        self.assertEqual(len(archive["plan"]["holdout_case_ids"]), 2)
        self.assertEqual(sum(len(b["evidence"]) for b in [archive["baseline"], *archive["candidates"]]), 22)
        self.assertEqual(archive["patch_id"], "f35967418e623234a47a9dd4499a5516e05cd4fc16d898953e60465d1a87fc60")
        self.assertEqual(archive["build_ids"]["baseline"], "54f5a3f7207af81b12d562537b1089886c2717275f1d579b8fd0828dba2cb5ff")
        self.assertEqual(archive["build_ids"]["candidate"], "81eb62e305ee8d87d7e99ff31e2bcd382a226afded61236d48d51f6d148df6b9")

    def test_wrong_acceptance_is_rejected_without_changing_source(self):
        path = ARCHIVE / "acceptance.json"
        original = path.read_bytes()
        with self.assertRaisesRegex(importer.ImportError, "acceptance identity"):
            importer.load_archive(ARCHIVE, "0" * 64)
        self.assertEqual(path.read_bytes(), original)

    def test_output_cannot_overlap_archive_or_replace_existing_directory(self):
        for output in (ARCHIVE, ARCHIVE / "new-replay", ARCHIVE.parent):
            with self.assertRaises(importer.ImportError):
                importer.ensure_separate_output(ARCHIVE, output)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileExistsError):
                importer.ensure_separate_output(ARCHIVE, directory)

    def test_artifacts_preserve_original_bytes_and_use_the_right_hash_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            replay = {"artifacts": {}}
            store = importer.ArtifactStore(root, replay)
            raw = b'{\n  "b": 2,\n  "a": 1\n}\n'
            identity = store.add(raw, "canonical_json", "application/json", ".json", "case.json")
            self.assertEqual(identity, importer.digest({"a": 1, "b": 2}))
            self.assertEqual((root / replay["artifacts"][identity]["path"]).read_bytes(), raw)
            self.assertEqual(store.inventory[0]["original_bytes_sha256"], importer.sha256(raw))
            for filename in ("baseline-build.json", "candidate-build.json", "corpus.json"):
                identity = store.file(ARCHIVE / filename if filename != "corpus.json" else
                                      ARCHIVE / "baseline" / importer.load_archive(ARCHIVE)["plan"]["case_id"] / filename)
                self.assertEqual(replay["artifacts"][identity]["hash_mode"], "bytes")
            patch = b"diff --git a/file b/file\n"
            patch_id = store.add(patch, "bytes", "text/x-diff", ".patch", "repair.patch")
            self.assertEqual(patch_id, importer.sha256(patch))
            self.assertEqual(replay["artifacts"][patch_id]["hash_mode"], "bytes")


if __name__ == "__main__":
    unittest.main()
