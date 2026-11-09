"""An audited input revision must remain pinned to its catalog, snapshots, and live files."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from queue import validate_input_hashes


class InputReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name, value in [('before.txt', 'old'), ('after.txt', 'new'), ('live.txt', 'new')]:
            (self.root / name).write_text(value)
        self.inputs = {'live.txt': self.sha('before.txt')}
        self.receipt = {
            'schema': 'openyamm-icon-input-reconciliation-v1', 'frozen_manifest_sha256': 'catalog-one',
            'inputs': {'live.txt': {
                'frozen_sha256': self.sha('before.txt'), 'current_sha256': self.sha('after.txt'),
                'before_snapshot': 'before.txt', 'current_snapshot': 'after.txt',
            }},
        }
        self.publish()

    def sha(self, name):
        return hashlib.sha256((self.root / name).read_bytes()).hexdigest()

    def publish(self):
        (self.root / 'receipt.json').write_text(json.dumps(self.receipt))
        self.pointer = {'path': 'receipt.json', 'sha256': self.sha('receipt.json')}

    def validate(self):
        validate_input_hashes(self.inputs, self.pointer, 'catalog-one', self.root)

    def test_no_receipt_still_requires_original_bytes(self):
        with self.assertRaisesRegex(AssertionError, 'Input drift'):
            validate_input_hashes(self.inputs, None, 'catalog-one', self.root)
        (self.root / 'live.txt').write_text('old')
        validate_input_hashes(self.inputs, None, 'catalog-one', self.root)

    def test_exact_reconciliation_passes(self):
        self.validate()

    def test_future_unreviewed_change_fails(self):
        (self.root / 'live.txt').write_text('another revision')
        with self.assertRaisesRegex(AssertionError, 'Input drift'):
            self.validate()

    def test_receipt_cannot_change_without_ledger_update(self):
        (self.root / 'receipt.json').write_text('{}')
        with self.assertRaisesRegex(AssertionError, 'receipt changed'):
            self.validate()

    def test_catalog_and_baseline_are_bound(self):
        with self.assertRaisesRegex(AssertionError, 'another catalog'):
            validate_input_hashes(self.inputs, self.pointer, 'catalog-two', self.root)
        self.receipt['inputs']['live.txt']['frozen_sha256'] = 'wrong-baseline'
        self.publish()
        with self.assertRaisesRegex(AssertionError, 'baseline differs'):
            self.validate()

    def test_unknown_input_is_rejected(self):
        self.receipt['inputs']['unknown.txt'] = self.receipt['inputs']['live.txt']
        self.publish()
        with self.assertRaisesRegex(AssertionError, 'Unregistered'):
            self.validate()

    def test_snapshots_must_remain_available_and_unchanged(self):
        (self.root / 'after.txt').write_text('edited snapshot')
        with self.assertRaisesRegex(AssertionError, 'snapshot changed'):
            self.validate()


if __name__ == '__main__':
    unittest.main()
