"""Scale checkpoint compatibility and validation; all writes use temporary storage."""

from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from checkpoints import Checkpoints, validate_colors


class ScaleCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.store = Checkpoints(self.root / 'frame_fixups.json')
        self.family = SimpleNamespace(id='test', artifact_sha256='art', manifest_sha256='manifest',
                                      label='Test', root=self.root,
                                      manifest={'pixels_per_logical_pixel': 2,
                                                'frames': {'a': {'crop_origin_px': [20, 40]}}})

    def save(self, **fields):
        frame = dict(offset_px=[2, 13], regenerate=True, note='Existing review')
        frame.update(fields)
        return self.store.save(self.family, dict(revision=self.store.get(self.family)['revision'], frames={'a': frame}))

    def test_legacy_offsets_and_notes_survive(self):
        frame = self.save()['frames']['a']
        self.assertEqual(frame['offset_px'], [2, 13])
        self.assertEqual(frame['note'], 'Existing review')
        self.assertEqual(frame['scale_factor'], 1)
        self.assertEqual(frame['scale_anchor'], 'bottom')

    def test_scale_only_record_persists_and_reset_removes_it(self):
        self.save(offset_px=[0, 0], regenerate=False, note='', scale_factor=1.0256477123)
        self.assertEqual(self.store.get(self.family)['frames']['a']['scale_factor'], 1.0256477123)
        self.assertEqual(self.save(offset_px=[0, 0], regenerate=False, note='', scale_factor=1)['frames'], {})

    def test_reset_scale_keeps_other_edits(self):
        self.save(scale_factor=1.03, scale_anchor='top')
        frame = self.save(scale_factor=1, scale_anchor='top')['frames']['a']
        self.assertEqual(frame['offset_px'], [2, 13])
        self.assertTrue(frame['regenerate'])
        self.assertEqual(frame['scale_anchor'], 'top')

    def test_invalid_scaling_does_not_write(self):
        for value in [0, -1, True, '1.02', 1.501, 0.499, float('nan'), float('inf')]:
            with self.assertRaisesRegex(ValueError, 'scale_factor'):
                self.save(scale_factor=value)
        with self.assertRaisesRegex(ValueError, 'scale_anchor'):
            self.save(scale_anchor='head')
        self.assertFalse(self.store.path.exists())

    def test_stale_revision_cannot_erase_scale(self):
        self.save(scale_factor=1.025)
        with self.assertRaises(RuntimeError):
            self.store.save(self.family, dict(revision=0, frames={}))
        self.assertEqual(self.store.get(self.family)['frames']['a']['scale_factor'], 1.025)

    def test_color_saves_with_placement_and_survives_old_client_save(self):
        self.family.manifest.update(variants={'684': {}}, regions={'mask_r': 'Purple skin'})
        first = self.save(scale_factor=1.03)
        colors = {'684': dict(region='mask_r', saturation=.8, brightness=1.1, enabled=True)}
        self.store.save(self.family, dict(revision=first['revision'], frames=first['frames'], colors=colors))
        self.assertEqual(self.store.get(self.family)['colors'], colors)
        self.assertEqual(self.store.get(self.family)['frames']['a']['scale_factor'], 1.03)
        self.save()
        self.assertEqual(self.store.get(self.family)['colors'], colors)

    def test_color_validation_rejects_unknown_regions_palettes_and_nonfinite_numbers(self):
        manifest = dict(variants={'684': {}}, regions={'mask_r': 'Skin'})
        valid = dict(region='mask_r', saturation=1, brightness=1, enabled=True)
        for change in [dict(region='mask_b'), dict(region=[]), dict(saturation=float('nan')),
                       dict(brightness=float('inf')), dict(brightness=-.1), dict(saturation=2.1),
                       dict(brightness=True), dict(enabled=1)]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_colors({'684': dict(valid, **change)}, manifest)
        with self.assertRaises(ValueError):
            validate_colors({'unknown': valid}, manifest)


if __name__ == '__main__':
    unittest.main()
