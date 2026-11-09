import unittest

from PIL import Image, ImageDraw
import numpy as np

from prepare_portrait_families import components, display_candidate, fitted_preview, numeric_frame


class PortraitFamilyTests(unittest.TestCase):
    def test_table_prefixes_not_filename_conventions(self):
        for name, prefix in [('pc01-56', 'pc01-'), ('malea07', 'malea'), ('wets_01', 'wets_'),
                             ('lmin-03', 'lmin-')]:
            self.assertIsNotNone(numeric_frame(name, prefix))
        for name in ('pc01bod', 'pc01-lhd', 'pc010-01', 'npc0001'):
            self.assertIsNone(numeric_frame(name, 'pc01-'))

    def test_no_upscale_or_anisotropic_fitting(self):
        small = fitted_preview(Image.new('RGB', (60, 80), 'white'), (118, 158))
        self.assertEqual(np.all(np.asarray(small) == 255, axis=2).sum(), 60*80)
        wide = fitted_preview(Image.new('RGB', (240, 160), 'white'), (118, 158))
        self.assertEqual(wide.getpixel((59, 0)), (88, 46, 88))
        self.assertEqual(wide.getpixel((59, 79)), (255, 255, 255))

    def test_opaque_canvas_detection_rejects_missing_slots(self):
        raw = Image.new('RGB', (300, 220), '#ff00ff')
        draw = ImageDraw.Draw(raw)
        draw.rectangle((5, 5, 124, 164), fill='#304030')
        draw.rectangle((150, 5, 269, 164), fill='#304030')
        layout = {'columns': 2, 'cells': [{'id': 'a'}, {'id': 'b'}]}
        self.assertEqual(components(raw, layout), [[5, 5, 120, 160], [150, 5, 120, 160]])
        layout['cells'].append({'id': 'missing'})
        self.assertEqual(components(raw, layout), [])

    def test_dark_gutters_are_measured_not_uniformly_guessed(self):
        raw = Image.new('RGB', (256, 160), '#333333')
        draw = ImageDraw.Draw(raw)
        draw.rectangle((0,0,119,159),fill='#98aa98')
        draw.rectangle((126,0,255,159),fill='#98aa98')
        layout = {'columns': 2, 'cells': [{'id':'a'},{'id':'b'}]}
        self.assertEqual(components(raw,layout),[[0,0,120,160],[126,0,130,160]])

    def test_unexpected_alpha_is_visible_not_hidden(self):
        result = display_candidate(Image.new('RGBA',(2,2),(255,255,255,0)))
        self.assertEqual(result.getpixel((0,0)),(88,46,88))


if __name__ == '__main__':
    unittest.main()
