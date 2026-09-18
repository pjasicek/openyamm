import unittest

from bake_geometry import face_basis, pack_lightmap_charts, rle_bgra


class FaceBasisTests(unittest.TestCase):
    def test_collinear_prefix_retains_visible_rectangle(self):
        points = [(0, 0, 0), (1, 0, 0), (2, 0, 0), (2, 0, 2), (0, 0, 2)]
        axis_u, axis_v = face_basis(points)
        self.assertAlmostEqual(sum(value * value for value in axis_u), 1)
        self.assertAlmostEqual(sum(value * value for value in axis_v), 1)
        self.assertAlmostEqual(sum(u * v for u, v in zip(axis_u, axis_v)), 0)
        # Both axes stay in the vertical face plane, with no collapsed chart dimension.
        self.assertEqual(axis_u[1], 0)
        self.assertEqual(axis_v[1], 0)

    def test_duplicate_prefix_is_not_degenerate(self):
        self.assertIsNotNone(face_basis([(0, 0, 0), (0, 0, 0), (2, 0, 0), (0, 2, 0)]))

    def test_entirely_collinear_face_is_degenerate(self):
        self.assertIsNone(face_basis([(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0)]))
        self.assertIsNone(face_basis([(0, 0, 0)]))

    def test_winding_is_preserved(self):
        axis_u, axis_v = face_basis([(0, 0, 0), (2, 0, 0), (0, 2, 0)])
        self.assertGreater(axis_u[0] * axis_v[1] - axis_u[1] * axis_v[0], 0)
        axis_u, axis_v = face_basis([(0, 0, 0), (0, 2, 0), (2, 0, 0)])
        self.assertLess(axis_u[0] * axis_v[1] - axis_u[1] * axis_v[0], 0)


class LightmapChartPackingTests(unittest.TestCase):
    def test_sorts_charts_and_crops_page_dimensions(self):
        placements, dimensions = pack_lightmap_charts([(20, 10), (40, 30), (20, 10)], 64, padding=4)

        self.assertEqual(dimensions, [(56, 56)])
        self.assertEqual(placements[1], (0, 4, 4, 40, 30))
        self.assertEqual(placements[0], (0, 4, 42, 20, 10))
        self.assertEqual(placements[2], (0, 32, 42, 20, 10))

    def test_clamps_oversized_chart_inside_page(self):
        placements, dimensions = pack_lightmap_charts([(100, 80)], 64, padding=4)

        self.assertEqual(placements, [(0, 4, 4, 56, 56)])
        self.assertEqual(dimensions, [(64, 64)])


class LightmapCompressionTests(unittest.TestCase):
    def test_encodes_literal_and_repeated_texels(self):
        a = bytes((1, 2, 3, 4))
        b = bytes((5, 6, 7, 8))
        c = bytes((9, 10, 11, 12))

        self.assertEqual(rle_bgra(a + b + c + c + c + a),
                         bytes((1,)) + a + b + bytes((0x82,)) + c + bytes((0,)) + a)

    def test_splits_spans_at_128_texels(self):
        pixel = bytes((1, 2, 3, 4))
        encoded = rle_bgra(pixel * 129)

        self.assertEqual(encoded, bytes((0xff,)) + pixel + bytes((0,)) + pixel)
