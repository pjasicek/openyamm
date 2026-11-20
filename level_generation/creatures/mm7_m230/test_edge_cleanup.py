"""Focused regressions for the observed m230 fringe and alpha-preserving resize correction."""
import unittest

import numpy as np
from PIL import Image
from scipy import ndimage

from process import matte, resize_base


class EdgeCleanupTests(unittest.TestCase):
    def test_red_minimum_spill_preserves_alpha_and_clean_core(self):
        # Actual m230ad1 foreground/edge colors: blue-only subtraction left purple here.
        rgb = np.full((20, 20, 3), (255, 0, 255), dtype=np.uint8)
        rgb[4:16, 4:16] = (142, 136, 183)
        rgb[3, 8] = (105, 41, 137)
        result = np.asarray(matte.extract(Image.fromarray(rgb))[0])
        self.assertTrue(np.array_equal(result[4:16, 4:16, :3], rgb[4:16, 4:16]))
        # Frozen pre-fix matte alpha for this isolated color fixture.
        self.assertEqual(int(result[3, 8, 3]), 217)
        self.assertLessEqual(min(int(result[3, 8, 0]), int(result[3, 8, 2])) - int(result[3, 8, 1]), 10)
        self.assertTrue(np.all(result[0, :, 3] == 0))

    def test_resize_preserves_alpha_and_noncontour_pixels(self):
        rgba = np.zeros((24, 24, 4), dtype=np.uint8)
        rgba[3:21, 3:21] = (120, 50, 140, 255)
        source = Image.fromarray(rgba)
        ordinary = np.asarray(source.convert('RGBa').resize((36, 36), Image.Resampling.LANCZOS).convert('RGBA'))
        corrected = np.asarray(resize_base(source, (36, 36)))
        self.assertTrue(np.array_equal(ordinary[:, :, 3], corrected[:, :, 3]))
        alpha = ordinary[:, :, 3]
        band = (alpha > 0) & ((ndimage.distance_transform_edt(alpha >= 128) <= 4) | (alpha < 255))
        self.assertTrue(np.array_equal(ordinary[~band], corrected[~band]))
        rgb = corrected[:, :, :3].astype(int)
        self.assertLessEqual(int((np.minimum(rgb[:, :, 0], rgb[:, :, 2]) - rgb[:, :, 1])[band].max()), 10)


if __name__ == '__main__':
    unittest.main()
