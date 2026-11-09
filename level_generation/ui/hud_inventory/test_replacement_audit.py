"""Focused checks: technical evidence must not manufacture visual approval."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

import numpy as np
from PIL import Image

from finalize_classification import digest
from replacement_audit import inspect_candidate


class ReplacementAuditTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory(prefix='icon-replacement-test-')
        self.directory = Path(self.temporary.name)
        self.source = self.directory / 'native.png'
        pixels = np.random.default_rng(42).integers(0, 256, (10, 16, 3), dtype=np.uint8)
        Image.fromarray(pixels).save(self.source)
        self.member = dict(id='test-cell', target='test-target', source_path=str(self.source),
                           source_sha256=digest(self.source), source_rect=[0, 0, 16, 10],
                           export_region=[0, 0, 32, 20])
        target = dict(output_path='restored.png', compositing={'profiles': ['hud']})
        self.queue = SimpleNamespace(members={'test-cell': ('test-job', self.member)},
                                     targets={'test-target': target})

    def tearDown(self):
        self.temporary.cleanup()

    def test_exact_nearest_enlargement_is_detected_but_not_visually_approved(self):
        output = self.directory / 'nearest.png'
        with Image.open(self.source) as source:
            source.resize((32, 20), Image.Resampling.NEAREST).save(output)
        result = inspect_candidate('test-cell', output, self.queue, 'test')
        self.assertTrue(result['exact_x2'])
        self.assertEqual(result['aspect_relative_error'], 0)
        self.assertIn('nearest', result['exact_native_resample_matches'])
        self.assertFalse(result['visual_approval'])

    def test_wrong_aspect_is_not_fixed_or_passed(self):
        output = self.directory / 'distorted.png'
        with Image.open(self.source) as source:
            source.resize((40, 20), Image.Resampling.BICUBIC).save(output)
        before = digest(output)
        result = inspect_candidate('test-cell', output, self.queue, 'test')
        self.assertFalse(result['exact_x2'])
        self.assertAlmostEqual(result['aspect_relative_error'], .25)
        self.assertEqual(result['status'], 'geometry_flag')
        self.assertEqual(digest(output), before)

    def test_missing_candidate_stays_unresolved(self):
        result = inspect_candidate('test-cell', self.directory / 'missing.png', self.queue, 'test')
        self.assertEqual(result['status'], 'missing_candidate')
        self.assertFalse(result['visual_approval'])


if __name__ == '__main__':
    unittest.main()
