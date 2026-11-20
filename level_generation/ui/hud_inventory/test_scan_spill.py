"""Guard against erasing legitimate materials or counting invisible/keyed backgrounds."""
import unittest

import numpy as np
from PIL import Image, ImageDraw

from scan_spill import measure, suppress_sheet_matte


def shape(color=(135, 125, 115, 255)):
    image = Image.new('RGBA', (48, 48))
    ImageDraw.Draw(image).rectangle((8, 8, 39, 39), fill=color)
    return image


class SpillScreenTests(unittest.TestCase):
    def test_hidden_key_rgb_is_ignored(self):
        for color in [(255, 0, 255, 0), (0, 255, 0, 0), (0, 252, 252, 0)]:
            self.assertEqual(measure(Image.new('RGBA', (20, 20), color))[0]['status'], 'no_spill_detected')

    def test_neutral_art_has_no_findings(self):
        self.assertEqual(measure(shape(), shape())[0]['status'], 'no_spill_detected')

    def test_mixed_chroma_rims_are_detected(self):
        for name, color in [('magenta', (170, 100, 165, 255)),
                            ('green', (95, 170, 100, 255)), ('cyan', (95, 170, 170, 255))]:
            with self.subTest(name=name):
                image = shape()
                ImageDraw.Draw(image).line((8, 10, 8, 35), fill=color, width=2)
                self.assertEqual(measure(image, shape())[0]['colors'][name]['status'], 'likely_spill')

    def test_existing_green_and_purple_materials_need_review(self):
        for name, color in [('magenta', (175, 65, 170, 255)), ('green', (50, 170, 55, 255)),
                            ('cyan', (50, 170, 175, 255))]:
            image = shape(color)
            self.assertEqual(measure(image, image)[0]['colors'][name]['status'], 'color_material_review')

    def test_opaque_canvas_border_is_scanned(self):
        native = Image.new('RGBA', (48, 48), (120, 120, 120, 255))
        image = native.copy()
        ImageDraw.Draw(image).line((0, 0, 0, 47), fill=(240, 30, 240, 255))
        self.assertEqual(measure(image, native)[0]['status'], 'likely_spill')

    def test_moderate_opaque_green_background_is_not_a_confirmed_fringe(self):
        native = Image.new('RGBA', (48, 48), (80, 90, 80, 255))
        image = native.copy()
        ImageDraw.Draw(image).line((0, 0, 0, 47), fill=(80, 120, 80, 255))
        self.assertEqual(measure(image, native)[0]['status'], 'color_material_review')
        ImageDraw.Draw(image).line((0, 0, 0, 47), fill=(0, 255, 0, 255))
        self.assertEqual(measure(image, native)[0]['status'], 'likely_spill')

    def test_translucent_visible_fringe_counts_but_one_pixel_is_trace(self):
        image = shape()
        ImageDraw.Draw(image).line((8, 10, 8, 35), fill=(255, 0, 255, 80))
        self.assertEqual(measure(image, shape())[0]['status'], 'likely_spill')
        image = shape()
        image.putpixel((8, 8), (255, 0, 255, 255))
        self.assertEqual(measure(image, shape())[0]['status'], 'trace')

    def test_tiny_gem_does_not_exempt_spill_elsewhere(self):
        native = shape()
        ImageDraw.Draw(native).rectangle((28, 28, 32, 32), fill=(255, 0, 255, 255))
        image = native.copy()
        ImageDraw.Draw(image).line((8, 10, 8, 35), fill=(220, 40, 220, 255))
        self.assertEqual(measure(image, native)[0]['colors']['magenta']['status'], 'likely_spill')

    def test_sheet_backing_is_excluded_but_soft_spill_remains(self):
        raw = Image.new('RGBA', (48, 48), (255, 0, 255, 255))
        ImageDraw.Draw(raw).rectangle((8, 8, 39, 39), fill=(130, 130, 130, 255))
        ImageDraw.Draw(raw).line((8, 10, 8, 35), fill=(170, 100, 165, 255))
        before = raw.tobytes()
        diagnostic, removed = suppress_sheet_matte(raw)
        self.assertGreater(removed['magenta'], 0)
        self.assertEqual(diagnostic.getpixel((0, 0))[3], 0)
        self.assertEqual(measure(diagnostic, shape())[0]['status'], 'likely_spill')
        self.assertEqual(raw.tobytes(), before)

    def test_accepted_key_blob_inside_hole_is_not_ignored(self):
        image = shape()
        ImageDraw.Draw(image).rectangle((21, 21, 24, 24), fill=(255, 0, 255, 255))
        result, masks = measure(image, shape())
        self.assertEqual(result['status'], 'likely_spill')
        self.assertTrue(np.any(masks['magenta'][21:25, 21:25]))


if __name__ == '__main__':
    unittest.main()
