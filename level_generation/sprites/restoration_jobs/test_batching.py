"""Offline packing, return and provenance regressions. Synthetic fixtures, no generation calls."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

import batching
from batching import inspect_return, pack, validate_asset_reviews, validate_sheet
from readiness import registration_scale, require_resolution, resolution


def cells(count, size):
    return [dict(asset=f'a{i}', job=f'j{i}', native_size=list(size)) for i in range(count)]


def returned_sheet(sheet):
    # A predictable 3x native return with transparent gutters and tight source canvases.
    image = Image.new('RGBA', tuple(n * 3 // 2 for n in sheet['sheet_size']))
    draw = ImageDraw.Draw(image)
    for cell in sheet['cells']:
        box = [n * 3 // 2 for n in cell['native_rectangle']]
        draw.rectangle((box[0], box[1], box[2] - 1, box[3] - 1), fill=(70, 60, 50, 255))
    return image


class BatchingTests(unittest.TestCase):
    def test_soft_effect_prompt_preserves_opacity_and_phase_constraints(self):
        sheet = dict(profile='soft_fx', cells=[dict(job='effect', asset='phase')])
        prompt = batching.make_prompt(sheet, {'effect': dict(label='air burst')})
        self.assertIn('detached particles and quiet frames', prompt)
        self.assertIn('do not make smoke or dark energy falsely additive', prompt)
        self.assertIn('opaque haze', prompt)

    def test_identity_reference_hides_rejected_transparent_rgb(self):
        from identity_reference import write_identity_reference
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'raw.png'
            destination = Path(tmp) / 'seed.png'
            image = Image.new('RGBA', (3, 1))
            image.putdata([(130, 94, 45, 0), (20, 30, 40, 255), (200, 100, 0, 128)])
            image.save(source)
            original = source.read_bytes()
            write_identity_reference(source, destination, (255, 0, 255))
            with Image.open(destination) as seed:
                self.assertEqual(seed.size, (3, 1))
                self.assertEqual(seed.mode, 'RGB')
                self.assertEqual(seed.getpixel((0, 0)), (255, 0, 255))
                self.assertEqual(seed.getpixel((1, 0)), (20, 30, 40))
                self.assertEqual(seed.getpixel((2, 0)), (227, 50, 127))
            self.assertEqual(source.read_bytes(), original)

    def test_small_props_share_sheet_but_large_props_do_not(self):
        for count in (8, 12):
            sheet = pack(cells(count, (128, 128)))
            self.assertIsNotNone(sheet)
            validate_sheet(sheet)
            self.assertGreaterEqual(sheet['predicted_master_scale'], 2.2)
        self.assertIsNone(pack(cells(8, (256, 256))))
        self.assertIsNotNone(pack(cells(2, (256, 256))))
        self.assertIsNone(pack(cells(1, (800, 800))))
        self.assertIsNone(pack(cells(65, (16, 16))))

    def test_variable_sizes_preserve_full_canvas_and_do_not_overlap(self):
        targets = cells(1, (220, 310)) + [dict(asset='b', job='jb', native_size=[13, 97]),
                                        dict(asset='c', job='jc', native_size=[128, 43])]
        sheet = pack(targets)
        validate_sheet(sheet)
        for cell in sheet['cells']:
            r = cell['native_rectangle']
            self.assertEqual([r[2] - r[0], r[3] - r[1]], [2 * n for n in cell['native_size']])
        sheet['cells'][1]['cell'] = list(sheet['cells'][0]['cell'])
        with self.assertRaises(ValueError):
            validate_sheet(sheet)

    def test_small_actual_return_cannot_be_resized_into_compliance(self):
        sheet = pack(cells(2, (64, 64)))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'raw.png'
            image = returned_sheet(sheet)
            image.save(path)
            checks = inspect_return(sheet, path)
            self.assertEqual(checks['frames']['a0']['master_scale'], [3, 3])
            image.resize(tuple(n // 2 for n in sheet['sheet_size'])).save(path)
            with self.assertRaisesRegex(ValueError, 'below strict 2x'):
                inspect_return(sheet, path)

    def test_empty_cell_gutter_contamination_and_opaque_return_rejected(self):
        sheet = pack(cells(2, (32, 32)))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'raw.png'
            image = returned_sheet(sheet)
            first = sheet['cells'][0]
            box = [n * 3 // 2 for n in first['cell']]
            image.paste((0, 0, 0, 0), tuple(box))
            image.save(path)
            with self.assertRaisesRegex(ValueError, 'Empty/missing'):
                inspect_return(sheet, path)
            image = returned_sheet(sheet)
            image.putpixel((box[0], box[1]), (255, 0, 255, 255))
            image.save(path)
            with self.assertRaisesRegex(ValueError, 'gutter'):
                inspect_return(sheet, path)
            Image.new('RGBA', image.size, (255, 0, 255, 255)).save(path)
            with self.assertRaisesRegex(ValueError, 'transparent RGBA'):
                inspect_return(sheet, path)

    def test_legacy_inverse_ratio_is_not_confused_with_current_ratio(self):
        legacy = dict(source_pixels_per_output_pixel=[.25, .5], source_bounds=[0, 0, 10, 10],
                      target_bounds=[0, 0, 20, 20])
        self.assertEqual(registration_scale(legacy), [8, 4])
        current = dict(method='native_rectangle_inverse_v2', source_pixels_per_output_pixel=[.99, 1.1])
        self.assertEqual(registration_scale(current), [1.98, 2.2])
        self.assertIsNone(registration_scale(dict(source_pixels_per_output_pixel=[.25, .5])))

    def test_missing_resolution_stays_unknown_and_low_resolution_cannot_be_waived(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / 'attempt_01'
            directory.mkdir()
            job = dict(assets=['a'])
            state = dict(output_dir='attempt_01', attempts=[dict(raw='attempt_01/raw.png', raw_sha256='hash')])
            checks = dict(frames={'a': dict(registration=dict(method='native_rectangle_inverse_v2',
                                                             source_pixels_per_output_pixel=[.99, 1.2]))})
            (directory / 'checks.json').write_text(json.dumps(checks))
            with self.assertRaisesRegex(ValueError, 'BOTH axes'):
                require_resolution(job, state, root)
            (directory / 'checks.json').write_text(json.dumps(dict(frames={'a': dict(placement={})})))
            self.assertEqual(resolution(job, state, root), {})
            with self.assertRaises(ValueError):
                require_resolution(job, state, root)

    def test_each_batch_asset_needs_detail_layout_and_placement_review(self):
        note = 'Concrete inspected artwork evidence for this specific cell.'
        review = dict(assets={'a': dict(master_detail=note, layout=note, placement=note)})
        validate_asset_reviews(['a'], review)
        with self.assertRaises(ValueError):
            validate_asset_reviews(['a', 'b'], review)
        review['assets']['a']['master_detail'] = ''
        with self.assertRaises(ValueError):
            validate_asset_reviews(['a'], review)

    def test_extraction_preserves_rock_bottom_contact_and_empty_native_margins(self):
        import finish
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sheet = pack(cells(2, (20, 30)))
            raw = Image.new('RGBA', tuple(n * 3 // 2 for n in sheet['sheet_size']))
            native = Image.new('RGBA', (20, 30))
            ImageDraw.Draw(native).rectangle((5, 15, 14, 29), fill=(90, 80, 70, 255))
            sources = {}
            for cell in sheet['cells']:
                key = cell['asset']
                native.save(root / (key + '.png'))
                sources[key] = dict(native=key + '.png', native_size=[20, 30], native_bounds=[5, 15, 15, 30])
                raw.paste(native.resize((60, 90), Image.Resampling.NEAREST),
                          tuple(n * 3 // 2 for n in cell['native_rectangle'][:2]))
            raw.save(root / 'raw.png')
            first = sheet['cells'][0]
            job = dict(id=first['job'], assets=[first['asset']], cells=[first], sheet_size=sheet['sheet_size'],
                       profile='solid', group='rock', matte_rgb=[255, 0, 255], matte_collision_fraction=0,
                       alignment='bottom')
            with patch.object(finish, 'HERE', root), patch.object(finish, 'review'):
                report = finish.process(job, sources, root / 'raw.png', root / 'out')
            restored = Image.open(root / 'out' / (first['asset'] + '.png'))
            self.assertEqual(restored.size, (40, 60))
            opaque = restored.getchannel('A').point(lambda v: 255 if v >= 192 else 0)
            self.assertEqual(opaque.getbbox(), (10, 30, 30, 60))
            self.assertEqual(report['frames'][first['asset']]['registration']['source_pixels_per_output_pixel'],
                             [1.5, 1.5])

    def test_multi_job_intake_is_resumable_and_keeps_one_raw(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for folder in ('jobs', 'state', 'native', 'batch'):
                (root / folder).mkdir()
            sheet = pack(cells(2, (32, 32)))
            sheet.update(id='S001', jobs=['j0', 'j1'], reference='S001.png', prompt='S001.txt', seeds=[])
            snapshots, sources = {}, {}
            for cell in sheet['cells']:
                job_id, key = cell['job'], cell['asset']
                job = dict(id=job_id, status='ready', assets=[key])
                jp = root / 'jobs' / (job_id + '.json')
                jp.write_text(json.dumps(job))
                snapshots[job_id] = dict(job_sha256=batching.digest(jp),
                                         state_sha256=batching.fingerprint(dict(status='ready', attempts=[])))
                np = root / 'native' / (key + '.png')
                Image.new('RGBA', (32, 32), (80, 60, 30, 255)).save(np)
                cell['source_sha256'] = batching.digest(np)
                sources[key] = dict(native=str(np.relative_to(root)), native_size=[32, 32])
            (root / 'sources.json').write_text(json.dumps(sources))
            reference = root / 'batch/S001.png'
            returned_sheet(sheet).save(reference)
            prompt = root / 'batch/S001.txt'
            prompt.write_text(batching.QUALITY + '\nTest prompt, no generation calls.')
            sheet.update(reference_sha256=batching.digest(reference), prompt_sha256=batching.digest(prompt))
            manifest = root / 'batch/manifest.json'
            manifest.write_text(json.dumps(dict(observed_output_pixels=batching.PIXEL_BUDGET,
                                                 planned_scale=batching.PLANNED_SCALE, jobs=snapshots, sheets=[sheet])))
            with patch.object(batching, 'HERE', root):
                batching.preflight(manifest, 'S001')
                batching.claim_sheet(manifest, 'S001')
                with self.assertRaises(ValueError):
                    batching.claim_sheet(manifest, 'S001')
                batching.record_sheet(manifest, 'S001', reference)
                self.assertEqual(len(batching.import_sheet(manifest, 'S001')['imported']), 2)
                self.assertEqual(batching.import_sheet(manifest, 'S001')['imported'], [])
                states = [batching.read(root / 'state' / (job + '.json')) for job in ('j0', 'j1')]
                self.assertEqual(states[0]['attempts'][0]['raw'], states[1]['attempts'][0]['raw'])
                self.assertTrue(all(s['status'] == 'generated' for s in states))
                self.assertTrue(all('batch_claim' not in s for s in states))


if __name__ == '__main__':
    unittest.main()
