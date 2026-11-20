"""Adversarial fitting cases: canvas dimensions alone cannot prove drop-in registration."""
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

import registration
from finalize_classification import digest


class RegistrationTests(unittest.TestCase):
    def test_same_canvas_shrunken_shifted_and_filled_icons_fail(self):
        source = Image.new('RGBA', (100, 100))
        ImageDraw.Draw(source).rectangle((20, 10, 69, 89), fill='white')
        self.assertFalse(registration.compare(source, source)['failures'])
        for box in [(30, 30, 59, 69), (28, 10, 77, 89), (0, 0, 99, 99)]:
            with self.subTest(box=box):
                output = Image.new('RGBA', source.size)
                ImageDraw.Draw(output).rectangle(box, fill='white')
                self.assertTrue(registration.compare(source, output)['failures'])

    def test_same_bounds_missing_interior_component_fails(self):
        source = Image.new('RGBA', (100, 100))
        draw = ImageDraw.Draw(source)
        draw.rectangle((5, 5, 94, 94), outline='white')
        output = source.copy()
        draw.rectangle((30, 30, 69, 69), fill='white')
        self.assertTrue(registration.compare(source, output)['failures'])

    def test_soft_glow_extent_is_checked_below_opaque_threshold(self):
        source = Image.new('RGBA', (100, 100))
        draw = ImageDraw.Draw(source)
        draw.rectangle((10, 10, 89, 89), fill=(255, 255, 255, 40))
        draw.rectangle((40, 40, 59, 59), fill='white')
        output = Image.new('RGBA', source.size)
        ImageDraw.Draw(output).rectangle((40, 40, 59, 59), fill='white')
        result = registration.compare(source, output)
        self.assertTrue(result['failures'])
        self.assertEqual(result['thresholds'][1]['silhouette_iou'], 1)

    def test_opaque_canvas_requires_internal_landmarks_and_bound_evidence(self):
        with tempfile.TemporaryDirectory(prefix='hud-fitting-test-') as directory:
            directory = Path(directory)
            source, output = directory / 'native.png', directory / 'restored.png'
            Image.new('RGB', (30, 40), 'gray').save(source)
            Image.new('RGB', (60, 80), 'gray').save(output)
            member = dict(id='fixture', source_path=str(source), source_sha256=digest(source),
                          source_rect=[0, 0, 30, 40], export_region=[0, 0, 60, 80], method='imagegen_sheet')
            target = dict(compositing=dict(profiles=['hud']))
            evidence = registration.evidence(member, target, output, directory / 'review')
            path = Path(evidence['registration_record'])
            record = json.loads(path.read_text())
            record['visual_fit_notes'] = 'Synthetic test, not a real visual review.'
            path.write_text(json.dumps(record))
            with self.assertRaisesRegex(AssertionError, 'three named'):
                registration.validate(member, target, output, path)
            record['landmarks'] = [dict(name=str(i), source_xy=[i * 8, i * 12],
                                        restored_xy=[i * 16, i * 24]) for i in range(3)]
            path.write_text(json.dumps(record))
            registration.validate(member, target, output, path)
            record['landmarks'][1]['restored_xy'][0] += 5
            path.write_text(json.dumps(record))
            with self.assertRaisesRegex(AssertionError, 'landmark scale'):
                registration.validate(member, target, output, path)
            Image.new('RGB', (60, 80), 'black').save(output)
            with self.assertRaisesRegex(AssertionError, 'stale measured'):
                registration.validate(member, target, output, path)


if __name__ == '__main__':
    unittest.main()
