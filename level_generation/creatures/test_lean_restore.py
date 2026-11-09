"""Focused regression checks for shared restoration screening and contact-based acceptance."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image

from sheet_checks import plan, screen

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('freeze_review', HERE / 'mm6_remaining/redo_2x/freeze_review.py')
freezer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(freezer)
stage_spec = importlib.util.spec_from_file_location('stage_result', HERE / 'mm6_remaining/redo_2x/stage_result.py')
stager = importlib.util.module_from_spec(stage_spec)
stage_spec.loader.exec_module(stager)


class SheetChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='creature-screen-')
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'sheet.png'

    def test_maximum_fitting_poses_and_custom_envelope(self):
        self.assertEqual(plan(8, 232, 232)['poses'], 6)
        self.assertEqual(plan(12, 100, 100)['poses'], 12)
        self.assertEqual(plan(8, 232, 232, envelopes=[(4096, 4096)])['poses'], 8)
        with self.assertRaises(ValueError):
            plan(1, 2000, 2000)

    def test_alpha_and_delivered_budget_are_hard_gates(self):
        Image.new('RGB', (40, 40), 'gray').save(self.path)
        self.assertEqual(screen(self.path, (20, 20), (1, 1), 1)['status'], 'blocked')
        Image.new('RGBA', (40, 40)).save(self.path)
        self.assertIn('Empty artwork', screen(self.path, (20, 20), (1, 1), 1)['failures'])
        image = Image.new('RGBA', (40, 40))
        image.paste((80, 90, 100, 255), (5, 5, 35, 35))
        image.save(self.path)
        self.assertEqual(screen(self.path, (21, 20), (1, 1), 1)['status'], 'blocked')
        result = screen(self.path, (20, 20), (1, 1), 1, .5)
        self.assertEqual(result['status'], 'static_screen_passed_visual_review_required')
        self.assertTrue(result['warnings'])  # Flat fills warn; they are not automatically failed or accepted.
        self.assertEqual(screen(self.path, (20, 20), (1, 1), 1, .6)['status'], 'blocked')

    def test_repeated_upscale_warns_and_empty_cell_fails(self):
        rng = np.random.default_rng(7)
        image = np.zeros((10, 10, 4), dtype=np.uint8)
        image[1:9, 1:9, :3] = rng.integers(0, 256, (8, 8, 3), dtype=np.uint8)
        image[1:9, 1:9, 3] = 255
        Image.fromarray(image).resize((20, 20), Image.Resampling.NEAREST).save(self.path)
        result = screen(self.path, (10, 10), (1, 1), 1)
        self.assertGreater(result['foreground_neighbor_repeat_fraction'], .45)
        self.assertTrue(any('pixel blocks' in warning for warning in result['warnings']))
        image = Image.new('RGBA', (80, 40))
        image.paste(Image.open(self.path), (0, 0))
        image.save(self.path)
        self.assertIn('Empty occupied cell 2', screen(self.path, (20, 20), (2, 1), 2)['failures'])

    def test_failed_return_is_archived_without_replacing_selected_art(self):
        root = Path(self.temp.name)
        out = root / 'redo_2x'
        (out / 'raw').mkdir(parents=True)
        prompt = root / 'prompt.txt'
        prompt.write_text('Synthetic fixture')
        Image.new('RGB', (40, 40), 'gray').save(self.path)
        job = dict(id='standing', cell_native_size=[20, 20], columns=1, rows=1, frames=['pose'],
                   prompt=str(prompt), references=[], attempts=[], selected_raw='accepted-previous.png')
        freezer.write(out / 'run.json', {'jobs': [job]})
        with contextlib.redirect_stdout(io.StringIO()):
            stager.stage(str(root), 'standing', str(self.path))
            stager.stage(str(root), 'standing', str(self.path))
        job = freezer.read(out / 'run.json')['jobs'][0]
        self.assertEqual(job['selected_raw'], 'accepted-previous.png')
        self.assertEqual(len(job['attempts']), 1)
        self.assertEqual(job['attempts'][0]['status'], 'blocked_static_screen')


class ContactAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='creature-acceptance-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'family'
        self.out = self.root / 'redo_2x'
        (self.out / 'review').mkdir(parents=True)
        manifest = dict(frames={'pose': {}}, animations={}, animations_by_palette={}, logical_canvas=[40, 40],
                        logical_pivot=[20, 40], native_frame_scale=1,
                        generated_detail={'measured_minimum': 2.2})
        freezer.write(self.root / 'manifest.json', manifest)
        freezer.write(self.out / 'manifest.json', manifest)
        freezer.write(self.out / 'registration.json', {'pose': dict(effective_sampling_xy=[2.2, 2.2],
                      raw_clip=False, raw_path='raw.png')})
        validation = dict.fromkeys(('source_hashes_unchanged', 'generation_provenance_hashes_verified',
            'raw_cells_unclipped', 'exact_crop_reconstruction', 'exact_atlas_extraction', 'variant_alpha_unchanged',
            'zero_mask_unchanged', 'base_bypass_exact', 'per_palette_native_sequences_preserved'), True)
        validation['visual_review_complete'] = False
        freezer.write(self.out / 'validation.json', validation)
        freezer.write(self.out / 'run.json', dict(jobs=[]))
        Image.new('RGB', (40, 40), 'gray').save(self.out / 'review/contact.png')
        self.decision = dict(status='accepted_after_visual_review', review_mode='static_contacts',
            method='Synthetic fixture; no actual creature accepted', reviewed_frames=['pose'],
            reviewed_manifest_sha256=freezer.sha(self.out / 'manifest.json'),
            checks=dict.fromkeys(('faithful_detail', 'poses_and_placement', 'edges_and_alpha', 'masks_and_variants'), True),
            evidence_artifacts={'review/contact.png': freezer.sha(self.out / 'review/contact.png')})

    def freeze(self, viewer=False):
        freezer.write(self.out / 'review/decision.json', self.decision)
        with contextlib.redirect_stdout(io.StringIO()):
            freezer.freeze(self.root, with_viewer=viewer)

    def test_contact_review_needs_no_browser_notes_or_viewer(self):
        self.freeze()
        acceptance = freezer.read(self.out / 'review/acceptance.json')
        self.assertEqual(acceptance['status'], 'accepted')
        for name, digest in acceptance['artifact_hashes'].items():
            self.assertEqual(freezer.sha(self.out / name), digest)
        self.assertFalse((self.out / 'review.html').exists())

    def test_template_viewer_uses_local_export_only(self):
        templates = self.root.parent / 'mm6_peasants'
        templates.mkdir()
        (templates / 'viewer.html').write_text('__TITLE__\n/* MANIFEST */')
        freezer.write(self.out / 'config.json', {'title': 'Fixture'})
        self.freeze(viewer=True)
        self.assertIn('Fixture', (self.out / 'review.html').read_text())

    def test_missing_pose_review_rejected(self):
        self.decision['reviewed_frames'] = []
        with self.assertRaises(AssertionError):
            self.freeze()

    def test_changed_review_evidence_rejected(self):
        Image.new('RGB', (40, 40), 'red').save(self.out / 'review/contact.png')
        with self.assertRaises(AssertionError):
            self.freeze()

    def test_missing_numeric_check_rejected(self):
        validation = freezer.read(self.out / 'validation.json')
        del validation['exact_atlas_extraction']
        freezer.write(self.out / 'validation.json', validation)
        with self.assertRaises(AssertionError):
            self.freeze()


if __name__ == '__main__':
    unittest.main()
