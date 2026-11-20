import unittest

import numpy as np
from PIL import Image

from local_geometry import deform, transform_points


class LocalGeometryTests(unittest.TestCase):
    def fixture(self):
        pixels = np.zeros((41, 41, 4), dtype=np.uint8)
        pixels[12:29, 12:29] = [180, 90, 30, 255]
        return Image.fromarray(pixels), Image.fromarray(pixels[:, :, 3])

    def specification(self, controls):
        return dict(reason='Test explicit local geometry', authorization='Test fixture', controls=controls)

    def test_identity_preserves_color_alpha_and_mask(self):
        image, mask = self.fixture()
        result, coverage, record = deform(image, mask, self.specification([]))
        np.testing.assert_array_equal(result, image)
        np.testing.assert_array_equal(coverage, mask)
        self.assertAlmostEqual(record['maximum_occupied_expansion'], 1)

    def test_joint_moves_and_uses_identical_mask_mapping(self):
        image, mask = self.fixture()
        result, coverage, record = deform(image, mask, self.specification([
            dict(source_raw=[20, 20], target_raw=[20, 24])]))
        np.testing.assert_allclose(transform_points([[20, 20], [0, 0]], record), [[20, 24], [0, 0]])
        self.assertLessEqual(np.abs(np.array(result)[:, :, 3].astype(int)-np.array(coverage)).max(), 1)
        pixels = np.array(result)
        np.testing.assert_array_equal(pixels[:, :, :3][pixels[:, :, 3] > 0],
                                      np.tile([180, 90, 30], ((pixels[:, :, 3] > 0).sum(), 1)))
        self.assertGreater(record['maximum_occupied_expansion'], 1)

    def test_rejects_folded_mesh(self):
        image, mask = self.fixture()
        with self.assertRaisesRegex(AssertionError, 'Folded|collapsed'):
            deform(image, mask, self.specification([
                dict(source_raw=[10, 10], target_raw=[30, 30]),
                dict(source_raw=[30, 30], target_raw=[10, 10])]))


if __name__ == '__main__':
    unittest.main()
