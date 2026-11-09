"""Receipt validation must preserve provenance and reject contradictory external logs."""
import unittest
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

from import_chat_returns import digest, provenance_receipts, reconcile_prior_intake


class ProvenanceTests(unittest.TestCase):
    def test_rebuilt_return_reuses_only_identical_raw_prompt_and_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / 'outputs/raw/S001.png'
            prompt = root / 'outputs/prompts/S001.txt'
            candidate = root / 'outputs/processed/S001/face.png'
            for path, value in ((raw, b'raw'), (prompt, b'exact prompt'), (candidate, b'candidate')):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(value)
            old_raw = root / 'old-raw.png'; old_raw.write_bytes(raw.read_bytes())
            old_art = root / 'old-candidate.png'; old_art.write_bytes(candidate.read_bytes())
            archive = root / 'partial.zip'; archive.write_bytes(b'retained archive')
            payload = root / 'payload.json'
            payload.write_text(json.dumps(dict(external_return=dict(bundle='bundle', sheet='S001'),
                selected_cells=['face'], prompt='exact prompt')))
            attempt = dict(id='existing-attempt', payload=str(payload), raw=str(old_raw), sha256=digest(old_raw))
            prior = root / 'intake.json'
            prior.write_text(json.dumps(dict(bundle='bundle', archive=str(archive), archive_sha256=digest(archive),
                cells=[dict(cell='face', sheet='S001', attempt=attempt['id'],
                            artifact=str(old_art), artifact_sha256=digest(old_art))])))
            manifest = dict(bundle_id='bundle', sheets=[dict(id='S001', cells=['face'])])
            q = SimpleNamespace(state=dict(attempts=[attempt]))
            _, reused = reconcile_prior_intake(prior, manifest, root, q)
            self.assertEqual(reused, {'S001': attempt})
            for path in (raw, prompt, candidate):
                original = path.read_bytes()
                path.write_bytes(b'changed')
                with self.assertRaises(AssertionError):
                    reconcile_prior_intake(prior, manifest, root, q)
                path.write_bytes(original)
            with self.assertRaises(AssertionError):
                reconcile_prior_intake(prior, dict(manifest, bundle_id='other'), root, q)

    def test_known_return_formats_retain_original_records(self):
        row = dict(sheet='S001', sha256='raw', prompt_sha256='prompt', returned_filename='actual.png')
        for ledger in ([row], {'generation_calls': [row]}, {'sheets': [row]}, {'S001': row}):
            receipt = provenance_receipts(ledger)['S001']
            self.assertEqual(receipt['raw_sha256'], 'raw')
            self.assertEqual(receipt['submitted_prompt_sha256'], 'prompt')
            self.assertEqual(receipt['model_returned_filename'], 'actual.png')
            self.assertEqual(receipt['records'], [row])

    def test_redundant_file_ledger_is_verified_not_discarded(self):
        row = dict(sheet='S001', raw_sha256='raw', submitted_prompt_sha256='prompt')
        extra = dict(sheet='S001', sha256='raw', filename='actual.png')
        ledger = dict(generation_calls=[row], model_returned_files=[extra])
        receipt = provenance_receipts(ledger)['S001']
        self.assertEqual(receipt['model_returned_filename'], 'actual.png')
        self.assertEqual(receipt['records'], [row, extra])
        extra['sha256'] = 'different-raw'
        with self.assertRaises(AssertionError):
            provenance_receipts(ledger)

    def test_nested_sheet_map_retains_actual_filename(self):
        row = dict(raw_sha256='raw', actual_model_returned_filename='actual.png')
        receipt = provenance_receipts(dict(sheets={'S001': row}))['S001']
        self.assertEqual(receipt['raw_sha256'], 'raw')
        self.assertEqual(receipt['model_returned_filename'], 'actual.png')
        with self.assertRaises(AssertionError):
            provenance_receipts(dict(sheets={'S001': dict(row, sheet='S002')}))

    def test_conflicting_aliases_and_unknown_shapes_are_rejected(self):
        for ledger in ([dict(sheet='S001', raw_sha256='one', sha256='two')],
                       {'other': []}, [dict(sheet='../raw')]):
            with self.assertRaises(AssertionError):
                provenance_receipts(ledger)


if __name__ == '__main__':
    unittest.main()
