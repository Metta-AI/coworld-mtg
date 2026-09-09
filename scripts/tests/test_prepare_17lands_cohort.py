"""Protocol fixtures test byte selection/provenance, not gameplay semantics."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "prepare_17lands_cohort.py"
SPEC = importlib.util.spec_from_file_location("prepare_17lands_cohort", MODULE)
cohort = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cohort)


class PrepareCohortTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.header = b'on_play,num_mulligans,opp_num_mulligans,opening_hand,note\r\n'
        self.rows = [
            b'True,0,0,101|101,"quoted,\r\nmultiline"\r\n',
            b'False,1,,102,"second"\r\n',
            b',,0,,"third"\r\n',
        ]
        self.archive = self.root / "source.csv.gz"
        self.archive.write_bytes(gzip.compress(self.header + b"".join(self.rows), mtime=0))
        self.mapping = self.root / "cards.csv"
        self.mapping.write_bytes(b'id,name\r\n101,Unit fixture A\r\n102,Unit fixture B\r\n')

    def prepare(self, name="output", **changes):
        args = dict(
            archive=self.archive,
            archive_sha256=hashlib.sha256(self.archive.read_bytes()).hexdigest(),
            source_url="https://example.org/test-only.csv.gz",
            cards_csv=self.mapping,
            cards_sha256=hashlib.sha256(self.mapping.read_bytes()).hexdigest(),
            output_dir=self.root / name,
            count=3,
            development_rows=(1,),
            previously_inspected_prefix=3,
        )
        args.update(changes)
        return cohort.prepare_cohort(**args)

    def test_exact_rows_line_endings_offsets_and_no_filtering(self):
        manifest = self.prepare()
        self.assertEqual((self.root / "output/games.csv").read_bytes(),
                         self.header + b"".join(self.rows))
        self.assertEqual((self.root / "output/cards.csv").read_bytes(),
                         self.mapping.read_bytes())
        self.assertEqual([c["source_row_index"] for c in manifest["cases"]], [0, 1, 2])
        self.assertEqual([c["game_index"] for c in manifest["cases"]], [0, 1, 2])
        self.assertEqual([c["role"] for c in manifest["cases"]],
                         ["evaluation", "development", "evaluation"])
        offset = len(self.header)
        for case, raw in zip(manifest["cases"], self.rows):
            self.assertEqual(case["decompressed_byte_offset"], offset)
            self.assertEqual(case["source_row_sha256"], hashlib.sha256(raw).hexdigest())
            offset += len(raw)
        self.assertEqual(manifest["cases"][1]["raw_metadata"]["num_mulligans"], "1")
        self.assertEqual(manifest["cases"][1]["metadata_presence"]["opp_num_mulligans"], "blank")

    def test_start_row_changes_fixture_index_without_changing_source_identity(self):
        m = self.prepare(start_row=1, count=2, development_rows=(1,))
        self.assertEqual([c["game_index"] for c in m["cases"]], [0, 1])
        self.assertEqual([c["source_row_index"] for c in m["cases"]], [1, 2])
        self.assertEqual((self.root / "output/games.csv").read_bytes(),
                         self.header + b"".join(self.rows[1:]))

    def test_identical_inputs_produce_identical_public_bytes(self):
        self.prepare("a")
        self.prepare("b")
        for name in ("games.csv", "cards.csv", "cohort.json"):
            self.assertEqual((self.root / "a" / name).read_bytes(),
                             (self.root / "b" / name).read_bytes())
        m = json.loads((self.root / "a/cohort.json").read_text())
        self.assertFalse(m["selection"]["unseen_holdout"])
        self.assertIsNone(m["source"]["retrieved_at"])
        self.assertNotIn(str(self.root), json.dumps(m))

    def test_bad_archive_or_mapping_hash_creates_no_output(self):
        for field in ("archive_sha256", "cards_sha256"):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                    self.prepare(**{field: "0" * 64})
                self.assertFalse((self.root / "output").exists())

    def test_existing_output_is_immutable(self):
        output = self.root / "output"
        output.mkdir()
        (output / "sentinel").write_bytes(b"retained")
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.prepare()
        self.assertEqual(list(output.iterdir()), [output / "sentinel"])
        self.assertEqual((output / "sentinel").read_bytes(), b"retained")

    def test_short_or_corrupt_csv_and_byte_limit_leave_no_partial_output(self):
        for args in ({"count": 4}, {"max_csv_bytes": len(self.header) + 2}):
            with self.assertRaises(ValueError):
                self.prepare(**args)
            self.assertFalse((self.root / "output").exists())
        self.archive.write_bytes(gzip.compress(self.header + b"True,0\n", mtime=0))
        with self.assertRaisesRegex(ValueError, "field count"):
            self.prepare(count=1, development_rows=())
        self.assertFalse((self.root / "output").exists())

    def test_missing_metadata_is_not_known_zero(self):
        self.archive.write_bytes(gzip.compress(b'on_play,note\r\nTrue,unit\r\n', mtime=0))
        m = self.prepare(count=1, development_rows=())
        case = m["cases"][0]
        self.assertIsNone(case["raw_metadata"]["num_mulligans"])
        self.assertEqual(case["metadata_presence"]["num_mulligans"], "missing_column")

    def test_development_labels_cannot_name_unselected_rows(self):
        with self.assertRaisesRegex(ValueError, "must belong"):
            self.prepare(development_rows=(9,))
        self.assertFalse((self.root / "output").exists())


if __name__ == "__main__":
    unittest.main()

