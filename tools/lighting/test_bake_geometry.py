import unittest

from bake_geometry import (face_basis, group_coplanar_faces, newell_normal, pack_lightmap_charts,
                           plane_chart_basis, rle_bgra, terrain_triangles_on_floors)


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


class IndoorChartTests(unittest.TestCase):
    def test_floor_and_wall_bases_are_world_aligned(self):
        self.assertEqual(plane_chart_basis((0.0, 0.0, 1.0)), ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))
        axis_u, axis_v = plane_chart_basis((1.0, 0.0, 0.0))
        self.assertEqual(axis_u, (0.0, 1.0, 0.0))
        self.assertEqual(axis_v, (0.0, 0.0, 1.0))

    def test_newell_normal_follows_winding(self):
        self.assertEqual(newell_normal([(0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0)]), (0.0, 0.0, 8.0))

    def test_faces_split_at_a_portal_share_a_chart(self):
        up = (0.0, 0.0, 1.0)
        left = [(0, 0, 0), (100, 0, 0), (100, 100, 0), (0, 100, 0)]
        right = [(100, 0, 0), (200, 0, 0), (200, 100, 0), (100, 100, 0)]
        # Back to back with the right one, and a parallel floor one unit higher: neither joins.
        below = [(100, 0, 0), (100, 100, 0), (200, 100, 0), (200, 0, 0)]
        higher = [(200, 0, 1), (300, 0, 1), (300, 100, 1), (200, 100, 1)]
        groups = group_coplanar_faces([(left, up), (right, up), (below, (0.0, 0.0, -1.0)), (higher, up)])
        self.assertEqual(groups, [[0, 1], [2], [3]])

    def test_touching_faces_far_apart_in_l_shape_keep_their_own_charts(self):
        up = (0.0, 0.0, 1.0)
        corridor = [(0, 0, 0), (1000, 0, 0), (1000, 100, 0), (0, 100, 0)]
        branch = [(900, 100, 0), (1000, 100, 0), (1000, 1000, 0), (900, 1000, 0)]
        self.assertEqual(group_coplanar_faces([(corridor, up), (branch, up)]), [[0], [1]])

    def test_first_fit_fills_shelves_before_opening_new_ones(self):
        sizes = [(10, 10)] + [(10, 4)] * 4
        _, best = pack_lightmap_charts(sizes, 64, padding=1)
        placements, first = pack_lightmap_charts(sizes, 64, padding=1, first_fit=True)
        self.assertEqual(first, [(60, 12)])
        self.assertGreater(best[0][1], first[0][1])
        self.assertTrue(all(page == 0 and y == 1 for page, _, y, _, _ in placements))


class TerrainOnFloorTests(unittest.TestCase):
    # Ravenshore (MM8 out02.odm): the crystal stands on a terrain plateau of height 320 (native 10) over a pit, and
    # its four models' DIRTtyl floors at z 320 cover the plateau around the crystal.
    PLATEAU = {81: [10, 10, 10, 10], 82: [10, 3, 5, 10], 83: [10, 6, 3, 10], 84: [10, 3, 4, 10],
               85: [10, 10, 10, 10]}
    FLOORS = [
        [(14336, -10000), (14480, -10000), (14624, -9792), (14544, -9696), (14336, -9696)],
        [(14560, -10208), (14336, -10752), (14752, -10336), (14688, -10224)],
        [(14576, -10080), (14480, -10000), (14336, -10000), (14336, -10752), (14560, -10208)],
        [(14944, -10368), (14864, -10272), (14752, -10336), (14336, -10752), (14944, -10752)],
        [(15408, -9040), (15408, -8704), (15104, -8704), (15104, -9072), (15344, -9128)],
        [(14896, -9136), (15024, -9168), (15104, -9072), (15104, -8704), (14896, -8704)],
        [(14688, -9152), (14336, -8704), (14544, -9360)],
        [(14896, -9136), (14896, -8704), (14336, -8704), (14688, -9152), (14800, -9216)],
        [(14544, -9360), (14336, -9360), (14336, -9696), (14544, -9696), (14624, -9600)],
        [(14544, -9360), (14336, -8704), (14336, -9360)],
        [(15408, -9040), (15616, -9184), (15872, -8704), (15408, -8704)],
        [(15616, -9184), (15680, -9296), (15872, -8704)],
        [(15680, -9296), (15872, -9296), (15872, -8704)],
        [(15552, -9520), (15648, -9760), (15872, -9760), (15872, -9296), (15680, -9296)],
        [(15520, -10288), (15408, -10272), (15296, -10336), (15872, -10752)],
        [(15520, -10288), (15872, -10752), (15600, -10192)],
        [(15600, -10064), (15600, -10192), (15872, -10752), (15872, -10064)],
        [(15648, -9760), (15536, -9824), (15536, -9952), (15600, -10064), (15872, -10064), (15872, -9760)],
        [(15872, -10752), (15296, -10336), (15184, -10272), (14944, -10368), (14944, -10752)],
    ]

    def heights(self):
        heights = [0] * (128 * 128)
        for gy, row in self.PLATEAU.items():
            for offset, height in enumerate(row):
                heights[gy * 128 + 92 + offset] = height
        return heights

    def test_ravenshore_crystal_plaza_corners(self):
        floors = [(320, polygon) for polygon in self.FLOORS]
        # Only the north-east and south-west corner cells hold a triangle flat at 320: the native diagonal of the
        # north-west and south-east corner cells runs through the pit, so neither of their triangles is flat.
        self.assertEqual(terrain_triangles_on_floors(self.heights(), floors), [(94, 81, 0), (92, 84, 1)])

    def test_floor_at_another_height_is_ignored(self):
        self.assertEqual(terrain_triangles_on_floors(self.heights(), [(352, p) for p in self.FLOORS]), [])

    def test_small_floor_inside_one_triangle(self):
        # Cell (64, 63) spans x 0..512, y 0..512; its second triangle is the half nearer the origin.
        flat = [0] * (128 * 128)
        self.assertEqual(terrain_triangles_on_floors(flat, [(0, [(10, 10), (60, 10), (10, 60)])]), [(64, 63, 1)])
        self.assertEqual(terrain_triangles_on_floors(flat, [(32, [(10, 10), (60, 10), (10, 60)])]), [])
