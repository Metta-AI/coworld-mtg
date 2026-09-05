import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class CaseCorpusTest(unittest.TestCase):
    def test_cross_check_refuses_wrong_identity_or_text_and_keeps_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases = root / 'cases'
            cases.mkdir()
            (cases / 'one.json').write_text(json.dumps({'scenario': {'cards': [{'name': 'Example'}]}}))
            export = {'example': {'name': 'Example', 'scryfall_oracle_id': 'id-a', 'oracle_text': 'Draw a card.'}}
            oracle = [{'name': 'Example', 'oracle_id': 'id-a', 'oracle_text': 'Draw a card.', 'scryfall_uri': 'https://scryfall.com/card/test/1/example'}]
            phase_path, oracle_path = root / 'phase.json', root / 'oracle.json'
            phase_path.write_text(json.dumps(export))
            oracle_path.write_text(json.dumps(oracle))

            def run(output):
                return subprocess.run(['python3', str(ROOT / 'scripts/prepare-case-corpus.py'),
                                       '--phase-export', str(phase_path), '--scryfall', str(oracle_path),
                                       '--cases', str(cases), '--output-dir', str(output)], capture_output=True)

            output = root / 'good'
            self.assertEqual(run(output).returncode, 0)
            original = (output / 'corpus.json').read_bytes()
            self.assertNotEqual(run(output).returncode, 0)
            self.assertEqual((output / 'corpus.json').read_bytes(), original)
            oracle[0]['oracle_id'] = 'id-b'
            oracle_path.write_text(json.dumps(oracle))
            self.assertNotEqual(run(root / 'wrong-id').returncode, 0)
            oracle[0]['oracle_id'] = 'id-a'
            oracle[0]['oracle_text'] = 'Draw two cards.'
            oracle_path.write_text(json.dumps(oracle))
            self.assertNotEqual(run(root / 'wrong-text').returncode, 0)
            self.assertFalse((root / 'wrong-id').exists())
            self.assertFalse((root / 'wrong-text').exists())
