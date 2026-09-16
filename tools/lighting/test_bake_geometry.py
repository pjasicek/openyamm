import unittest

from bake_geometry import face_basis


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
