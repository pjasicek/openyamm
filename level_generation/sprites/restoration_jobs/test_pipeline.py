"""Focused offline invariants; no imagegen calls, source edits or engine launch."""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw

from build import resolve, matte_for
from finish import clean_soft, clean_solid, has_checkerboard_backdrop, register_cell, process
from placement import CHECKS_VERSION, apply_layout_override, inspect_placement, inspect_motion, validate_review
from weather import preserve_field


class RestorationTests(unittest.TestCase):
    def test_reviewed_mask_opens_rgba_holes_without_recoloring_dark_bars(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            raw = Image.new('RGBA', (32, 32), (23, 15, 8, 255))
            raw.putpixel((0, 0), (255, 0, 255, 0))
            raw.save(directory / 'raw.png')
            native = raw.resize((16, 16))
            native.save(directory / 'native.png')
            mask = Image.new('RGBA', (32, 32), (255, 255, 255, 255))
            # Invisible white RGB must not seal the opening; masks must apply to RGBA masters too.
            ImageDraw.Draw(mask).rectangle((12, 8, 19, 23), fill=(255, 255, 255, 0))
            mask.save(directory / 'mask.png')
            cell = dict(asset='frame', cell=[0, 0, 32, 32], native_rectangle=[0, 0, 32, 32],
                        native_size=[16, 16], native_bounds=[0, 0, 16, 16])
            job = dict(sheet_size=[32, 32], cells=[cell], profile='solid', group='fixture',
                       alignment='center', matte_rgb=[255, 0, 255], matte_collision_fraction=0)
            sources = {'frame': dict(native=str(directory / 'native.png'), native_bounds=[0, 0, 16, 16])}
            with patch('finish.review'):
                process(job, sources, directory / 'raw.png', directory / 'out',
                        mask_path=directory / 'mask.png')
            restored = Image.open(directory / 'out/frame.master.png')
            self.assertEqual(restored.getpixel((16, 16))[3], 0)
            self.assertEqual(restored.getpixel((5, 16)), (23, 15, 8, 255))
            self.assertEqual(restored.getpixel((0, 0))[3], 0)

    def test_user_excluded_art_is_accounted_without_being_accepted(self):
        from readiness import assess_job
        result = assess_job({'id': 'snow', 'assets': ['frame']},
                            {'status': 'accepted', 'user_excluded': {'reason': 'User will not use snow'}}, {})
        self.assertFalse(result['frame']['ready'])
        self.assertEqual(result['frame']['disposition'], 'user_excluded_keep_native')
        self.assertEqual(result['frame']['recorded_status'], 'accepted')
        self.assertEqual(result['frame']['reasons'], [])

    def test_opaque_weather_black_is_not_removed_as_background(self):
        native = Image.new('RGBA', (40, 30), (0, 0, 0, 255))
        native.putpixel((12, 9), (255, 255, 254, 255))
        native.putpixel((3, 3), (0, 0, 0, 0))
        raw = native.convert('RGB').resize((80, 60))
        output, _ = preserve_field(raw, native)
        self.assertEqual(output.getchannel('A').getextrema(), (255, 255))
        self.assertEqual(output.getpixel((0, 0)), (0, 0, 0, 255))
        self.assertTrue(np.array_equal(np.asarray(raw), np.asarray(output)[:, :, :3]))
        with self.assertRaises(ValueError):
            preserve_field(raw, Image.new('RGBA', (40, 30)))
        broken_return = raw.convert('RGBA')
        broken_return.putpixel((0, 0), (0, 0, 0, 0))
        with self.assertRaises(ValueError):
            preserve_field(broken_return, native)

    def test_soft_cleanup_preserves_purple_edges_on_cyan_and_yellow(self):
        for matte in ((0, 255, 255), (255, 255, 0)):
            with self.subTest(matte=matte):
                source = Image.new('RGB', (40, 40), matte)
                ImageDraw.Draw(source).rectangle((10, 10, 29, 29), fill=(100, 30, 110))
                restored, _ = clean_soft(source, matte)
                self.assertEqual(restored.getpixel((10, 20)), (100, 30, 110, 255))
                self.assertEqual(restored.getpixel((0, 0))[3], 0)

    def test_downsampling_filters_fine_detail(self):
        # Fine repeated material detail should average, not alias into bright/dark bands.
        pixels = np.zeros((300, 300, 4), dtype=np.uint8)
        pixels[:, :, :3] = ((np.arange(300) % 3 == 0) * 255)[None, :, None]
        pixels[:, :, 3] = 255
        cell = {'cell': [0, 0, 300, 300], 'native_rectangle': [0, 0, 300, 300],
                'native_size': [15, 15]}
        output, _ = register_cell(Image.fromarray(pixels), {'sheet_size': [300, 300]}, cell, (300, 300))
        interior = np.asarray(output)[3:-3, 3:-3]
        self.assertLessEqual(np.abs(interior[:, :, 0].astype(float) - 85).max(), 3)
        self.assertTrue((interior[:, :, 3] == 255).all())

    def test_runtime_view_resolution(self):
        frame = {'texture_name': 'shp', 'flags': ['Mirror5', 'Mirror6', 'Mirror7']}
        self.assertEqual([resolve(frame, n)[0] for n in range(8)],
                         ['shp0', 'shp1', 'shp2', 'shp3', 'shp4', 'shp3', 'shp2', 'shp1'])
        self.assertTrue(resolve(frame, 7)[1])
        self.assertEqual(resolve({'texture_name': 'already0', 'flags': []}, 4)[0], 'already0')
        self.assertEqual(resolve({'texture_name': 'bolt', 'flags': ['Images3']}, 5)[0], 'bolt4')
        self.assertEqual(resolve({'texture_name': 'static', 'flags': ['Image1']}, 7)[0], 'static')

    def test_common_transform_keeps_intended_frame_motion(self):
        # Same-size native canvases with a deliberately displaced silhouette in frame two.
        job = {'sheet_size': [200, 100]}
        images = []
        for index, x in enumerate((20, 28)):
            raw = Image.new('RGBA', (100, 100))
            ImageDraw.Draw(raw).rectangle((x, 40, x + 9, 69), fill=(110, 80, 40, 255))
            cell = {'cell': [index * 100, 0, (index + 1) * 100, 100],
                    'native_rectangle': [index * 100, 0, (index + 1) * 100, 100], 'native_size': [50, 50],
                    'native_bounds': [10, 20, 15, 35]}
            output, _ = register_cell(raw, job, cell, (200, 100))
            images.append(output)
        self.assertEqual(images[1].getbbox()[0] - images[0].getbbox()[0], 8)
        self.assertEqual(images[1].size, (100, 100))

    def test_padding_and_faint_speck_do_not_rescale_foreground(self):
        raw = Image.new('RGBA', (200, 200))
        ImageDraw.Draw(raw).rectangle((70, 60, 89, 119), fill=(100, 70, 40, 255))
        raw.putpixel((175, 175), (20, 20, 20, 30))
        cell = {'cell': [0, 0, 200, 200], 'native_rectangle': [50, 40, 150, 140],
                'native_size': [50, 50], 'native_bounds': [10, 10, 20, 40]}
        output, report = register_cell(raw, {'sheet_size': [200, 200]}, cell, (200, 200))
        self.assertEqual(output.getbbox(), (20, 20, 40, 80))
        self.assertEqual(report['source_pixels_per_output_pixel'], [1, 1])

    def test_faint_pixels_do_not_satisfy_opaque_base(self):
        native = Image.new('RGBA', (40, 60))
        ImageDraw.Draw(native).rectangle((15, 10, 24, 59), fill=(90, 70, 50, 255))
        enhanced = native.resize((80, 120), Image.Resampling.NEAREST)
        pixels = np.array(enhanced)
        pixels[100:, :, 3] = np.minimum(pixels[100:, :, 3], 30)
        _, warnings = inspect_placement(native, Image.fromarray(pixels),
                                        [{'name': 'base', 'box': [10, 45, 30, 60]}])
        self.assertIn('opaque_landmark_drift:base', warnings)
        self.assertIn('opaque_bounds_drift_review_supports_and_proportions', warnings)

    def test_support_comparison_preserves_native_bobbing(self):
        frames = {}
        for i, shift in enumerate((0, 5)):
            native = Image.new('RGBA', (40, 60))
            ImageDraw.Draw(native).rectangle((15, 10 + shift, 24, 49 + shift), fill=(90, 70, 50, 255))
            enhanced = native.resize((80, 120), Image.Resampling.NEAREST)
            placement, warnings = inspect_placement(native, enhanced,
                                                     [{'name': 'support', 'box': [10, 0, 30, 60]}])
            self.assertFalse(warnings)
            frames[str(i)] = {'placement': placement}
        self.assertFalse(inspect_motion(frames))
        frames['1']['placement']['regions']['support']['residual'][3] = 5
        self.assertIn('animation_support_drift:support', inspect_motion(frames))

    def test_acceptance_rejects_unreviewed_warning_and_old_checks(self):
        review = {k: 'Concrete visual evidence recorded here.' for k in
                  ('master_detail', 'light', 'dark', 'placement', 'supports', 'motion')}
        review.update(anchor_kind='suspended', warnings={})
        checks = {'checks_version': CHECKS_VERSION, 'warnings': ['opaque_landmark_drift:pole']}
        with self.assertRaises(ValueError):
            validate_review(checks, review, True)
        review['warnings']['opaque_landmark_drift:pole'] = 'Inspected native-relative pole region; explain residual here.'
        validate_review(checks, review, True)
        checks['checks_version'] = 1
        with self.assertRaises(ValueError):
            validate_review(checks, review, True)

    def test_native_alpha_preserves_magenta_material(self):
        rgba = Image.new('RGBA', (20, 20))
        ImageDraw.Draw(rgba).rectangle((5, 5, 15, 15), fill=(245, 15, 240, 127))
        for fn in (clean_solid, clean_soft):
            clean, report = fn(rgba, [255, 0, 255])
            self.assertEqual(clean.tobytes(), rgba.tobytes())
            self.assertEqual(report['method'], 'delivered_alpha')

    def test_soft_tail_beyond_old_seven_pixel_erosion_survives(self):
        rgb = Image.new('RGB', (70, 30), (255, 0, 255))
        draw = ImageDraw.Draw(rgb)
        draw.rectangle((30, 10, 40, 20), fill=(255, 255, 255))
        draw.rectangle((15, 10, 29, 20), fill=(255, 45, 255))
        result, _ = clean_soft(rgb, [255, 0, 255])
        self.assertGreater(result.getpixel((16, 15))[3], 30)
        self.assertEqual(result.getpixel((0, 0))[3], 0)

    def test_black_physical_core_stays_opaque(self):
        rgb = Image.new('RGB', (32, 32), (255, 0, 255))
        ImageDraw.Draw(rgb).rectangle((8, 8, 24, 24), fill=(0, 0, 0))
        for fn in (clean_soft, clean_solid):
            output, _ = fn(rgb, [255, 0, 255])
            self.assertEqual(output.getpixel((16, 16)), (0, 0, 0, 255))

    def test_yellow_matte_for_cyan_magenta_subject(self):
        rgba = Image.new('RGBA', (20, 10), (255, 0, 255, 255))
        ImageDraw.Draw(rgba).rectangle((10, 0, 19, 9), fill=(0, 255, 255, 255))
        matte, collision = matte_for([rgba])
        self.assertEqual(matte, [255, 255, 0])
        self.assertEqual(collision, 0)
        rgb = Image.new('RGB', (40, 30), tuple(matte))
        rgb.paste(rgba.convert('RGB'), (10, 10))
        output, _ = clean_solid(rgb, matte)
        self.assertEqual(output.getpixel((15, 15)), (255, 0, 255, 255))
        self.assertEqual(output.getpixel((25, 15)), (0, 255, 255, 255))
        self.assertEqual(output.getpixel((0, 0))[3], 0)

    def test_checkerboard_backdrop_is_rejected(self):
        image = Image.new('RGB', (32, 32), (192, 192, 192))
        pixels = image.load()
        for y in range(0, 32, 8):
            for x in range(0, 32, 8):
                if (x // 8 + y // 8) % 2:
                    ImageDraw.Draw(image).rectangle((x, y, x + 7, y + 7), fill=(224, 224, 224))
        self.assertTrue(has_checkerboard_backdrop(image))
        self.assertFalse(has_checkerboard_backdrop(Image.new('RGB', (32, 32), (255, 0, 255))))

    def test_gray_material_at_magenta_sheet_edge_is_not_checkerboard(self):
        image = Image.new('RGB', (100, 100), (255, 0, 255))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 30, 20, 50), fill=(60, 60, 60))
        draw.rectangle((0, 50, 20, 70), fill=(160, 160, 160))
        self.assertFalse(has_checkerboard_backdrop(image))

    def test_explicit_layout_selects_one_intact_copy_without_changing_native_canvas(self):
        cell = {'asset': 'a', 'cell': [0, 0, 40, 20], 'native_rectangle': [0, 0, 10, 10],
                'native_size': [10, 10]}
        job = {'assets': ['a'], 'cells': [cell], 'sheet_size': [40, 20]}
        layout = {'raw_sha256': 'recorded-master', 'reason': 'Select complete right copy; preserve source margins.',
                  'sheet_size': [40, 20], 'cells': {'a': {'cell': [20, 0, 40, 20],
                                                       'native_rectangle': [24, 4, 34, 14]}}}
        raw = Image.new('RGBA', (40, 20))
        draw = ImageDraw.Draw(raw)
        draw.rectangle((5, 5, 12, 12), fill=(80, 60, 40, 255))
        draw.rectangle((25, 5, 32, 12), fill=(80, 60, 40, 255))
        revised = apply_layout_override(job, layout, 'recorded-master')
        output, _ = register_cell(raw.crop((20, 0, 40, 20)), revised, revised['cells'][0], raw.size)
        self.assertEqual(output.size, (20, 20))
        self.assertEqual(job['cells'][0]['native_rectangle'], [0, 0, 10, 10])
        self.assertEqual(output.getpixel((0, 10))[3], 0)
        self.assertEqual(output.getpixel((10, 10))[3], 255)
        with self.assertRaises(ValueError):
            apply_layout_override(job, layout, 'wrong-master')


if __name__ == '__main__':
    unittest.main()
