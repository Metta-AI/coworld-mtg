import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.request import Request

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("share_factory_replay", ROOT / "scripts/share_factory_replay.py")
share = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = share
SPEC.loader.exec_module(share)
URL = "https://publisher.example/original.txt"


def fixture(directory):
    raw = b"Original source text.\n"
    identity = hashlib.sha256(raw).hexdigest()
    directory.mkdir()
    (directory / "artifacts").mkdir()
    (directory / "artifacts" / identity).write_bytes(raw)
    replay = {"artifacts": {identity: {"path": "artifacts/" + identity, "hash_mode": "bytes"}},
              "events": [{"payload": {"kind": "source_imported",
                         "source": {"snapshot_id": identity, "url": URL}}}]}
    (directory / "replay.json").write_text(json.dumps(replay, indent=2) + "\n")
    return raw, identity, replay


def fixture_verifier(runtime, directory):
    # Unit fixture hash auditor, not an MTG evaluator or factory evidence.
    replay = json.loads((directory / "replay.json").read_bytes())
    for identity, artifact in replay["artifacts"].items():
        raw = (directory / artifact["path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != identity:
            raise share.ShareError("native replay verification failed: artifact hash mismatch")


class ShareFactoryReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = self.root / "run"
        self.raw, self.identity, self.replay = fixture(self.run)
        self.output = self.root / "share"

    def package(self):
        with patch.object(share, "verify", side_effect=fixture_verifier):
            return share.package_run(self.run, self.output, "runtime", {self.identity: URL})

    def test_package_preserves_replay_and_leaves_original_artifact_untouched(self):
        replay_bytes = (self.run / "replay.json").read_bytes()
        self.package()
        self.assertEqual((self.output / "replay.json").read_bytes(), replay_bytes)
        self.assertEqual((self.run / "artifacts" / self.identity).read_bytes(), self.raw)
        self.assertFalse((self.output / "artifacts" / self.identity).exists())
        self.assertEqual(json.loads((self.output / share.EXTERNAL_FILE).read_text()), {self.identity: URL})

    def test_only_explicit_source_with_exact_https_url_can_be_externalized(self):
        for external in ({self.identity: "http://publisher.example/original.txt"},
                         {self.identity: "https://other.example/replacement"},
                         {"0" * 64: URL}):
            with self.subTest(external=external), self.assertRaises(share.ShareError):
                share.package_run(self.run, self.output, "runtime", external)
        self.replay["events"] = []
        (self.run / "replay.json").write_text(json.dumps(self.replay))
        with self.assertRaisesRegex(share.ShareError, "source_imported"):
            share.package_run(self.run, self.output, "runtime", {self.identity: URL})

    def test_traversal_absolute_and_reserved_paths_rejected_before_native_verification(self):
        for relative in ("../escape", "/escape", "artifacts/../../escape", "artifacts\\escape",
                         "artifacts/%2e%2e/escape", "artifacts//x", "./artifact", "replay.json"):
            with self.subTest(relative=relative):
                self.replay["artifacts"][self.identity]["path"] = relative
                (self.run / "replay.json").write_text(json.dumps(self.replay))
                with patch.object(share, "verify") as verify, self.assertRaises(share.ShareError):
                    share.package_run(self.run, self.output, "runtime", {})
                verify.assert_not_called()

    def test_artifact_and_directory_symlinks_are_rejected(self):
        artifact = self.run / "artifacts" / self.identity
        outside = self.root / "outside"
        outside.write_bytes(self.raw)
        artifact.unlink()
        artifact.symlink_to(outside)
        with self.assertRaisesRegex(share.ShareError, "symlink"):
            share.load_run(self.run)
        artifact.unlink()
        artifact.write_bytes(self.raw)
        link = self.root / "linked-run"
        link.symlink_to(self.run, target_is_directory=True)
        with self.assertRaisesRegex(share.ShareError, "symlink"):
            share.load_run(link)

    def test_existing_output_cannot_be_replaced(self):
        self.output.mkdir()
        marker = self.output / "keep"
        marker.write_text("unchanged")
        with self.assertRaises(share.ShareError):
            share.package_run(self.run, self.output, "runtime", {})
        self.assertEqual(marker.read_text(), "unchanged")

    def test_corrupt_download_never_publishes_missing_artifact(self):
        self.package()
        before = (self.output / "replay.json").read_bytes()
        def corrupt(url, target, *limits):
            target.write_bytes(b"wrong source")
        with patch.object(share, "fetch_source", side_effect=corrupt), \
                patch.object(share, "verify", side_effect=fixture_verifier), \
                self.assertRaisesRegex(share.ShareError, "hash mismatch"):
            share.hydrate_run(self.output, "runtime")
        self.assertFalse((self.output / "artifacts" / self.identity).exists())
        self.assertEqual((self.output / "replay.json").read_bytes(), before)
        self.assertEqual(list(self.root.glob(".replay-hydrate-*")), [])

    def test_hydration_verifies_before_publish_and_preserves_existing_artifacts(self):
        self.package()
        target = self.output / "artifacts" / self.identity
        verification_dirs = []
        def native(runtime, directory):
            if directory != self.output:
                self.assertFalse(target.exists())
            verification_dirs.append(directory)
            fixture_verifier(runtime, directory)
        def retrieve(url, path, *limits):
            self.assertEqual(url, URL)
            path.write_bytes(self.raw)
        with patch.object(share, "fetch_source", side_effect=retrieve) as fetch, \
                patch.object(share, "verify", side_effect=native):
            result = share.hydrate_run(self.output, "runtime")
        self.assertEqual(result["hydrated_artifacts"], 1)
        self.assertEqual(len(verification_dirs), 2)
        self.assertEqual(target.read_bytes(), self.raw)
        with patch.object(share, "fetch_source") as fetch, \
                patch.object(share, "verify", side_effect=fixture_verifier):
            result = share.hydrate_run(self.output, "runtime")
        fetch.assert_not_called()
        self.assertEqual(result["hydrated_artifacts"], 0)

    def test_existing_corrupt_artifact_is_not_replaced_from_network(self):
        self.package()
        target = self.output / "artifacts" / self.identity
        target.write_bytes(b"existing corrupt bytes")
        with patch.object(share, "fetch_source") as fetch, \
                patch.object(share, "verify", side_effect=fixture_verifier), \
                self.assertRaisesRegex(share.ShareError, "hash mismatch"):
            share.hydrate_run(self.output, "runtime")
        fetch.assert_not_called()
        self.assertEqual(target.read_bytes(), b"existing corrupt bytes")

    def test_https_redirect_downgrade_and_credentials_are_rejected(self):
        for url in ("http://publisher.example/file", "file:///etc/passwd",
                    "https://user:secret@publisher.example/file", "https://publisher.example/file#fragment"):
            with self.subTest(url=url), self.assertRaises(share.ShareError):
                share.https_url(url)
        with self.assertRaises(share.ShareError):
            share.HTTPSRedirects().redirect_request(
                Request(URL), None, 302, "Moved", {}, "http://publisher.example/file")

    def test_download_limit_rejects_oversized_stream(self):
        class Response:
            headers = {}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def geturl(self): return URL
            def read(self, limit): return b"x" * limit
        class Opener:
            def open(self, request, timeout): return Response()
        with patch.object(share, "build_opener", return_value=Opener()), \
                self.assertRaisesRegex(share.ShareError, "size limit"):
            share.fetch_source(URL, self.root / "download", max_bytes=10)
        self.assertLessEqual((self.root / "download").stat().st_size, 10)


if __name__ == "__main__":
    unittest.main()
