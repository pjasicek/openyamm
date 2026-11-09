"""Synthetic geometry checks; no synthetic image is artwork or queue acceptance."""
import unittest

from PIL import Image, ImageDraw

from review_dense_sheet import opaque_rectangles, sampling, trim_gutter


class DenseExtractionTests(unittest.TestCase):
    def test_measures_returned_boundaries_instead_of_assuming_regular_slots(self):
        image = Image.new('RGB', (260, 350), '#ff00ff')
        draw = ImageDraw.Draw(image)
        boxes = [(4, 4, 122, 162), (133, 4, 251, 162), (4, 178, 122, 336), (133, 178, 251, 336)]
        for x0, y0, x1, y1 in boxes:
            draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill='#667788')
        self.assertEqual(opaque_rectangles(image, 2, 2),
                         [[x, y, x1 - x, y1 - y] for x, y, x1, y1 in boxes])

    def test_sampling_rejects_undersized_cells_even_in_a_large_sheet(self):
        with self.assertRaisesRegex(AssertionError, 'Insufficient'):
            sampling([200, 200, 117, 158], [59, 79])
        self.assertEqual(sampling([10, 10, 118, 158], [59, 79]), [2, 2])

    def test_merged_cells_are_ambiguous(self):
        image = Image.new('RGB', (260, 350), '#ff00ff')
        ImageDraw.Draw(image).rectangle((4, 4, 250, 335), fill='#667788')
        with self.assertRaisesRegex(AssertionError, 'Ambiguous'):
            opaque_rectangles(image, 2, 2)

    def test_distorted_cell_requires_review_instead_of_silent_stretch(self):
        with self.assertRaisesRegex(AssertionError, 'Distorted'):
            sampling([4, 4, 118, 180], [59, 79])

    def test_residual_matte_edge_removed_without_fitting_the_face(self):
        image = Image.new('RGB', (124, 164), '#687868')
        ImageDraw.Draw(image).rectangle((0, 0, 123, 0), fill='#dd33dd')
        self.assertEqual(trim_gutter(image, [0, 0, 124, 164]), [0, 1, 124, 163])


if __name__ == '__main__':
    unittest.main()
