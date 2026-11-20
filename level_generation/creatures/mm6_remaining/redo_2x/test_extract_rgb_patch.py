"""Local generated detail must not alter surrounding accepted artwork or alpha."""
import hashlib
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image

from extract_run import apply_rgb_patch


class InteriorPatchTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.source = Path(self.directory.name) / 'donor.png'
        Image.new('RGBA', (12, 12), (180, 100, 80, 252)).save(self.source)
        self.clean = Image.new('RGBA', (16, 16), (30, 20, 10, 253))
        self.patch = dict(source=str(self.source),
                          source_sha256=hashlib.sha256(self.source.read_bytes()).hexdigest(),
                          input_rgba_sha256=hashlib.sha256(self.clean.tobytes()).hexdigest(),
                          source_rect=[0, 0, 12, 12], target_rect=[4, 5, 10, 11],
                          feather_px=2, reason='Test interior detail composition')

    def test_only_requested_rgb_changes_and_alpha_is_exact(self):
        before = np.array(self.clean)
        after = np.array(apply_rgb_patch(self.clean, self.patch))
        np.testing.assert_array_equal(before[:, :, 3], after[:, :, 3])
        outside = np.ones(before.shape[:2], dtype=bool)
        outside[5:11, 4:10] = False
        np.testing.assert_array_equal(before[outside], after[outside])
        # Pillow's RGBA resampling may round one color level during premultiplication.
        np.testing.assert_allclose(after[7, 7, :3], [180, 100, 80], atol=1)
        self.assertLess(after[5, 4, 0], after[7, 7, 0])
        np.testing.assert_array_equal(np.array(self.clean), before)

    def test_stale_source_or_base_is_rejected(self):
        for field in ('source_sha256', 'input_rgba_sha256'):
            with self.subTest(field=field), self.assertRaises(AssertionError):
                apply_rgb_patch(self.clean, dict(self.patch, **{field: 'stale'}))

    def test_enlargement_and_out_of_bounds_are_rejected(self):
        for rect in ([0, 0, 16, 16], [-1, 0, 5, 6], [12, 12, 18, 18]):
            with self.subTest(rect=rect), self.assertRaises(AssertionError):
                apply_rgb_patch(self.clean, dict(self.patch, target_rect=rect))

    def test_transparent_donor_is_rejected(self):
        Image.new('RGBA', (12, 12), (180, 100, 80, 0)).save(self.source)
        self.patch['source_sha256'] = hashlib.sha256(self.source.read_bytes()).hexdigest()
        with self.assertRaisesRegex(AssertionError, 'interior artwork'):
            apply_rgb_patch(self.clean, self.patch)


if __name__ == '__main__':
    unittest.main()
