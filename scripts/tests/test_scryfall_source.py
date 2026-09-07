import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("scryfall_source", ROOT / "scripts/scryfall_source.py")
source = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = source
SPEC.loader.exec_module(source)


def card(oracle="00000000-0000-4000-8000-000000000001", printing="00000000-0000-4000-8000-000000000011", text="{T}, Mill a card: Add {C}."):
    return {"object": "card", "oracle_id": oracle, "id": printing, "name": "Unit-test card",
            "layout": "normal", "games": ["paper"], "legalities": {"vintage": "legal"},
            "oracle_text": text}


def snapshot(directory, raw):
    directory.mkdir()
    archive = directory / "source.jsonl.gz"
    archive.write_bytes(gzip.compress(raw))
    manifest = {"status": "complete", "artifacts": {"archive": {
        "path": archive.name, "bytes": archive.stat().st_size,
        "sha256": source.file_sha256(archive)}}}
    source.write_json(directory / "source-manifest.json", manifest)


class DescriptorTests(unittest.TestCase):
    def test_current_and_legacy_descriptors_and_rejected_origins(self):
        current = source.descriptor_download({
            "type": "oracle_cards", "jsonl_download_uri": "https://data.scryfall.io/oracle.jsonl.gz",
            "compressed_size": 24535585})
        self.assertEqual(current["expected_bytes"], 24535585)
        self.assertEqual(current["format"], "gzip_jsonl")
        legacy = source.descriptor_download({
            "type": "oracle_cards", "download_uri": "https://data.scryfall.io/oracle.json",
            "size": 172000000, "content_encoding": "gzip"})
        self.assertIsNone(legacy["expected_bytes"])  # Old size is not compressed wire length.
        self.assertEqual(legacy["format"], "legacy_json")
        for descriptor in [
            {"type": "rulings", "download_uri": "https://data.scryfall.io/x"},
            {"type": "oracle_cards", "jsonl_download_uri": "https://data.scryfall.io/x"},
            {"type": "oracle_cards", "download_uri": "https://scryfall.io.evil.test/x"},
            {"type": "oracle_cards", "download_uri": "http://data.scryfall.io/x"},
        ]:
            with self.assertRaises(source.SourceError):
                source.descriptor_download(descriptor)


class RecordTests(unittest.TestCase):
    def test_gzip_jsonl_keeps_exact_boundaries_unicode_and_corruption(self):
        raw = b'{"name":"first"}\r\n' + '{"name":"Óin"}\n'.encode() + b'not JSON\n\n{"name":"last"}'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cards.bin"
            path.write_bytes(gzip.compress(raw))
            rows = list(source.iter_records(path))
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0].raw, b'{"name":"first"}\r\n')
        self.assertEqual(rows[1].card["name"], "Óin")
        self.assertEqual(rows[1].offset, len(rows[0].raw))
        self.assertIsNotNone(rows[2].error)
        self.assertIsNotNone(rows[3].error)
        self.assertEqual(rows[4].card["name"], "last")
        self.assertEqual(b"".join(row.raw for row in rows), raw)

    def test_legacy_array_retains_raw_objects_across_chunks(self):
        first = '{ "name" : "Óin", "oracle_text": "' + ("x" * 70000) + '" }'
        second = '{"nested":{"quoted":"} ] \\""},"array":[1,2]}'
        raw = (" \n[ \n" + first + ",\n" + second + "\n]\n").encode()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cards.json"
            path.write_bytes(raw)
            rows = list(source.iter_records(path))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].raw, first.encode())
        self.assertEqual(rows[1].raw, second.encode())
        for row in rows:
            self.assertEqual(raw[row.offset:row.offset + len(row.raw)], row.raw)

    def test_limits_truncated_gzip_and_bad_array_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cards"
            path.write_bytes(b'{"text":"1234567890"}\n')
            with self.assertRaises(source.SourceError):
                list(source.iter_records(path, max_record_bytes=10))
            with self.assertRaises(source.SourceError):
                list(source.iter_records(path, max_uncompressed_bytes=10))
            path.write_bytes(gzip.compress(b'{"a":1}\n')[:-5])
            with self.assertRaises(source.SourceError):
                list(source.iter_records(path))
            for raw in (b'[{"a":1},]', b'[{"a":1}', b'[{"a":1}] junk', b'[{"a":'):
                path.write_bytes(raw)
                with self.assertRaises(source.SourceError):
                    list(source.iter_records(path))


class ClassificationTests(unittest.TestCase):
    def test_cohort_preserves_exclusions_and_face_identity(self):
        item = card()
        self.assertTrue(source.classify_card(item)["eligible"])
        item.update(layout="reversible_card", oracle_id=None, games=["arena"],
                    legalities={"vintage": "not_legal"},
                    card_faces=[{"oracle_id": "face-a"}, {"oracle_id": "face-b"}])
        result = source.classify_card(item)
        self.assertFalse(result["eligible"])
        self.assertEqual(result["face_oracle_ids"], ["face-a", "face-b"])
        self.assertEqual(set(result["exclusion_reasons"]),
                         {"missing_oracle_id", "layout_not_normal", "representative_printing_not_paper",
                          "vintage_not_legal_or_restricted"})
        self.assertIsNone(result["split"])

    def test_split_uses_identity_not_printing_or_name(self):
        first = card()
        second = dict(first, id="different-printing", name="Different translated name")
        self.assertEqual(source.classify_card(first)["split"], source.classify_card(second)["split"])
        oracle = first["oracle_id"]
        digest = hashlib.sha256((source.RECIPE["seed"] + "\0" + oracle).encode()).hexdigest()
        expected = "holdout" if int(digest[:8], 16) % 100 < 20 else "development"
        self.assertEqual(source.split_identity(oracle), expected)
        splits = [source.split_identity(str(index)) for index in range(100)]
        self.assertIn("holdout", splits)
        self.assertIn("development", splits)

    def test_cost_effect_and_quoted_signals_are_explicitly_weak(self):
        cost = source.paragraph_signals("{T}, Mill a card: Add {C}.")[0]
        effect = source.paragraph_signals("{1}, {T}, Sacrifice this artifact: Add one mana of any color. Draw a card.")[0]
        both = source.paragraph_signals("{T}, Mill a card: Draw a card. Add {C}.")[0]
        quoted = source.paragraph_signals('Creatures have "{T}: Draw a card. Add {C}."')[0]
        self.assertEqual([cost["movement_location"], effect["movement_location"], both["movement_location"]],
                         ["cost", "effect", "both"])
        self.assertEqual(cost["semantic_verdict"], "not_evaluated")
        self.assertTrue(any("quoted" in ambiguity for ambiguity in quoted["ambiguities"]))
        self.assertFalse(source.paragraph_signals("{T}: Add {G}."))
        self.assertFalse(source.paragraph_signals("Whenever you draw a card, add {G}."))
        self.assertFalse(source.paragraph_signals("{T}: Target creature gains vigilance."))


class FetchTests(unittest.TestCase):
    def test_429_stops_without_retry_and_records_headers(self):
        calls = []
        def opener(request, timeout):
            calls.append(request)
            raise HTTPError(request.full_url, 429, "slow down", {"Retry-After": "30"}, io.BytesIO())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "descriptor.json"
            with self.assertRaisesRegex(source.SourceError, "429"):
                source.Fetcher(opener, lambda delay: None).download(source.DESCRIPTOR_URL, path, 1000)
            self.assertEqual(len(calls), 1)
            meta = json.loads((Path(directory) / "descriptor.json.http.json").read_text())
            self.assertEqual(meta["attempts"][0]["status"], 429)
            self.assertIn(["Retry-After", "30"], meta["attempts"][0]["response_headers"])
            self.assertFalse(path.exists())
            self.assertEqual(calls[0].get_header("User-agent"), source.USER_AGENT)
            self.assertIsNotNone(calls[0].get_header("Accept"))

    def test_download_checks_wire_size_and_hash_before_promoting_evidence(self):
        from email.message import Message
        class Response(io.BytesIO):
            status = 200
            def __init__(self, raw):
                super().__init__(raw)
                self.headers = Message()
                self.headers["Content-Length"] = str(len(raw))
            def geturl(self):
                return "https://data.scryfall.io/fixture.jsonl.gz"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            client = source.Fetcher(lambda request, timeout: Response(b"some bytes"))
            meta = client.download("https://data.scryfall.io/fixture.jsonl.gz", root / "good", 100, 10)
            self.assertEqual(meta["sha256"], source.sha256(b"some bytes"))
            self.assertEqual((root / "good").read_bytes(), b"some bytes")
            with self.assertRaisesRegex(source.SourceError, "size mismatch"):
                client.download("https://data.scryfall.io/fixture.jsonl.gz", root / "wrong", 100, 11)
            self.assertFalse((root / "wrong").exists())
            with self.assertRaisesRegex(source.SourceError, "limit"):
                client.download("https://data.scryfall.io/fixture.jsonl.gz", root / "oversized", 5)

    def test_existing_cache_is_verified_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "snapshot"
            snapshot(target, b'{"a":1}\n')
            class NoNetwork:
                def download(self, *args):
                    raise AssertionError("cache should avoid network")
            self.assertEqual(source.fetch_snapshot(target, fetcher=NoNetwork())["status"], "complete")
            (target / "source.jsonl.gz").write_bytes(b"corrupted")
            with self.assertRaises(source.SourceError):
                source.fetch_snapshot(target, fetcher=NoNetwork())


class ScanTests(unittest.TestCase):
    def test_scan_accounts_for_all_rows_keeps_exact_candidates_and_ranks_deterministically(self):
        rows = [
            card(),
            card(oracle="another-oracle", printing="another-printing",
                 text="{1}, {T}, Sacrifice this artifact: Add {G}. Draw a card."),
            dict(card(oracle="excluded", printing="excluded-printing"), games=["arena"]),
            card(oracle="control", printing="control-printing", text="{T}: Add {G}."),
        ]
        raw_lines = [json.dumps(row, ensure_ascii=False).encode() + b"\n" for row in rows]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot(root / "snapshot", b"".join(raw_lines) + b"broken\n")
            first = source.scan_snapshot(root / "snapshot", root / "one")
            second = source.scan_snapshot(root / "snapshot", root / "two")
            self.assertEqual(first["status"], "complete_with_input_errors")
            self.assertEqual(first["counts"]["source_rows"], 5)
            self.assertEqual(first["counts"]["eligible_records"], 3)
            self.assertEqual(first["counts"]["excluded_records"], 2)
            self.assertEqual(first["counts"]["eligible_weak_candidate_records"], 2)
            self.assertEqual(first["counts"]["all_weak_signal_records"], 3)
            self.assertEqual(first["counts"]["source_decode_errors"], 1)
            one, two = root / "one", root / "two"
            self.assertEqual((one / "candidates.jsonl").read_bytes(), (two / "candidates.jsonl").read_bytes())
            candidates = [json.loads(line) for line in (one / "candidates.jsonl").read_text().splitlines()]
            for candidate in candidates:
                raw = (one / candidate["raw_record_path"]).read_bytes()
                self.assertEqual(source.sha256(raw), candidate["raw_record_sha256"])
                self.assertEqual(raw, raw_lines[candidate["source_index"] - 1])
                self.assertEqual(candidate["semantic_verdict"], "not_evaluated")
            with self.assertRaises(FileExistsError):
                source.scan_snapshot(root / "snapshot", one)


if __name__ == "__main__":
    unittest.main()
