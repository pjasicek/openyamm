"""Landmark persistence, uncertainty and tracking gates using independent fixtures."""

from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import numpy as np

from checkpoints import Checkpoints
from landmarks import head_top, leg_gap, template_match, validate_landmarks
from PIL import Image, ImageDraw


class LandmarkTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.family = SimpleNamespace(id='test', artifact_sha256='art', manifest_sha256='manifest',
                                      label='Test', root=self.root, manifest={
                                          'pixels_per_logical_pixel': 2, 'frames': {'a': {'crop_origin_px': [1, 3]}}})
        self.store = Checkpoints(self.root / 'frame_fixups.json')

    def test_fractional_positions_hidden_eye_and_head_x_survive_old_client_save(self):
        points = {'a': {'original': {'eye1': [15.5, 7.25], 'eye2': None, 'head': [18.25, None]},
                        'restored': {'groin': [16, 43.5]}}}
        first = self.store.save(self.family, dict(revision=0, frames={}, landmarks=points))
        # An already open old tab does not send a landmarks field.
        self.store.save(self.family, dict(revision=first['revision'], frames={}))
        saved = self.store.get(self.family)
        self.assertEqual(saved['landmarks'], points)
        self.assertNotIn('eye2', saved['landmarks']['a']['restored'])

    def test_rejects_false_coordinates_unknown_landmarks_and_wrong_head_shape(self):
        for point in [[True, 3], [float('nan'), 3], [3, float('inf')], [3, None], [20000, 3]]:
            with self.assertRaises(ValueError):
                validate_landmarks({'a': {'original': {'eye1': point}}}, self.family.manifest)
        for record in [{'unknown': {}}, {'a': {'unknown': {}}}, {'a': {'original': {'tail': [1, 3]}}},
                       {'a': {'original': {'head': [1, 3]}}}]:
            with self.assertRaises(ValueError):
                validate_landmarks(record, self.family.manifest)

    def test_points_stay_bound_to_art_and_stale_edits_are_rejected(self):
        self.store.save(self.family, dict(revision=0, frames={}, landmarks={'a': {'original': {'eye1': [3, 4]}}}))
        with self.assertRaises(RuntimeError):
            self.store.save(self.family, dict(revision=0, frames={}, landmarks={}))
        self.family.artifact_sha256 = 'different-pixels'
        self.assertEqual(self.store.get(self.family), dict(revision=0, frames={}))

    def test_head_top_records_are_two_dimensional_and_preserve_other_points(self):
        points = {'a': {'original': {'head': [18.25, None], 'head_top': [18.5, 4.25]},
                        'restored': {'head_top': [19, 5.5]}}}
        self.store.save(self.family, dict(revision=0, frames={}, landmarks=points))
        self.assertEqual(self.store.get(self.family)['landmarks'], points)
        with self.assertRaises(ValueError):
            validate_landmarks({'a': {'original': {'head_top': [18.5, None]}}}, self.family.manifest)

    def test_head_top_ignores_higher_foreground_outside_the_head(self):
        art = Image.new('RGBA', (100, 120))
        draw = ImageDraw.Draw(art)
        draw.ellipse((38, 20, 62, 48), fill='white')
        draw.rectangle((35, 42, 65, 115), fill='white')
        draw.line((4, 5, 32, 56), fill='white', width=4)  # raised wing/weapon
        point = head_top(np.asarray(art), [50, 33])
        self.assertIsNotNone(point)
        self.assertAlmostEqual(point[0], 50)
        self.assertAlmostEqual(point[1], 20)

    def test_head_top_refuses_a_bun_or_projection_joined_by_a_narrow_stem(self):
        art = Image.new('RGBA', (100, 120))
        draw = ImageDraw.Draw(art)
        draw.ellipse((38, 24, 62, 49), fill='white')
        draw.rectangle((35, 44, 65, 115), fill='white')
        draw.ellipse((45, 4, 55, 12), fill='white')
        draw.rectangle((49, 10, 51, 26), fill='white')
        self.assertIsNone(head_top(np.asarray(art), [50, 33]))

    def test_tracks_unique_translated_texture_but_rejects_duplicate_candidates(self):
        source = np.zeros((100, 100, 4), dtype=np.float32)
        texture = np.random.default_rng(10).integers(25, 255, size=(21, 21, 3))
        source[30:51, 30:51, :3] = texture
        source[30:51, 30:51, 3] = 255
        target = np.zeros_like(source)
        target[35:56, 37:58] = source[30:51, 30:51]
        point, score = template_match(source, target, [40.5, 40.5])
        self.assertEqual(point, [47.5, 45.5])
        self.assertGreater(score, .99)
        target[15:36, 17:38] = source[30:51, 30:51]
        self.assertIsNone(template_match(source, target, [40.5, 40.5]))

    def test_leg_gap_requires_visible_split_not_an_opaque_robe(self):
        robe = np.zeros((110, 100, 4), dtype=np.float32)
        robe[10:101, 25:75, 3] = 255
        self.assertIsNone(leg_gap(robe))
        legs = robe.copy()
        for row in range(62, 101):
            half = max(1, (row-62)//5)
            legs[row, 50-half:51+half, 3] = 0
        gap = leg_gap(legs)
        self.assertIsNotNone(gap)
        self.assertAlmostEqual(gap[0], 50)
        self.assertAlmostEqual(gap[1], 61.5)

    def test_arm_body_gap_cannot_be_substituted_for_a_leg_junction(self):
        art = np.zeros((130, 120, 4), dtype=np.float32)
        art[10:70, 45:80, 3] = 255  # torso
        art[50:115, 48:65, 3] = 255  # one overlapping leg: no visible A
        art[38:85, 33:40, 3] = 255  # arm alongside the torso
        self.assertIsNone(leg_gap(art))


if __name__ == '__main__':
    unittest.main()
