import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image, ImageDraw

from audit_decoration_placement import scan_installed


class InstalledPlacementTests(unittest.TestCase):
    def test_installed_pixels_detect_anchor_canvas_and_manifest_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            originals = root / '_legacy/sprites_original'
            installed = root / 'engine/decorations_x2'
            originals.mkdir(parents=True)
            installed.mkdir(parents=True)
            native = Image.new('P', (20, 30))
            native.putpalette([0, 0, 0, 90, 70, 50] + [0] * (768 - 6))
            ImageDraw.Draw(native).rectangle((5, 10, 14, 24), fill=1)
            native.save(originals / 'PROP.bmp')  # Case-insensitive lookup; intentional native bottom margin.
            restored = native.convert('RGBA')
            restored.putalpha(native.point([0] + [255] * 255, 'L'))
            restored = restored.resize((40, 60), Image.Resampling.NEAREST)
            restored.save(installed / 'prop_p2.png')
            binding = dict(name='prop', palette_id=2, file='prop_p2.png', logical_size=[20, 30],
                           sha256=hashlib.sha256((installed / 'prop_p2.png').read_bytes()).hexdigest())
            (installed / 'manifest.json').write_text(json.dumps(dict(pixels_per_logical_pixel=2, bindings=[binding])))
            self.assertEqual(scan_installed(root)['frames'][0]['flags'], [])

            shifted = Image.new('RGBA', (40, 60))
            shifted.paste(restored, (0, -8))
            shifted.save(installed / 'prop_p2.png')
            frame = scan_installed(root)['frames'][0]
            self.assertIn('bottom_anchor_drift_review', frame['flags'])
            self.assertIn('installed_hash_differs_from_manifest', frame['flags'])
            self.assertEqual(frame['placement']['bottom_margin_delta'], 4)

            restored.crop((0, 0, 40, 58)).save(installed / 'prop_p2.png')
            self.assertIn('installed_canvas_differs_from_native', scan_installed(root)['frames'][0]['flags'])


if __name__ == '__main__':
    unittest.main()
