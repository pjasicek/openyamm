#!/usr/bin/env python3
"""Conventions of the surface material maps (tools/surface_materials.py) that the shaders rely on."""
import unittest

import numpy as np

import surface_materials


def bump(size=64):
    rows, columns = np.mgrid[:size, :size]
    return np.exp(-((columns - size // 2) ** 2 + (rows - size // 2) ** 2) / 100.0).astype(np.float32)


class BuildMapsTest(unittest.TestCase):
    def setUp(self):
        self.classes = surface_materials.load_classes()
        self.brick = [entry['name'] for entry in self.classes].index('brick')
        self.glass = [entry['name'] for entry in self.classes].index('glass')

    def maps(self, height, index, wrap='uv'):
        master = np.full(height.shape + (4,), 128, np.uint8)
        indices = np.full(height.shape, index, np.int32)
        return surface_materials.build_maps(master, height, indices, self.classes, {'wrap': wrap})

    def test_normal_faces_away_from_a_bump(self):
        normal, _ = self.maps(bump(), self.brick)
        # +x along +u (right), +y up the image (smaller rows).
        self.assertLess(normal[32, 24, 0], 128)
        self.assertGreater(normal[32, 40, 0], 128)
        self.assertGreater(normal[24, 32, 1], 128)
        self.assertLess(normal[40, 32, 1], 128)

    def test_height_is_one_at_the_face_plane_and_scaled_by_depth(self):
        _, detail = self.maps(bump(), self.brick)
        self.assertEqual(detail[32, 32, 3], 255)
        depth = next(entry['depth'] for entry in self.classes if entry['name'] == 'brick')
        expected = round((1.0 - depth / surface_materials.MAX_DEPTH) * 255)
        self.assertAlmostEqual(int(detail[0, 0, 3]), expected, delta=1)

    def test_glass_glows_at_night_only(self):
        normal, _ = self.maps(np.ones((16, 16), np.float32), self.glass)
        self.assertGreater(normal[8, 8, 2], 0)
        self.assertLessEqual(normal[8, 8, 2], round(0.45 * 255))

    def test_edges_that_do_not_wrap_flatten_to_the_face_plane(self):
        height = np.zeros((64, 64), np.float32)
        height[:, 32:] = 1.0
        normal, detail = self.maps(height, self.brick, wrap='')
        self.assertEqual(detail[32, 0, 3], 255)
        self.assertEqual(tuple(normal[32, 0, :2]), (128, 128))


if __name__ == '__main__':
    unittest.main()
