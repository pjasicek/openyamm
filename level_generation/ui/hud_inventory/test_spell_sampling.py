"""Focused coverage for unequal native spell states drawn into one declared button rectangle."""
import importlib.util
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

path = Path(__file__).parent / 'pilots/air_spells/process_pair.py'
spec = importlib.util.spec_from_file_location('spell_pair_processing', path)
processing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(processing)


class SpellSamplingTests(unittest.TestCase):
    def test_unequal_states_keep_exact_canvases_and_share_declared_page_region(self):
        pixels = np.zeros((480, 640, 4), dtype='uint8')
        pixels[:, :, :3] = np.arange(640)[None, :, None] % 200
        pixels[:, :, 3] = 255
        page = Image.fromarray(pixels)
        rect = [468, 333, 126, 137]
        normal = processing.page_substrate(page, rect, (126, 137))
        highlighted = processing.page_substrate(page, rect, (125, 137))
        self.assertEqual(highlighted.size, (125, 137))
        self.assertEqual(normal.tobytes(), page.crop((468, 333, 594, 470)).tobytes())
        displayed = processing.resize_for_layout(highlighted, (126, 137))
        # The same page region is sampled; no newly invented padding or right-edge crop.
        self.assertLessEqual(np.abs(np.asarray(displayed).astype(int) - np.asarray(normal)).max(), 1)

    def test_quad_resampling_does_not_mix_hidden_black_into_foreground(self):
        source = Image.new('RGBA', (2, 1))
        source.putdata([(255, 80, 20, 255), (0, 0, 0, 0)])
        sampled = processing.resize_for_layout(source, (4, 1))
        for r, g, b, a in sampled.getdata():
            if a:
                self.assertGreaterEqual(r, 253)
                self.assertLessEqual(abs(g - 80), 3)
                self.assertLessEqual(abs(b - 20), 3)


if __name__ == '__main__':
    unittest.main()
