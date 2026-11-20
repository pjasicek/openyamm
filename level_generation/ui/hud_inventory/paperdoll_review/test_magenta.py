import unittest
from PIL import Image, ImageDraw
from scan_magenta import measure, classify


class MagentaScreenTests(unittest.TestCase):
    def test_invisible_rgb_is_ignored(self):
        self.assertEqual(measure(Image.new('RGBA', (20, 20), (255, 0, 255, 0)))['key_pixels'], 0)

    def test_neutral_shape_with_magenta_rim_is_flagged(self):
        native = Image.new('RGBA', (30, 30))
        ImageDraw.Draw(native).rectangle((5, 5, 24, 24), fill=(150, 150, 150, 255))
        candidate = native.copy()
        ImageDraw.Draw(candidate).line((5, 5, 5, 24), fill=(255, 0, 255, 255), width=2)
        self.assertEqual(classify(measure(candidate), measure(native)), 'suspected_magenta_spill')
        self.assertEqual(classify(measure(native), measure(native)), 'no_spill_detected')

    def test_known_purple_is_separate_from_spill(self):
        image = Image.new('RGBA', (30, 30))
        ImageDraw.Draw(image).rectangle((5, 5, 24, 24), fill=(180, 60, 160, 255))
        self.assertEqual(classify(measure(image), measure(image)), 'purple_material_check')


if __name__ == '__main__':
    unittest.main()
