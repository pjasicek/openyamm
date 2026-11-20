"""Check that matte removal does not treat intentional purple as contamination."""
import unittest

import numpy as np
from PIL import Image

from matte import extract


class MatteTests(unittest.TestCase):
    def test_opaque_purple_core_is_preserved_with_soft_border_unmixed(self):
        pixels = np.full((40, 40, 3), [255, 0, 255], dtype='uint8')
        purple = np.array([160, 40, 180])
        pixels[7:33, 7:33] = np.round((purple + [255, 0, 255]) / 2).astype('uint8')
        pixels[8:32, 8:32] = purple
        result, stats = extract(Image.fromarray(pixels), core_radius=2)
        output = np.array(result)
        self.assertEqual(list(output[20, 20]), [160, 40, 180, 255])
        self.assertEqual(int(output[0, 0, 3]), 0)
        self.assertTrue(stats['protected_core_rgb_unchanged'])
        self.assertLessEqual(abs(int(output[7, 20, 3]) - 128), 2)
        self.assertTrue(np.all(np.abs(output[7, 20, :3].astype(int) - purple) <= 2))

    def test_missing_foreground_is_not_a_successful_empty_export(self):
        with self.assertRaisesRegex(AssertionError, 'actual foreground'):
            extract(Image.new('RGB', (20, 20), (255, 0, 255)))

    def test_thin_colored_bowstring_survives_far_from_solid_foreground(self):
        pixels = np.full((60, 40, 3), [255, 0, 255], dtype='uint8')
        pixels[5:55, 24:34] = [90, 60, 30]
        pixels[5:55, 2] = [103, 137, 56]
        result, _ = extract(Image.fromarray(pixels), preserve_thin_lines=True)
        output = np.array(result)
        self.assertTrue(np.all(output[5:55, 2, 3] == 255))
        self.assertTrue(np.all(output[5:55, 2, :3] == [103, 137, 56]))
        self.assertTrue(np.all(output[:, 12, 3] == 0))


if __name__ == '__main__':
    unittest.main()
